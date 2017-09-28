#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Methods to get tweets and convert then into a parsable feed.
"""
import urllib2 \
    , re \
    , html2text \
    , logging \
    , json \
    , ssl

from tqdm import tqdm
from datetime import datetime
from bs4 import BeautifulSoup

"""
Main URL to get the first page of results
"""
build_twitter_url = lambda user: "https://twitter.com/" + user

"""
Builds the URL to get the rest of the tweets, knowing the max_position
"""
build_newpage_url = (
    lambda user
            , max_pos:
                "https://twitter.com/i/profiles/show/" + user + "/timeline/tweets?"
                + "include_available_features=1&include_entities=1"
                + "&max_position=" + str (max_pos) + "&reset_error_state=false"
)



"""
Builds the URL to get the new tweets, knowing the min_position
"""
build_update_url = (
    lambda user
            , min_pos:
                "https://twitter.com/i/profiles/show/" + user + "/timeline/tweets?"
                + "composed_count=0&include_available_features=1&"
                + "include_entities=1&include_new_items_bar=true&"
                + "interval=30000&latent_count=0&min_position=" + str (min_pos)
)


"""
Seconds befoire giving up on the URL request
"""
timeout = 20


def process_tweet (tag, older_age = None):
    """Gets the data from the given tag, containing the tweet

    Args:
        -> tag: The BeautifulSoup element with the div containing the tweet

        -> older_age (optional): Age of the oldest tweets to extract; in
                UNIX epoch format

    Returns:
        -> A dictionary with all the attributes,
        or
        -> None, if the tweet is older than 'older_age' (but not pinned)
    """
    data = {}

    # Checks if this tweet is pinned
    if len (tag.select (".context .pinned")) == 1:
        data ["pinned"] = True
    else:
        data ["pinned"] = False

    # Checks if this tweet is retweeted. If it is, stores also the account from which it
    # has been retweeted
    if len (tag.select (".context .js-retweet-text")) == 1:
        data ["retweet"] = True
        data ["retweet_info"] = {
            "retweeter": tag ["data-retweeter"]
            , "retweet_id": tag ["data-retweet-id"]
        }
    else:
        data ["retweet"] = False

    tag_epoch = int (tag.select (".tweet-timestamp span")[0]["data-time"])

    data ["tweet_age"] = tag_epoch
    # Filters by date, if necessary
    if older_age:
        threshold = datetime.fromtimestamp (older_age)
        age = datetime.fromtimestamp (tag_epoch)

        if age < threshold:
            # The pinned tweet may be older, but it's shown the first one
            if not data ["pinned"]:
                return None

    content = tag.select (".content")[0]

    # User data
    user = {
        "username": tag ["data-screen-name"]
        , "displayname": tag ["data-name"]
        , "uid": int (tag ["data-user-id"])
        , "avatar": content.find ("img", attrs = {"class": "avatar"})["src"]
    }
    data ["user"] = user

    # The text of the tweet
    text = unicode (content.select (".js-tweet-text-container")[0])
    data ["text"] = html2text.html2text (text)

    # Extra data (likes, retweets, permalink...)
    data ["permalink"] = tag ["data-permalink-path"]
    data ["conversation"] = int (tag ["data-conversation-id"])

    stat_str = "data-tweet-stat-count"
    # Stats in the following order: replies, retweets and favourites (likes)
    stat_list = [
            int (x.strip (stat_str + "=\""))
            for x in re.findall (stat_str + "=\"\d+\"", unicode (content))
    ]

    stats = {
        "replies":      stat_list [0]
        , "retweets":   stat_list [1]
        , "likes":      stat_list [2]
    }

    data ["stats"] = stats

    return data


def process_html (html, max_count = 10, older_age = None):
    """
    Process the HTML to get the tweets.

    Args:
        -> html: Text with the HTML to be processed

        -> max_count (optional): Maximum number of tweets to extract

        -> older_age (optional): Age of the oldest tweets to extract; in
                UNIX epoch format

    Returns:
        -> A dictionary with the follwing keys and values:
                - tweet_map: extracted tweets
                - n_items: Number of extracted tweets
                - min_position: ID of the older tweet
                - older_age_reached: Boolean to indicate if the 'older_age' threshold
                        has been reached
        or
        -> None, if the user hasn't been found
    """
    logger = logging.getLogger (__name__)
    tweet_map = {}
    older_age_reached = False

    parsed = BeautifulSoup (html, "html.parser")

    tweet_class = "data-tweet-id"
    tweet_ids = [ x.strip (tweet_class + "=\"")
                    for x in re.findall (tweet_class + "=\"\d+\"", html)
    ]

    # Gets the 'max_count' first items (including the pinned tweet, if any)
    tweet_ids = tweet_ids [:max_count]

    for i in tweet_ids:

        tweet = parsed.find ("div", attrs = {"data-tweet-id": i})
        data = process_tweet (tweet, older_age)

        if not data:
            older_age_reached = True
            break

        data ["tweet_id"] = i

        # If it's not a retweet, adds the full size avatar
        if not data ["retweet"]:
            data ["profile_pic"] = parsed.select (".ProfileAvatar-image")[0]["src"]

        tweet_map [i] = data
        logger.info ("Retrieved tweet with id " + i)


    # Gets the min position (the older tweet)
    older_tweet = int (parsed.select (".stream-container") [0]["data-min-position"])

    return {
        "tweet_map": tweet_map
        , "n_items": len (tweet_map)
        , "min_position": older_tweet
        , "older_age_reached": older_age_reached
    }



def get_next_page (username, max_position, full_html
                    , max_count = 10, older_age = None):
    """
    Gets the tweets of the specified user from the update URL (to get new tweets from
    the infinite scrolling), up to 'max' elements; or until the max old date is reached
    (whatever comes first)

    Args:
        -> username: Name of the user whose tweets will be extracted, performing a
            request to https://twitter.com/<username>

        -> max_position: Parameter to perform the request

        -> full_html: BeautifulSoup object with the main HTML, to extract some global
                data of the user, like the user's avatar

        -> max_count (optional): Maximum number of tweets to extract

        -> older_age (optional): Age of the oldest tweets to extract; in
                UNIX epoch format

    Returns:
        -> A dictionary with the extracted tweets,
        or
        -> None, if the user hasn't been found
    """
    tweet_map = {}

    logger = logging.getLogger (__name__)
    tweet_map = {}

    logger.info ("Getting more tweets, starting from " + str (max_position))
    try:
        response = urllib2.urlopen (
                        build_newpage_url (username, max_position)
                        , timeout = timeout
                    ).read ()

    except urllib2.HTTPError as e:
        logger.error ("No user found: '" + username + "' => " + str (e))
        return None

    except urllib2.URLError as e:
        logger.error ("Timeout expired getting tweets of '" + username + "' => "
                        + str (e)
        )
        return None

    except ssl.SSLError as e:
        logger.error ("Connection getting tweets of '" + username + "' => "
                        + str (e)
        )
        return None


    resp_map = json.JSONDecoder ().decode (response)

    html = BeautifulSoup (resp_map ["items_html"], "html.parser")

    # Deletes the old tweets on the page and adds the new ones
    container = full_html.select ("#stream-items-id")[0]
    container.clear ()
    container.append (html)

    html = str (full_html)

    # Gets the map with the tweets
    data = process_html (html, max_count, older_age)

    tweet_map = data ["tweet_map"]
    n_items = len (data ["tweet_map"])

    # Checks if the maximum amount of requested data has been extracted
    if n_items < max_count \
        and not data ["older_age_reached"]:
            tweet_map.update (
                get_next_page (username
                                , resp_map ["min_position"]
                                , full_html
                                , max_count - n_items
                                , older_age
                )
            )

    return tweet_map


def get_user_tweets (username, max_count = 10, older_age = None):
    """
    Gets the tweets of the specified user, up to 'max' elements; or until the max old
    date is reached (whatever comes first)

    Args:
        -> username: Name of the user whose tweets will be extracted, performing a
            request to https://twitter.com/<username>

        -> max_count (optional): Maximum number of tweets to extract

        -> older_age (optional): Age of the oldest tweets to extract; in
                UNIX epoch format

    Returns:
        -> A dictionary with the extracted tweets,
        or
        -> None, if the user hasn't been found
    """
    logger = logging.getLogger (__name__)
    tweet_map = {}

    try:
        # Doubles the timeout, as this information is crucial to get updates
        html = urllib2.urlopen (
                    build_twitter_url (username)
                    , timeout = (timeout * 2)
                ).read ()

    except urllib2.HTTPError as e:
        logger.error ("No user found: '" + username + "' => " + str (e))
        return None

    except urllib2.URLError as e:
        logger.error ("Timeout expired getting tweets of '" + username + "' => "
                        + str (e)
        )
        return None

    except ssl.SSLError as e:
        logger.error ("Connection getting tweets of '" + username + "' => "
                        + str (e)
        )
        return None

    data = process_html (html, max_count, older_age)
    tweet_map = data ["tweet_map"]
    n_items = len (data ["tweet_map"])

    # Checks if the maximum amount of requested data has been extracted
    if n_items < max_count \
        and not data ["older_age_reached"]:
            tweet_map.update (
                get_next_page (username
                                , data ["min_position"]
                                , BeautifulSoup (html, "html.parser")
                                , max_count - n_items
                                , older_age
                )
            )

    return tweet_map



def get_tweets (users, max_count = 10, older_age = None):
    """
    Gets the tweets of all the specified users, up to 'max' elements; or until the max
    old date is reached (whatever comes first)

    Args:
        -> users: A list with the name of the users whose tweets will be extracted,
            performing requests to https://twitter.com/<username>

        -> max_count (optional): Maximum number of tweets to extract

        -> older_age (optional): Age of the oldest tweets to extract; in
                UNIX epoch format

    Returns:
        A dictionary with the extracted tweets.
    """
    tweets = {}
    logger = logging.getLogger (__name__)

    for username in tqdm (users):

        logger.info ("Getting tweets of '" + username + "'")

        data = get_user_tweets (username, max_count, older_age)

        if data:
            tweets [username] = data
        else:
            logging.info ("No data retrieved from '" + username + "'")

    return tweets


def get_update_info (username):
    """
    Gets al the needed info to later use with 'get_new_tweets'

    Args:
        -> username: Name of the user whose tweets will be extracted, performing a
            request to https://twitter.com/<username>

    Returns:
        -> A dictionary with the following keys:
                - html: The parsed HTML, as a BeautifulSoup object
                - max_pos: The ID of the newer tweet
        or
        -> None, if the user hasn't been found
    """
    tweet_map = {}
    logger = logging.getLogger (__name__)

    try:
        response = urllib2.urlopen (
                        build_twitter_url (username)
                        , timeout = timeout
                    ).read ()

    except urllib2.HTTPError as e:
        logger.error ("No user found: '" + username + "' => " + str (e))
        return None

    except urllib2.URLError as e:
        logger.error ("Timeout expired getting tweets of '" + username + "' => "
                        + str (e)
        )
        return None

    except ssl.SSLError as e:
        logger.error ("Connection getting tweets of '" + username + "' => "
                        + str (e)
        )
        return None

    parsed = BeautifulSoup (response, "html.parser")
    max_position = parsed.select (".stream-container") [0]["data-max-position"]

    return {"html": parsed, "max_pos": max_position}



def get_new_tweets (username, min_position, full_html):
    """
    Queries the server for update info (new tweets)

    Args:
        -> username: Name of the user whose tweets will be extracted, performing a
            request to https://twitter.com/<username>

        -> min_position: Parameter to perform the request

        -> full_html: BeautifulSoup object with the main HTML, to extract some global
                data of the user, like the user's avatar

    Returns:
        -> A dictionary with the extracted tweets (it may be empy, if no new tweets were
        found),
        or
        -> None, if the user hasn't been found
    """
    tweet_map = {}
    logger = logging.getLogger (__name__)

    logger.info ("Updating tweets from " + username + ", starting from "
                + str (min_position)
    )

    try:
        response = urllib2.urlopen (
                        build_update_url (username, min_position)
                        , timeout = timeout
                ).read ()

    except urllib2.HTTPError as e:
        logger.error ("No user found: '" + username + "' => " + str (e))
        return None

    except urllib2.URLError as e:
        logger.error ("Timeout expired getting tweets of '" + username + "' => "
                        + str (e)
        )
        return None

    except ssl.SSLError as e:
        logger.error ("Connection getting tweets of '" + username + "' => "
                        + str (e)
        )
        return None

    resp_map = json.JSONDecoder ().decode (response)

    # If 'new_latent_count' is 0, no new tweets were recieved
    if resp_map ["new_latent_count"] == 0:
        # Returns an empty dictionary
        return tweet_map

    html = BeautifulSoup (resp_map ["items_html"], "html.parser")

    # Deletes the old tweets on the page and adds the new ones
    container = full_html.select ("#stream-items-id")[0]
    container.clear ()
    container.append (html)

    html = str (full_html)

    # Gets the map with the tweets
    data = process_html (html, max_count = resp_map ["new_latent_count"])

    tweet_map = data ["tweet_map"]

    return tweet_map
