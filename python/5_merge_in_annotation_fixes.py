__author__ = 'kjoseph'

import codecs

import sys
import re
import string
from utility_code.util import *

# read in dependency parsed data
dep_parses_map = {int(g[0]): g[1:] for g in read_grouped_by_newline_file('processed_data/dep_parse_w_ids.txt')}

# read in matched labels (including empty)
match_dat = read_grouped_by_newline_file('processed_data/matched_annotations.txt')
annotations_map = dict()
for m in match_dat:
    if len(m) > 1:
        annotations_map[int(m[0])] = [Annotation().from_text(x) for x in m[1:]]
    else:
        annotations_map[int(m[0])] = []

# append with fixed_data
data = read_grouped_by_newline_file("processed_data/fixed_unmatched.txt")
for d in data:
    if len(d) > 2:
        annotations_map[int(d[0])] += [Annotation().from_text(x) for x in d[2:]]

tweet_id_to_tweetinfo = get_original_tweet_data()


conll_out = codecs.open("processed_data/all_conll_data.txt","w","utf8")

# merge dependency parse with labels, tweet ids, dataset
# to do so, strip annotations of punctuation
for id, annotations in annotations_map.items():

    tweetinfo_for_tweet = tweet_id_to_tweetinfo[id]

    tweet_text = get_tweet_text_sub_emoticons(tweetinfo_for_tweet.tweet)
    dependency_parse = [ [d, 'O'] for d in dep_parses_map[id]]

    dp_terms = []
    for i, dp in enumerate(dependency_parse):
        term = dp[0].split("\t")[1]
        dp_terms.append(term)
    dp_text = create_dp_text(dp_terms)

    # everything is Outside unless we find an annotation for it
    # very dumb and slow and need to do manual stuff after but right
    for ann in annotations:

        # remove stop words at beginning
        ann.text = ann.text.strip(string.punctuation)
        ann.text = STOP_WORD_REGEX.sub("",ann.text)
        init_ann_size = len(re.split("[;. ,]",ann.text))
        ann_sizes = {init_ann_size, len(ann.text.split(" "))}
        if len(re.findall("[;.,]",ann.text)):
            ann_sizes.add(init_ann_size+len(re.findall("[;.,]",ann.text))-1)

        indices_found_at = []
        for ann_size in ann_sizes:
            i = 0
            while i+ann_size <= len(dependency_parse):
                text = create_dp_text(dp_terms[i:(i+ann_size)])

                if text == ann.text or POSSESSIVE_REGEX.sub("",text) == ann.text\
                 or text.replace("#","") == ann.text or\
                 POSSESSIVE_REGEX.sub("",text.replace("#","")) == ann.text:
                    indices_found_at.append([i,ann_size])

                i += 1

        if len(indices_found_at) != 1:
            print 'WILL HAVE TO EDIT MANUALLY:::: ', ann.text
            print dp_text
        else:
            ind, ann_size = indices_found_at[0]
            type_of_ann = ann.type
            dependency_parse[ind][1] = 'B-'+type_of_ann
            for v in range(ind+1,ind+ann_size):
                dependency_parse[v][1] = 'I-'+type_of_ann

    for dp in dependency_parse:
        conll_out.write("\t".join([dp[0], str(tweetinfo_for_tweet.tweet.id),
                                   tweetinfo_for_tweet.term.replace("output/",""), tweetinfo_for_tweet.type,
                                   dp[1]]) + "\n")
    conll_out.write("\n")


conll_out.close()



