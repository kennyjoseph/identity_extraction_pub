__author__ = 'kennyjoseph'

import os
import glob
import json

from utility_code.util import *
from twitter_dm.utility.general_utils import get_handles
from twitter_dm.nlp.tweeboparser import dependency_parse_tweets
from twitter_dm.Tweet import Tweet
from identity_extraction.python.utility_code.dependency_parse_object import DependencyParseObject

PATH_TO_TWITTER_APP_HANDLES = "/Users/kennyjoseph/git/thesis/thesis_python/twitter_login_creds"

def get_raw_tweets(tweet_ids, output_filename):

    if os.path.exists(output_filename):
        tweet_data = [json.loads(s) for s in codecs.open(output_filename,"r","utf8")]
        print 'N TWEETS: ', len(tweet_data)
        return {tw['id_str']:tw for tw in tweet_data}

    ## collect the raw json for the tweets - need the raw text for the dependency parsing
    handles = get_handles(glob.glob(os.path.join(PATH_TO_TWITTER_APP_HANDLES,"*.txt")))

    output_fil = codecs.open(output_filename,"w","utf8")
    i = 0
    tweets_chunked = []
    while i < len(tweet_ids):
        tweets_chunked.append(tweet_ids[i:(i+100)])
        i += 100

    tweets_chunked.append(tweet_ids[i:len(tweet_ids)])

    good_tweets_json = {}
    good = 0
    for i, tweet_chunk in enumerate(tweets_chunked):
        tweet_data = handles[i].get_from_url("statuses/lookup.json", {"id": ",".join(tweet_chunk)})
        tweet_chunk = set(tweet_chunk)
        for tw in tweet_data:
            good += 1
            if tw['id_str'] in good_tweets_json:
                print 'AHHHH', i
            good_tweets_json[tw['id_str']] = tw
            tweet_chunk.remove(tw['id_str'])
            output_fil.write(json.dumps(tw)+"\n")
    print('N GOOD: ', good)

    output_fil.close()
    return good_tweets_json

#get labeled tweets
orig_data = read_grouped_by_newline_file("test_data/daily547.supertsv")
labeled_data = {x[0]: x[1:] for x in orig_data}
tweet_ids = [x[0] for x in orig_data]
print 'N TW IDS: ', len(tweet_ids), len(set(tweet_ids))

# get original json
good_tweets_json = get_raw_tweets(tweet_ids, "test_data/still_alive_tweets.json")
print 'N TWEETS: ', len(good_tweets_json)

# dependency parse
all_tweets = [Tweet(t) for t in good_tweets_json.values()]
parse_data = dependency_parse_tweets(TWEEBOPARSER_LOCATION,
                                     all_tweets,
                                     os.path.join(os.getcwd(),'test_data/dep_parse_out.txt'))[:-1]

# okay, run java on this stuff (java -jar ... not in the script yet), save it to test_data/java_out.txt.gz
java_out = {x[0] : x[1:] for x in read_grouped_by_newline_file("test_data/java_out.txt")}
# don't run twitter ner on it right now. just not worth it

#write out the final file

final_out_file = codecs.open("test_data/final_conll_pub.txt","w","utf8")
k = 0
for i, parse in enumerate(parse_data):
    tw_id = str(all_tweets[i].id)
    java_data = java_out[tw_id]
    gold_data = labeled_data[tw_id]
    if len(parse.split("\n")) != len(java_data) or len(java_data) != len(gold_data) or len(parse.split("\n")) != len(gold_data):
        print 'Skipping, due to differences in tokenization'
        k += 1
        continue

    all_same = True
    for j, p in enumerate(parse.split("\n")):
        if p.split("\t")[1] != gold_data[j].split("\t")[1]:
            print 'funky - same length but different terms. Skipping'
            all_same = False
            k += 1
            break

    if all_same:
        for j, p in enumerate(parse.split("\n")):
            d = DependencyParseObject("\t".join([p,tw_id,"public_ark","_",gold_data[j].split("\t")[2]]))
            # get java features
            spl_java = java_data[j].split("\t")
            java_id, penn_pos_tag,word = spl_java[:3]
            java_features = '' if len(spl_java) == 3 else spl_java[3]
            d.features += [x for x in java_features.split("|") if x != '']
            d.features.append("penn_treebank_pos="+penn_pos_tag)
            final_out_file.write(d.get_conll_form()+"\n")
        final_out_file.write("\n")
final_out_file.close()
print 'Total skipped due to tokenization: ', k
