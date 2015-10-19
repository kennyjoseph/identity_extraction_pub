__author__ = 'kjoseph'

from utility_code.util import *
from twitter_dm import dependency_parse_tweets
import codecs


tweet_id_to_tweet = get_original_tweet_data()

all_tweets = [v.tweet for v in tweet_id_to_tweet.values()]

parse_data = dependency_parse_tweets(TWEEBOPARSER_LOCATION,
                                     all_tweets,
                                     'processed_data/dependency_parsed_tweets.txt',
                                     gzip_final_output=False)[:-1]

write_dep_parse_with_tweet_ids_file = codecs.open("dep_parse_w_ids.txt","w","utf8")

for i, parse in enumerate(parse_data):
    write_dep_parse_with_tweet_ids_file.write(str(all_tweets[i].id) + "\n")
    write_dep_parse_with_tweet_ids_file.write(parse)
    write_dep_parse_with_tweet_ids_file.write("\n\n")

write_dep_parse_with_tweet_ids_file.close()