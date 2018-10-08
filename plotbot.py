#Notable libraries used to complete this application include: Matplotlib, Pandas, Tweepy, and VADER.
import json
import tweepy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests as req
import csv
import datetime
import time
from config4 import consumer_key, consumer_secret, access_token, access_token_secret
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
#analyzer = SentimentIntensityAnalyzer()

# Setup Tweepy API Authentication
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())

# #Your bot should scan your account every five minutes for mentions.
def main():

    counter = 0

    while(counter < 1):
    #go find new tweets   
        new_tweet = check_for_new_tweet()

        #if new tweet: 1) who requesting 2) who target
        seeker = find_requestor_handle(new_tweet)
        pursued = find_target_acct(new_tweet, seeker)

        #has target been requested before (check csv)
        if check_for_abuse(pursued, seeker) == True:
            break
        #if not, run analysis, save png, tweet
        else:
            sentiment = pull_tweets(pursued)
        
        scatter_plot(pursued, sentiment, seeker) 
        
        time.sleep(300)

        counter += 1
            
def check_for_new_tweet():
    plot_tweets = []
    plot_tweets = api.search("pbot4444", count = 1)['statuses'][0]

    return plot_tweets

#find the Twitter User handle for the person requesting the analysis
def find_requestor_handle(tweets):
    requesting_user = ""
    new_tweet = tweets
    requesting_user = '@' + new_tweet['user']['screen_name']

    return requesting_user

#find the Twitter handle of the person or entity being analyzed 
def find_target_acct(tweets, requestor):
    #I know I should use the lower method but couldn't figure it out in time
    Analyze = "Analyze"
    analyze = 'analyze'

    bad_requester = requestor

    plot_tweets = tweets

    target_acct = ""

    if Analyze in plot_tweets['text']:
        target_acct = '@' + plot_tweets['entities']['user_mentions'][1]['screen_name']
    elif analyze in plot_tweets['text']:
        target_acct = '@' + plot_tweets['entities']['user_mentions'][1]['screen_name']
    else:
        api.update_status(f"Play by the rules, you must @{bad_requester}")

    return target_acct

#check to see if the target has already been analyzed
def check_for_abuse(target, requestor):
    abuse = False
    target_acct = target
    requesting = requestor

    with open('target_user.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            for field in row:
                if field == target_acct:
                    abuse = True
                    f.close()
                    break
                else:
                    abuse = False    
                
    if abuse == True:
        api.update_status(f"I'm sorry, @{requesting}, but you're going to have to be more original.")
        return abuse 
    else:
        with open('target_user.csv', 'a') as f:
            f.write(target_acct + '\n')
        f.close()
        return abuse

#Your bot should pull 500 most recent tweets to analyze for each incoming request.
def pull_tweets(target):

    analyzer = SentimentIntensityAnalyzer()
    target_acct = target
    oldest_tweet = None
    target_user_tweets = []
    sentiments = []
    counter = 1

    for x in range(5):
        public_tweets = api.user_timeline(target_acct, page=x, max_id = oldest_tweet)
        for tweet in public_tweets: 
            target_user_tweets.append(tweet['text'])
    
            # Run Vader Analysis on each tweet
            results = analyzer.polarity_scores(tweet["text"])
            compound = results["compound"]
            pos = results["pos"]
            neu = results["neu"]
            neg = results["neg"]

            # Get Tweet ID, subtract 1, and assign to oldest_tweet
            oldest_tweet = tweet['id'] - 1

            # Add sentiments for each tweet into a list
            sentiments.append({"Date": tweet["created_at"], 
                            "Compound": compound,
                            "Positive": pos,
                            "Negative": neu,
                            "Neutral": neg,
                            "Tweets Ago": counter})
            # Add to counter 
            counter += 1
    
    return sentiments
    
            
def scatter_plot(target, senti, requestor):
    target_acct = target
    requesting_user = requestor
    sentiments = senti
    sentiments_df = pd.DataFrame(sentiments)

    x_vals = sentiments_df["Tweets Ago"]
    y_vals = sentiments_df["Compound"]
    plt.plot(x_vals,y_vals, marker="o", linewidth=0.5, alpha=0.8)

    # Incorporate the other graph properties
    now = datetime.datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M")
    plt.title(f"Sentiment Analysis of Tweets ({now}) for {target_acct}")
    plt.xlim([x_vals.max(),x_vals.min()])
    plt.ylabel("Tweet Polarity")
    plt.xlabel("Tweets Ago")
    plt.savefig(f"images/Sentiment Analysis of Tweets for {target_acct}.png")
    
    plt.show()
    
    api.update_with_media(f'images/Sentiment Analysis of Tweets for {target_acct}.png', f'Tweet Analysis: {target_acct} at the request of {requesting_user}')

if __name__ == '__main__':
    main()