import tweepy
import pymongo
import twitter_credentials
import operator
import json

from pymongo import MongoClient
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from heapq import nlargest
from operator import itemgetter

'''
Finds the most commonly used words in tweets, hashtags
and users through KMeans clustering
'''
def tweetClustering(tweets, numOfClusters):
    
    tweetTexts = []
    tweetHashtags = [] 

    #The start of each retweet's text is stripped of the RT indicator
    for tweet in tweets:
        raw = tweet['text']
        if raw.startswith('RT @'):
             raw = raw.split(":", 1)[1]

        #Prevents http from being term considered
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
    labels = modelText.fit_predict(text)

    clusterTweets =  [ [] for i in range(numOfClusters) ]

    #Calculates size of each cluster group (number of tweets used to make cluster)
    for i in range(len(tweets)):
        clusterTweets[labels[i]].append(tweets[i])
   
    centroids = modelText.cluster_centers_.argsort()[:, ::-1]
    termsText = vectorizer.get_feature_names()

    
    #Displays the most commonly used terms per cluster of tweets
    for i in range(numOfClusters):
        print("Cluster %d\n" % (i))
        for ind in centroids[i, :10]:

            print(termsText[ind])
        print("\n")
    
    return clusterTweets


'''
Finds most important usernames by ranking what users get mentioned the most
'''
def powerUsers(tweets):

    users = {}
    for tweet in tweets:
        if (len(tweet['mentions']) > 0):
            for mention in tweet['mentions']:
                if (mention['screen_name'] != tweet['user']):
                    
                    if (mention['screen_name'] in users):
                        users[mention['screen_name']] += 1
                    else:
                        users[mention['screen_name']] = 1
    
    powerfulUsers = list(sorted(users.items(), key=operator.itemgetter(1), reverse=True)[:10])
    return powerfulUsers


'''
This function calculates how much users are interacting with other users. It also monitors
what hashtags are used alongisde each other.
'''
def tweetNetworks(tweets):

    #dictionaries represent user interaction
    #keys are specific users
    #values are lists of users that a user has interacted with
    normalMentions = {}
    retweetMentions = {}
    quoteMentions = {}

    #dictionary represents each hashtag used any the values are any other hashtags used alongside it
    hashtagsOccurences = {}

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
                first = hashtag['text']
                if first in hashtagsOccurences:
                    for hashtag2 in tweet['hashtags']:
                        if hashtag2['text'] != first and hashtag2['text'] not in hashtagsOccurences[first]:
                            hashtagsOccurences[first].append(hashtag2['text'])
                else:
                    hashtagsOccurences[first] = []
                    for hashtag2 in tweet['hashtags']:
                        if hashtag2['text'] != first:
                            hashtagsOccurences[first].append(hashtag2['text'])
        
    return normalMentions, retweetMentions, quoteMentions, hashtagsOccurences

'''
Calculates the ties and triads across the three user interaction networks
'''             
def ties_triads(normalMentions, retweetMentions, quoteMentions):
    ties = []
    triads = []
    
    networks = [normalMentions, retweetMentions, quoteMentions]
    
    for network in networks:
        for user1 in network:
            for user2 in network[user1]:
                
                potentialTie = {user1,user2}
                if potentialTie not in ties:
                    ties.append(potentialTie)

                if user2 in network:
                    for user3 in network[user2]:
                        
                        potentialTriad = {user1,user2,user3}

                        #Checks that the first node is not the same as the third node
                        if (user1 != user3):
                            triads.append(potentialTriad)       

    return ties, triads

if __name__ == "__main__":

    client = MongoClient('127.0.0.1', 27017)

    # Gets the database instance
    #db = client['tweets']

    #tweets = []
    #tweets.extend(db['raw'].find())

    tweets = []
    with open('tweetData.json', 'r') as file:
        for line in file:
            tweets.append(json.loads(line))
    
    #Sets k to 10
    numOfClusters = 10

    #finds most mentioned users
    print("The ten most mentioned users are " + str(powerUsers(tweets)))

    #retrieves most popular hashtags and words used in tweets
    clusterTweets = tweetClustering(tweets, numOfClusters)

    

    #Find the networks for general data
    gen_normalMentions, gen_retweetMentions, gen_quoteMentions, gen_hashtagsOccurences = tweetNetworks(tweets)

    print("Normal mentions for general data has a size of " + str(len(gen_normalMentions.keys())))
    print("Retweet mentions for general data has a size of " + str(len(gen_retweetMentions.keys())))
    print("Quote mentions for general data has a size of " + str(len(gen_quoteMentions.keys())))
    print("Hashtag co-ocurrences for general data has a size of " + str(len(gen_hashtagsOccurences.keys())))

    clusterNetworks = [ [] for i in range(numOfClusters) ]

    #Find the networks for each cluster
    for i in range(numOfClusters):
        print('\n')
        clus_normalMentions, clus_retweetMentions, clus_quoteMentions, clus_hashtagsOccurences =  tweetNetworks(clusterTweets[i])
        print("Normal mentions for cluster %d has a size of %s" %  (i, len(clus_normalMentions.keys())))
        print("Retweet mentions for cluster %d has a size of %s" % (i, len(clus_retweetMentions.keys())))
        print("Quote mentions for cluster %d has a size of %s" %  (i, len(clus_quoteMentions.keys())))
        print("Hashtag co-ocurrences for cluster %d has a size of %s" %  (i, len(clus_hashtagsOccurences.keys())))
        clusterNetworks[i] = [clus_normalMentions, clus_retweetMentions, clus_quoteMentions]

    
    #Find the ties and triads for general data
    gen_ties, gen_triads= ties_triads(gen_normalMentions, gen_retweetMentions, gen_quoteMentions)
    #print(gen_ties)
    #print(gen_triads)
    print("\nNumber of ties for general data is " + str(len(gen_ties)))
    print("Number of triads for general data is " + str(len(gen_triads)))

    for i in range(numOfClusters):
        print('\n')
        clus_ties, clus_triads = ties_triads(clusterNetworks[i][0],clusterNetworks[i][1],clusterNetworks[i][2])
        print("Number of ties for cluster %d is %s" %  (i, len(clus_ties)))
        print("Number of triads for cluster %d is %s" % (i, len(clus_triads)))

    


