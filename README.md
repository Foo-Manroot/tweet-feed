# Tweet feed

This is a little Python script that helps me to stay updated on the latest new using
Twitter.

I'm sure this project isn't very useful, as most people will prefer to create an account
and use the official twitter tools, even when they only want to lurk around, without
tweeting nor interacting in any way.

Anyway, I'm personally using this tool to stay updated on the latest security-related
events, and most probably I'll keep improving this tool.

## Scraper

I think that the most interesting thing on this project is the scraper, as it has to get
data from an infinite scrolling page (that kind of page that loads more content when
you're at the bottom).

An explanation of this project can be found on
[this post my webpage](https://foo-manroot.github.io/post/scraping/twitter/2017/09/05/scraping-twitter.html).

Of course, if the scraper is useful to you, you are free to use and modifiy it (under the
terms stated on the license, if there's one).

For example, to get the first tweet from a user, you can use the function `get_tweets`,
that recieves a list with the users (read the docstring for more info), as follows:
```python
>>> import scraper
>>> s = scraper.Scraper ()
>>> data = s.get_tweets (["mzbat"], max_count = 2)
>>> data
>>> data
{'mzbat': {'902887483704320004': {'permalink': u'/Rainmaker1973/status/902887483704320004', 'stats': {'likes': 6407, 'retweets': 3659, 'replies': 64}, 'conversation': 902887483704320004, 'text': u'A really cool visual explanation of how potential &amp; kinetic energy are\nexchanged on a trampoline [http://buff.ly/2qhkllZ\xa0](https://t.co/a4NepKyZnj\n"http://buff.ly/2qhkllZ"\n)[pic.twitter.com/gAR1WWBHiu](https://t.co/gAR1WWBHiu)\n\n', 'tweet_age': 1504100125, 'pinned': False, 'retweet_info': {'retweet_id': u'904701461153681408', 'retweeter': u'mzbat'}, 'user': {'username': u'Rainmaker1973', 'displayname': u'Massimo', 'uid': 177101260, 'avatar': u'https://pbs.twimg.com/profile_images/686298118904786944/H4aoP8vA_bigger.jpg'}, 'tweet_id': '902887483704320004', 'retweet': True}, '720999941225738240': {'profile_pic': u'https://pbs.twimg.com/profile_images/683177128943337472/4CSt778e_400x400.jpg', 'permalink': u'/mzbat/status/720999941225738240', 'stats': {'likes': 3068, 'retweets': 854, 'replies': 67}, 'tweet_id': '720999941225738240', 'text': u'A dude told me I hacked like a girl. I told him if he popped shells a little\nfaster, he could too.[pic.twitter.com/PgiyYw41oo](https://t.co/PgiyYw41oo)\n\n', 'tweet_age': 1460734756, 'pinned': True, 'conversation': 720999941225738240, 'user': {'username': u'mzbat', 'displayname': u'b\u0360\u035d\u0344\u0350\u0310\u035d\u030a\u0341a\u030f\u0344\u0343\u0305\u0302\u0313\u030f\u0304t\u0352', 'uid': 253608265, 'avatar': u'https://pbs.twimg.com/profile_images/683177128943337472/4CSt778e_bigger.jpg'}, 'retweet': False}}}

>>> print json.dumps (data, indent=4)
{
    "mzbat": {
        "902887483704320004": {
            "permalink": "/Rainmaker1973/status/902887483704320004",
            "stats": {
                "likes": 6407,
                "retweets": 3659,
                "replies": 64
            },
            "conversation": 902887483704320004,
            "text": "A really cool visual explanation of how potential &amp; kinetic energy are\nexchanged on a trampoline [http://buff.ly/2qhkllZ\u00a0](https://t.co/a4NepKyZnj\n\"http://buff.ly/2qhkllZ\"\n)[pic.twitter.com/gAR1WWBHiu](https://t.co/gAR1WWBHiu)\n\n",
            "tweet_age": 1504100125,
            "pinned": false,
            "retweet_info": {
                "retweet_id": "904701461153681408",
                "retweeter": "mzbat"
            },
            "user": {
                "username": "Rainmaker1973",
                "displayname": "Massimo",
                "uid": 177101260,
                "avatar": "https://pbs.twimg.com/profile_images/686298118904786944/H4aoP8vA_bigger.jpg"
            },
            "tweet_id": "902887483704320004",
            "retweet": true
        },
        "720999941225738240": {
            "profile_pic": "https://pbs.twimg.com/profile_images/683177128943337472/4CSt778e_400x400.jpg",
            "permalink": "/mzbat/status/720999941225738240",
            "stats": {
                "likes": 3068,
                "retweets": 854,
                "replies": 67
            },
            "tweet_id": "720999941225738240",
            "text": "A dude told me I hacked like a girl. I told him if he popped shells a little\nfaster, he could too.[pic.twitter.com/PgiyYw41oo](https://t.co/PgiyYw41oo)\n\n",
            "tweet_age": 1460734756,
            "pinned": true,
            "conversation": 720999941225738240,
            "user": {
                "username": "mzbat",
                "displayname": "b\u0360\u035d\u0344\u0350\u0310\u035d\u030a\u0341a\u030f\u0344\u0343\u0305\u0302\u0313\u030f\u0304t\u0352",
                "uid": 253608265,
                "avatar": "https://pbs.twimg.com/profile_images/683177128943337472/4CSt778e_bigger.jpg"
            },
            "retweet": false
        }
    }
}
```

In that example, two tweets are retrieved and pretty-printed using `json.dumps`.

The retrieved data is a dictionary with the following format:
```python
{
    "<user handle>": {
        "id": "<user ID>"
        , "rest_id": "<user ID to perform API requests>"
        , "created_at": "<date when the user created its account>"
        , "description": "<user's bio>"
        , "fast_followers_count": <NUM>
        , "favourites_count": <NUM>
        , "followers_count": <NUM>
        , "friends_count": <NUM>
        , "has_custom_timelines": <BOOL>
        , "is_translator": <BOOL>
        , "listed_count": <NUM>
        , "location": "<location string>",
        , "media_count": <NUM>
        , "name": "<name that the user has set (not its handle, which is unique)>",
        , "normal_followers_count": <NUM>
        , "pinned_tweet_ids_str": [
              "<tweet-id>"
        ],
        , "profile_image_url": "<url of the profile image>"
        , "protected": "<BOOL>"
        , "screen_name": "<user handle>"
        , "statuses_count": <NUM>,
        , "translator_type": "<STRING>"
        , "url": "<homepage set by the user>",
        , "verified": <BOOL>
        # Tweet list, ordered from newer (position 0) to older (position n)
        , "tweets": [
            {
                "tweet_id": "<tweet-id>"
                , "profile_pic": "<avatar URL of the tweet owner>"
                , "permalink": "<link to the tweet>"
                , "stats": {
                      "likes": <number of likes>
                    , "retweets": <number of retweets>
                    , "replies": <number of replies>
                }
                , "text": "<plain text of the tweet>"
                , "tweet_age": <(NUM) timestamp of the tweet, in UNIX epoch format>
                , "pinned": <BOOL>
                , "conversation": <conversation-id>
                , "user": {
                    # Information of the owner of the tweet (important if it's a retweet)
                      "username": <account name (twitter.com/username)>
                    , "displayname": <nickname for the user>
                    , "uid": <user id>
                    , "avatar": <profile pic>
                }
                , "retweet": <indication to know if it's a retweet>
                # Only if "retweet" is True
                , "retweet_info" {
                      "retweet_id": <id of the retweet>
                    , "retweeter": <username who retweeted (the one whose data is being extracted)>
                }
            }
        # ... (more tweeets from the user)
        ]
        , "cursor": {
            "top": "<ID of the most recent tweet recovered>"
            , "bottom": "<ID of the oldest tweet recovered>"
        }
    }
    # ... (more users and their tweets)
}
```


## Configuration file

The syntax is pretty simple, with the following rules:
  - One user per line
  - Empty lines allowed (they're simply ignored)
  - Comments start with `//`


An example list of users to follow can be found on `./cli/example.cfg`
