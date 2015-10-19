__author__ = 'kjoseph'

import requests
from utility_code.util import *
import codecs
from collections import Counter
from twitter_dm.nlp.tweeboparser import replace_tweet_newlines
import sys
import shutil
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')
import os


# download annotations from the server
def download_annotations_data():
    url =  "http://52.20.46.242/brat/ajax.cgi?action=downloadCollection&collection=%2F&protocol=1"
    page = requests.get(url)
    with open('annotation_output.tgz', 'wb') as output_fil:
        output_fil.write(page.content)

    extract_tarfile('annotation_output.tgz')

def get_tweet_annotations(tweet_id_to_tweetinfo):
    # for each annotator, record annotations for the tweet
    for fil in glob("data/a_*/*.ann"):
        if fil.split("/")[2].startswith("00"):
            continue

        ann_id = fil.split("/")[1]
        try:
            text_file = codecs.open(fil.replace(".ann",".txt"),"r","utf8").readlines()
        except:
            print 'text file doesnt exist for: ', fil
            continue

        full_text = ""
        line_index = 0
        text_index = 0
        id_to_starting_index_map = {}
        index_to_id_map = {}
        # map tweets to indices in file
        while line_index < len(text_file):

            l, text_index,line_index,full_text = advance_file(text_file,line_index,text_index,full_text)

            tweet_start_index = text_index
            tweet_id = int(l.strip())

            while True:
                l, text_index,line_index,full_text = advance_file(text_file,line_index,text_index,full_text)
                if l == '\n' and is_id_or_end(text_file,line_index):
                    tweet_end_index = text_index
                    line_index += 1
                    text_index += 1
                    full_text += '\n'
                    id_to_starting_index_map[tweet_id] = tweet_start_index
                    for i in range(tweet_start_index, tweet_end_index-1):
                        index_to_id_map[i] = tweet_id
                    break

        # now map annotations to the tweets

        # first, ensure there is a record that this person annotated the tweet
        # even if they didn't specify any annotations
        for tweet_id in id_to_starting_index_map.keys():
            tweet_id_to_tweetinfo[tweet_id].annotations_map[ann_id] = []

        # now fill in the annotations
        for line in codecs.open(fil,"r","utf8"):
            line_spl = line.strip().split()
            type, start,fin = line_spl[1:4]
            start = int(start)
            fin = int(fin)
            text = " ".join(line_spl[4:])

            # make sure that text matches the extracted annotation
            z = full_text[start:fin]
            if z != text:
                print 'AHHH DOESNT MATCH!!!', text, z

            tweet_id = index_to_id_map[int(start)]
            tweet_index_start = id_to_starting_index_map[tweet_id]
            # remove: skills, expert-driven non identities, god
            if '@' not in z and type != 'Skill' and \
                    (start-tweet_index_start-1 < 0 or full_text[start-1] != '@')\
                and z.lower() not in EXPERT_NON_IDENTITIES:

                tweet_id_to_tweetinfo[tweet_id].annotations_map[ann_id].append(
                                                Annotation(z, type,start-tweet_index_start,fin-tweet_index_start))

            tweet_text = get_tweet_text_sub_emoticons(tweet_id_to_tweetinfo[tweet_id].tweet)
            if tweet_text[start-tweet_index_start:fin-tweet_index_start] != z:
                print 'AHHH DOESNT MATCH HERE!!!!', tweet_text[start-tweet_index_start:fin-tweet_index_start], z
    print 'done collecting annotations'
    return tweet_id_to_tweetinfo


def get_agreement_scores(tweet_id_to_tweetinfo):
    total_annotations = 0

    match_type_counter = Counter()

    n_tweets = 0

    for id, tweetinfo in tweet_id_to_tweetinfo.iteritems():

        # if more than one person has labeled it, then check agreement
        if len(tweetinfo.annotations_map) > 1:
            if len(tweetinfo.annotations_map) > 2:
                print 'AHHH, MORE THAN TWO ANNOTATORS!!!!!'

            n_tweets += 1
            ann1_id, ann1_data = tweetinfo.annotations_map.items()[0]
            ann2_id, ann2_data = tweetinfo.annotations_map.items()[1]

            total_annotations += len(ann1_data) + len(ann2_data)
            if len(ann1_data) == len(ann2_data) == 0:
                match_type_counter['none_match'] += 1
                continue

            print '\n\n', id, tweetinfo.tweet.text
            print 'ANNOTATORS: ', ann1_id, ann2_id

            unmatched_a1_indices = []
            matched_a2_indices = set()

            for i, ann1_annotation in enumerate(ann1_data):

                matched_index, match, match_type = ann1_annotation.find_match(ann2_data)

                if match_type == 'no_match':
                    unmatched_a1_indices.append(i)
                else:
                    match_type_counter[match_type] += 1
                    print '\t', ann1_annotation.__unicode__(), ann2_data[matched_index].text, '\t', match_type
                    matched_a2_indices.add(matched_index)

            ann2_data_unmatched = [ann2_data[i] for i in range(len(ann2_data)) if i not in matched_a2_indices]
            ann1_data_unmatched = [ann1_data[i] for i in unmatched_a1_indices]
            print
            for a, b in [[ann1_id, ann1_data_unmatched], [ann2_id, ann2_data_unmatched]]:
                for ann in b:
                    print '\tUNMATCHED ::: ', a, ann.__unicode__()
                    match_type_counter['unmatched'] += 1

    print 'TOTAL TWEETS ::: ', n_tweets
    print 'TOTAL ANNOTATIONS ::: ', total_annotations

    for item, count in match_type_counter.items():
        print 'TOTAL', item, ': ', count

    n_total_tokens = 0
    for group in read_grouped_by_newline_file("processed_data/dependency_parsed_tweets.txt"):
        n_total_tokens += len(group)
    print 'TOTAL TOKENS: ', n_total_tokens


