#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CLI tool to check for the newest tweets of the users on
"""

import scraper \
    , logging \
    , re \
    , time \
    , notify2 \
    , html2text


from bs4 import BeautifulSoup
from markdown import markdown
from datetime import datetime

# For the argument parsing
import argparse \
    , sys


notif_name = "Tweet feeder"
notif_icon = "notification-message-IM"
notif_type = "im.received"
# Set to 'critical so it shows on top of every other window (even on full-screen,
# like while playing games)
notif_urgency = notify2.URGENCY_CRITICAL


def positive_int (value):
    """
    Checks that the given value is a positive integer

    Args:
        -> value: The value to check

    Returns:
        The value, as an integer

    Raises:
        -> argparse.ArgumentTypeError, if the argument wasn't a positive integer
    """
    ivalue = int (value)
    if ivalue <= 0:
         raise argparse.ArgumentTypeError (value + " is an invalid positive int value")
    return ivalue


def parse_args ():
    """
    Parses the arguments recieved from the command line
    """
    parser = argparse.ArgumentParser ()

    parser.add_argument ("users"
                        , type = argparse.FileType ("r")
                        , default = sys.stdin
                        , help = "File with the usernames from whose tweets will be "
                            "extracted, separated by new lines"
    )

    parser.add_argument ("-v", "--verbose"
                        , help = "Shows the actions being executed"
                        , action = "store_true"
    )

    parser.add_argument ("-c", "--max-count"
                        , help = "Maximum number of tweets to be extracted for each user"
                        , type = positive_int
    )

    parser.add_argument ("-e", "--max-epoch"
                        , help = "Maximum epoch (UNIX timestamp) of the older tweets "
                            "to retrieve"
                        , type = positive_int
    )

    parser.add_argument ("-w", "--watch"
                        , help = "Keep polling the endpoint for more tweets"
                        , action = "store_true"
    )

    parser.add_argument ("-n", "--notify"
                        , help = "Same as --watch; but also sends a notification on "
                                " every new tweet"
                        , action = "store_true"
    )

    return parser.parse_args ()



def sort_tweets (tweet_map):
    """
    Sorts the given map and creates a list, using arbitrary criteria

    Args:
        -> tweet_map: A dictionary with all the exracted tweets by user

    Returns:
        A list with the sorted tweets
    """
    # Sorts all the tweets by date (olders first, so the newest comes at the bottom)
    all_tweets = []

    for x in tweet_map.values ():
        all_tweets += x.values ()

    sorted_tweets = sorted ( all_tweets
                            , lambda a, b: cmp (a ["tweet_age"], b ["tweet_age"])
    )


    return sorted_tweets


def format_tweet (text, add_tabs = False, strip = False):
    """
    Removes all unwanted format from the given markdown and fixes some links (like
    mentions, where Twitter uses absolute paths to their root).

    Args:
        -> text: String with the markdown to be processed

        -> add_tabs (optional): If True, adds a tab before each line

        -> strip (optional): If True, removes all formatting (links, images...), leaving
                only the text

    Returns:
        A string with the processed markdown
    """
    # Substitutes the mentions:
    # [~~@~~**<username>**](/<username>)
    text = re.sub (r"\[~~@~~\*\*([^*]+)\*\*\]\(([^)]+)\)"
                    , r"[@\1](https://twitter.com\2)"
                    , text
        )

    # Hashtags:
    # [~~#~~**<tag>**](/<tag_link>)
    text = re.sub (r"\[~~#~~\*\*([^*]+)\*\*\]\(([^)]+)\)"
                    , r"[#\1](https://twitter.com\2)"
                    , text
        )

    if strip:
        # Converts it to HTML to put it back to text, but without links
        html = markdown (text)

        parsed = BeautifulSoup (html)

        # As twitter sometimes uses <a> tags to refer to pictures and links, some
        # processing has to be done
        # p -> parsed html
        # t -> tag to be replaced
        replace_anchor = lambda p, t: (

                t.replace_with (
                    p.new_string (" https://" + re.sub ("\n", "", t.text) + " ")
                )
            if re.search ("pic.twitter.com/.+", re.sub ("\n", "", t.text))
            else
                t.replace_with (
                    p.new_string (" " + re.sub ("\n", "", t.text) + " ")
                )
        )
        # Similar as before, some images are just emojis
        replace_img = lambda p, t: (

                t.replace_with (
                    p.new_string (" https://" + re.sub ("\n", "", t ["alt"]) + " ")
                )
            if re.search ("pic.twitter.com/.+", re.sub ("\n", "", t ["alt"]))
            else
                t.replace_with (
                    p.new_string (" " + re.sub ("\n", "", t ["alt"]) + " ")
                )
        )

        # Replaces the 'a' tags with their text (without "\n")
        [ replace_anchor (parsed, x)
            for x in parsed.select ("a")
        ]
        # Replaces the 'img' tags with their alt-text (without "\n")
        [ replace_img (parsed, x)
            for x in parsed.select ("img")
        ]

        text = html2text.html2text (parsed.get_text (), bodywidth = 140)


    # Removes final new lines
    text = re.sub ("\n+$", "", text)

    # Adds tabs before each line (if needed)
    if add_tabs:
        text = re.sub (r"^", r"\t", text)
        text = re.sub (r"\n", r"\n\t", text)


    return text


def print_tweets (tweet_map):
    """
    Dumps on STDOUT all the contents of the tweets, after ordering them using
    'order_tweets'

    Args:
        -> tweet_map: A dictionary with all the exracted tweets by user
    """
    base_url = "https://twitter.com"

    for tweet in sort_tweets (tweet_map):
        msg = u"{}\n".format ("=" * 100)
        # Header -> Direct link to the tweet
        msg += u"\n## [{0}]({1}{2}) \n".format (
                            tweet ["tweet_id"]
                            , base_url
                            , tweet ["permalink"]
                        )

        if tweet ["pinned"]:
            msg += u"Pinned tweet\n"

        # Retweet info (if any)
        if tweet ["retweet"]:
            msg += u"Retweet from {}\n".format (
                            tweet ["retweet_info"]["retweeter"]
                        )

        # Data of the user who tweeted
        msg += u"User: {0} [@{2}]({1}/{2})\n".format (
                            tweet ["user"]["displayname"]
                            , base_url
                           , tweet ["user"]["username"]
                        )
        # Date of the tweet
        msg += u"Date: {0}\n".format (
                            str (datetime.fromtimestamp (tweet ["tweet_age"]))
                    )

        msg += u"\n\t{0}\n{1}\n\t{0}\n".format (
                            "-" * 100
                            , format_tweet (tweet ["text"]
                                            , add_tabs = True
                                            , strip = True
                            )
                    )

        # Stats
        msg += u"\t{0} replies  - {1} retweets  - {2} likes\n".format (
                        tweet ["stats"]["replies"]
                        , tweet ["stats"]["retweets"]
                        , tweet ["stats"]["likes"]
                    )

        print msg


def get_tweets (users, max_count, max_epoch):
    """
    Gets the tweets of all the users and dumps them on STDOUT

    Args:
        -> users: A list with all the usernames to get tweets from

        -> max_count: Maximum number of tweets to be extracted for each user

        -> max_epoch: Maximum epoch (UNIX timestamp) of the older tweets to retrieve

    """
    data = scraper.get_tweets (users, max_count, max_epoch)

    print_tweets (data)



def poll (users, send_notif = False):
    """
    Waits for updates of any of the users on the list

    Args:
        -> users: A list with all the usernames to get tweets from

        -> send_notif (optional): If True, also sends a notification on every new tweet
    """
    # Waits 60 seconds between every update
    sleep_time = 60
    logger = logging.getLogger ("Polling")

    info = {}
    notif_err = False

    if send_notif:
        if not notify2.init (notif_name):
            logger.error ("Error accessing DBus")
            notif_err = True

    del_items = []
    # Stores the current html and max_position
    for u in users:
        logger.info ("Getting initial data from '" + u + "'")
        info [u] = scraper.get_update_info (u)

        # If there has been some error fetching content, no updates can be done
        if not info [u]:
            logger.error ("No tweet from '" + u + "' couldn't be obtained")
            # Marks the item to be removed
            del_items.append (u)

    # Deletes all the marked items
    users = [ x for x in users if x not in del_items ]

    if len (info) <= 0:
        logger.error ("No available info to get updates")
        return

    while True:
        try:
            time.sleep (sleep_time)
            logger.info ("Polling, looking for updates at " + str (datetime.now ()))

            for u in users:
                update = scraper.get_new_tweets (u
                                                , info [u]["max_pos"]
                                                , info [u]["html"]
                    )

                if update:
                    # Prints the new tweet. The data is wrapped in a dictionary with the
                    # username as the key, because that's how 'print_tweets' expects it
                    print_tweets ( {u: update} )
                    # Updates also the stored info
                    info [u] = scraper.get_update_info (u)

                    if send_notif and not notif_err:
                        title = "New tweet from @" + u
                        msg =  format_tweet (update.values ()[0] ["text"]
                                            , add_tabs = False
                                            , strip = True
                                )

                        notif = notify2.Notification (title, msg, notif_icon)
                        notif.set_category (notif_type)
                        notif.set_urgency (notif_urgency)

                        notif.show ()
                        # Deletes the notification to avoid conflicts with the next ones
                        del notif

            logger.info ("Poll done\n")

        except KeyboardInterrupt:
            logger.info ("Interrupt caught while polling. Cleaning data...")
            # Cleans everything
            notify2.uninit ()

            logger.info ("All done")
            break


if __name__ == "__main__":
    args = parse_args ()

    FORMAT = "%(levelname)s on %(name)s => %(message)s"

    if args.verbose:
        logging.basicConfig (level = logging.INFO, format = FORMAT)
    else:
        logging.basicConfig (level = logging.WARNING, format = FORMAT)

    logger = logging.getLogger ("Main")

    users = []
    with args.users as in_file:
        for line in in_file:
            line = line.rstrip ("\n")
            # Skips comments (everything after //) and empty lines
            line = re.sub ("[ \t]*//.*$", "", line)

            if line:
                users.append (line)

    logger.info ("Loaded {0} accounts from file '{1}'\n".format (
                    len (users)
                    , args.users.name
                )
    )

    max_count = args.max_count
    max_epoch = args.max_epoch

    try:

        get_tweets (users, max_count, max_epoch)

    except KeyboardInterrupt:
        logger.info ("Interrupt caught while getting tweets. Cleaning data...")
        logger.info ("All done")
        exit ()

    if args.notify:
        poll (users, send_notif = True)
    elif args.watch:
        poll (users, send_notif = False)
