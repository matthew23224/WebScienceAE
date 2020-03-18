import tweepy
import pymongo
import twitter_credentials

from pymongo import MongoClient
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from heapq import nlargest
from operator import itemgetter


#Finds the most commonly used words in tweets, hashtags
# and users through KMeans clustering
def tweetClustering(tweets, numOfClusters):
    
    tweetTexts = []
    tweetHashtags = [] 

    #The start of each retweet's text is stripped of the RT indicator
    for tweet in tweets:
        raw = tweet['text']
        if raw.startswith('RT @'):
             raw = raw.split(":", 1)[1]

        #doesnt work yet
        index = raw.find("http")
        if (index != -1):
            end = raw.find(" ", index)
            link = raw[index:end]
            raw.replace(link,"")
        
        raw.replace("https","")
        tweetTexts.append(raw)

        for hashtag in tweet['hashtags']:
            tweetHashtags.append(hashtag["text"].encode("utf-8"))
       
    
    vectorizer = TfidfVectorizer(stop_words='english')
    
    text = vectorizer.fit_transform(tweetTexts)
    modelText = KMeans(n_clusters=numOfClusters, init='k-means++', max_iter=100, n_init=1)
    modelText.fit(text)
   
    centroids = modelText.cluster_centers_.argsort()[:, ::-1]
    termsText = vectorizer.get_feature_names()

    with open("textCluster.txt", "w") as file:

        for i in range(numOfClusters):
            print("Cluster %d\n" % (i))
            file.write("Cluster %d\n" % (i))
            for ind in centroids[i, :10]:
                print(termsText[ind])
                file.write(termsText[ind] + '\n')
            print("\n")
            file.write("\n")
    
    '''
    Attempted to cluster hashtags however when writing to file I encounter errors
    
    hashtags = vectorizer.fit_transform(tweetTexts)
    modelText = KMeans(n_clusters=numOfClusters, init='k-means++', max_iter=100, n_init=1)
    modelText.fit(hashtags)
   
    centroids = modelText.cluster_centers_.argsort()[:, ::-1]
    termsHashtags = vectorizer.get_feature_names()

    with open("hashtagCluster.txt", "w") as file:

        for i in range(numOfClusters):
            print("Cluster %d\n" % (i))
            file.write("Cluster %d\n" % (i))
            for ind in centroids[i, :10]:
                print(termsHashtags[ind])
                file.write(termsHashtags[ind] + '\n')
            print("\n")
            file.write("\n")'''

#Finds most important usernames by ranking what users get mentioned the most
def powerUsers(tweets):

    users = {}
    for tweet in tweets:
        if (len(tweet['mentions']) > 0):
            for mention in tweet['mentions']:
                if (mention != tweet['user']):
                    
                    if (mention in users):
                        users[mention] += 1
                    else:
                        users[mention] = 1
    
    print(users)


def tweetNetworks(tweets):

    #dictionaries represent user interaction
    #keys are specific users
    #values are lists of users that a user has interacted with
    normalMentions = {}
    retweetMentions = {}
    quoteMentions = {}
    hashtagsCoOccurence = {}

    for tweet in tweets:

        if (tweet['type'] == "normal"):
            if (len(tweet['mentions']) > 0):

                if (tweet['user'] not in normalMentions):
                    normalMentions[tweet['user']] = {}
                
                for mention in tweet['mentions']:
                    if (mention['screen_name'] != tweet['user']):
                        if mention['screen_name'] in normalMentions[tweet['user']]:
                            normalMentions[tweet['user']][mention['screen_name']] += 1
                        else:
                            normalMentions[tweet['user']][mention['screen_name']] = 1

        elif (tweet['type'] == "retweet"):
            if (tweet['user'] != tweet['originalUser']):
                
                if (tweet['user'] not in retweetMentions):
                    retweetMentions[tweet['user']] = {}
                
                if tweet['originalUser'] in retweetMentions[tweet['user']]:
                    retweetMentions[tweet['user']][tweet['originalUser']] += 1
                else:
                    retweetMentions[tweet['user']][tweet['originalUser']] = 1
        
        else:
            if (tweet['user'] != tweet['originalUser']):
                
                if (tweet['user'] not in quoteMentions):
                    quoteMentions[tweet['user']] = {}
                
                if tweet['originalUser'] in quoteMentions[tweet['user']]:
                    quoteMentions[tweet['user']][tweet['originalUser']] += 1
                else:
                    quoteMentions[tweet['user']][tweet['originalUser']] = 1

        if (len(tweet['hashtags']) > 0):
            for hashtag in tweet['hashtags']:
                pass



if __name__ == "__main__":

    client = MongoClient('127.0.0.1', 27017)

    # Gets the database instance
    db = client['tweets']

    tweets = []
    tweets.extend(db['raw'].find())
    

    numOfClusters = 10

    #retrieves most popular hashtags and words used in tweets
    #tweetClustering(tweets, numOfClusters)

    #finds most mentioned users
    powerUsers(tweets)

    #Find the networks for general data
    #tweetNetworks(tweets)

    #Find the networks for each cluster
    #for i in range(numOfClusters):
    #    tweetNetworks(cluster)
    


