import tweepy
import time
import pymongo
import json
import datetime
from pymongo import MongoClient

import twitter_credentials

'''
Listener class processes each tweet and stores it in the mongodb.
The tweets are streamed if they contain the keywords specified.
The tweet entry in to the database refers to the original user the tweet api 
query was referenced from, 
'''

class StdOutListener(tweepy.streaming.StreamListener):

    def on_status(self, data):

        try:

            #tracks the original user account the tweet is associated with.
            originalUser = data.user.screen_name
            
            if hasattr(data, "retweeted_status"):
                typeOfTweet = "retweet"
                originalUser = data.retweeted_status.user.screen_name
            elif hasattr(data, "quoted_status"):
                typeOfTweet = "quote"
                originalUser = data.quoted_status.user.screen_name
            else:
                typeOfTweet = "normal"
            
            #checks if the tweet exceeds 140 characters
            if (data.truncated):
                text = data.extended_tweet["full_text"]
            else:
                text = data.text

            #inserts tweet data into dictionary for insertion into the collection
            tweet = {'_id': data.id_str, 'user': data.user.screen_name, 'text': text, "created": data.created_at,
            "originalUser": originalUser, "type": typeOfTweet, "hashtags": data.entities['hashtags'],
            "mentions": data.entities['user_mentions']}

            #inserts original tweet into collection 
            collection.insert_one(tweet)
            
            print(tweet)

        except BaseException as e:
            print ("Error on data: %s" % str(e))

    def on_error(self, status):
        print(status)

if __name__ == "__main__":

    client = MongoClient('127.0.0.1', 27017)

    # Gets the database instance
    db = client['tweets']

    # Cleares collections in database for new stream data
    for collection in db.list_collection_names():
        print(db[collection].drop())

    # Creates the collection
    collection = db['raw']

    # Creates index to avoid insertion of duplicate tweets
    #db.raw.create_index([('id', pymongo.ASCENDING)], unique=True)
    
    # Sets the stream time to an hour
    #end = datetime.datetime.now() + datetime.timedelta(minutes=1)

    while (True):
        keywords = ["Trump", "Putin", "Xi Jinping", "corona", "covid-19"]

        listener = StdOutListener()

        auth = tweepy.OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)

        #api = tweepy.API(auth)

        stream = tweepy.Stream(auth, listener)
        
        # Filters stream of tweets over chosen keywords
        stream.filter(languages=["en"], track=keywords)
