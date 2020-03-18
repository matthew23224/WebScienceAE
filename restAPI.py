import tweepy
import time
import pymongo
from pymongo import MongoClient

import twitter_credentials

'''
Using Rest API to stream tweets from specific users.
'''

def captureTimeline(username):

    for status in tweepy.Cursor(api.user_timeline, screen_name=username, lang='en', include_rts=True, count=200).items(1000):
        
        #retrieves tweet data
        tweet = status._json
        
        #tracks the original user account the tweet is associated with
        originalUser = tweet["user"]["screen_name"]

         
        if hasattr(tweet, "retweeted_status"):
            typeOfTweet = "retweet"
            originalUser = tweet["retweeted_status"]["user"]["screen_name"]
        elif hasattr(tweet, "quoted_status"):
            typeOfTweet = "quote"
            originalUser = tweet["quoted_status"]["user"]["screen_name"]
        else:
            typeOfTweet = "normal"
            
        #checks if the tweet exceeds 140 characters
        #fix to incldude truncated tweets
        '''if (tweet['truncated']):
            text = tweet["extended_tweet"]["full_text"]
        else:
            text = tweet["text"]'''

        #inserts tweet data into dictionary for insertion into the collection
        tweet = {'_id': tweet['id_str'], 'user': tweet["user"]["screen_name"], 'text': tweet["text"], "created": tweet["created_at"],
        "originalUser": originalUser, "type": typeOfTweet,
        "hashtags": tweet["entities"]['hashtags'], "mentions": tweet['entities']['user_mentions']}

        #inserts original tweet into collection 
        collection.insert_one(tweet)
        print(tweet)

if __name__ == "__main__":

    auth = tweepy.OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
    auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)

    api = tweepy.API(auth)

    client = MongoClient('127.0.0.1', 27017)

    # Gets the database instance
    db = client['tweets']

    # Creates reference to the collection of tweets streamed from crawler
    collection = db['raw']

    powerUsers = ['POTUS','realDonaldTrump','SkyNews','BBCNews','BorisJohnson',
                  'NBCNews', 'FoxNewsSunday','LilNasX','Snowden','BarackObama',
                  'justinbieber','katyperry','Cristiano','Youtube','cnnbrk',
                  'ChinaDaily', 'PDChina', 'XHNews', 'TheEllenShow', 'JeremyClarkson']

    for user in powerUsers:
        captureTimeline(user)