#download_annotations_data()

tweet_id_to_tweetinfo = get_original_tweet_data()

tweet_id_to_tweetinfo = get_tweet_annotations(tweet_id_to_tweetinfo)

get_agreement_scores(tweet_id_to_tweetinfo)


matched_ann_output_file = codecs.open('processed_data/matched_annotations.txt', "w","utf8")

unmatched_fn = 'processed_data/unmatched_annotations_to_fix.txt'
#if os.path.exists(unmatched_fn):
#    print ' copying over ', unmatched_fn, 'to ', unmatched_fn.replace(".txt",'_copy.txt')+' so I dont overwrite edits'
#    shutil.copy2(unmatched_fn,unmatched_fn.replace(".txt",'_copy.txt'))

unmatched_ann_output_file = codecs.open(unmatched_fn,'w','utf8')

i = 0
for id, tweetinfo in tweet_id_to_tweetinfo.iteritems():

    # if more than one person has labeled it, then check agreement
    if len(tweetinfo.annotations_map) > 1:
        if len(tweetinfo.annotations_map) > 2:
            print 'AHHH, MORE THAN TWO ANNOTATORS!!!!!'

        ann1_id, ann1_data = tweetinfo.annotations_map.items()[0]
        ann2_id, ann2_data = tweetinfo.annotations_map.items()[1]

        matched_ann_output_file.write(str(id)+"\n")

        if len(ann1_data) == len(ann2_data) == 0:
            matched_ann_output_file.write("\n")
            continue

        unmatched_a1_indices = []

        gold_annotations = []
        matched_a2_indices = set()
        for i, ann1_annotation in enumerate(ann1_data):
            matched_index, match, match_type = ann1_annotation.find_match(ann2_data)
            if match_type == 'exact':
                gold_annotations.append(ann1_annotation)
                matched_a2_indices.add(matched_index)
            elif match_type == 'no_match':
                unmatched_a1_indices.append(i)
            else:
                matched_a2_indices.add(matched_index)
                # take the longer of the two
                if ((ann1_annotation.ending_index-ann1_annotation.starting_index) -
                        (ann2_data[matched_index].ending_index-ann2_data[matched_index].starting_index)) >= 0:
                    gold_annotations.append(ann1_annotation)
                else:
                    gold_annotations.append(ann2_data[matched_index])

        # get all unmatched annotations
        ann2_data_unmatched = [ann2_data[i] for i in range(len(ann2_data)) if i not in matched_a2_indices]
        ann1_data_unmatched = [ann1_data[i] for i in unmatched_a1_indices]
        unmatched_total = ann2_data_unmatched+ann1_data_unmatched

        # we have to make sure there is no overlap between the gold and the unmatched:::
        unmatched_to_ignore = set()
        for i, unmatched_ann in enumerate(unmatched_total):
            for gold in gold_annotations:
                # if it ends before the gold starts or starts after gold ends, we're good. else, shit.
                if not (unmatched_ann.ending_index < gold.starting_index or\
                        unmatched_ann.starting_index > gold.ending_index):
                    print 'OVERLAP:::: ', unmatched_ann.__unicode__(), gold.__unicode__()
                    print '\tgoing to ignore the unmatched when writing out'
                    unmatched_to_ignore.add(i)

        unmatched_to_write_out = [unmatched_total[i] for i in range(len(unmatched_total))
                                    if i not in unmatched_to_ignore]

        if len(unmatched_to_write_out):
            unmatched_ann_output_file.write(str(id)+"\n")
            unmatched_ann_output_file.write(replace_tweet_newlines(tweetinfo.tweet.text)+"\n")

            for ann in unmatched_to_write_out:
                unmatched_ann_output_file.write(ann.__unicode__()+"\n")

            unmatched_ann_output_file.write("\n")

        for ann in gold_annotations:
            matched_ann_output_file.write(ann.__unicode__() + "\n")

        matched_ann_output_file.write("\n")

matched_ann_output_file.close()
unmatched_ann_output_file.close()
