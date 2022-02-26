from venv import create
import pandas as pd
import requests
import re
from statistics import mode

import tweets


#tans: BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAAIKlZgEAAAAA%2FPzTUcIMxE%2F1YSRh2b60shhO6C4%3DJFNP2ksUXD7qgTGxmhmkG6DHiCL4FvwNHR9gfLujioOff430au' 
BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAAHCXZgEAAAAAsFWHTYPNRHdi7ogP8CUBN%2FoM9QQ%3D1Id3Z7UFSoiCrknB7zA2BucLTzdpwgG3hdMY4cz5a5IvrzRYoL'
DATA_FILE = 'notes-00000.tsv'
ENDPOINT = 'https://api.twitter.com/2/tweets'


def read_data(filename):
    data = pd.read_csv(filename, sep='\t')
    return data


def create_headers(bearer_token):
    headers = {"Authorization": f"Bearer {bearer_token}"}
    return headers


def query(ids):

    def format_ids(ids):
        """Takes input of nparray of IDs and outputs comma separated strings"""
        return ','.join(str(id) for id in ids)

    params = {
        'ids': format_ids(ids),
        'tweet.fields': 'entities'
    }
    return params


def get_label_by_id(data, id):
    return ''.join(mode(data[data.tweetId == int(id)].classification))


# Returns True if keyword tweet contains keywords and is not duplicate 
def is_relevant(tweet, keywords, current_data):
    return tweet['id'] not in current_data['metadata'] and any(f' {word} ' in tweet['text'].lower() for word in keywords)



# Takes Birdwatch data and relevant keywords
# Returns dataframe containing relevant training data in format text,label,metadata
# Metadata is tweet ID
def process_data(data, keywords):
    
    fetched_data = {'text':[], 
                    'label':[], 
                    'metadata':[]}   

    def chunk(lst, n):
        """Yield successive n-sized chunks"""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    # Send one request per 100 tweets using their IDs
    ids = data.tweetId.values
    id_list = chunk(ids, 100)
    count=0
    for id_chunk in id_list:
        for tweet in (tweet for tweet in tweets.fetch_tweets(create_headers(BEARER_TOKEN), params=query(id_chunk)) if is_relevant(tweet, keywords, fetched_data)):
                # If not a duplicate tweet, clean it up and include it in our dataset
                fetched_data['text'].append(tweets.get_clean_text(tweet))
                fetched_data['label'].append(get_label_by_id(data, tweet['id']))
                fetched_data['metadata'].append(tweet['id'])

    #del fetched_data['metadata'] # TODO: remove metadata?
    return pd.DataFrame(fetched_data)




if __name__ == '__main__':
    with open("keywords.txt") as file:
        keywords = file.read().lower()
        keywords = keywords.split('\n')

    data = process_data(read_data(DATA_FILE), keywords)
    data.to_csv("training_data.csv", encoding='utf-8', index=False)
