__author__ = 'kjoseph'

import cPickle as pickle
from utility_code.util import *
import sys
import os
import itertools
from math import ceil
import random
import codecs
import shutil
from glob import glob
import zipfile


sys.argv = ['',
            'output/',
            '../annotation_data/',
            '13',
            '2',
            '15']

def create_file(ann,fil_name):
    filename = os.path.join(ann,"f_"+str(fil_name))
    ann_fil = codecs.open(filename+ '.ann',"w","utf8")
    ann_fil.close()
    fil = codecs.open(filename+'.txt',"w","utf8")
    return fil


place_to_get_pickled_tweets_from = os.path.join(sys.argv[1],'*.p')
annotation_directory = sys.argv[2]
num_annotators = int(sys.argv[3])
num_times_each_tweet_annotated = int(sys.argv[4])
num_tweets_per_file = int(sys.argv[5])

pickled_tweets = [pickle.load(open(filename,'rb')) for filename in glob(place_to_get_pickled_tweets_from)]

all_tweets = list(itertools.chain.from_iterable(pickled_tweets))


random.seed(0)
random.shuffle(all_tweets)

n_tweets_per_annotator = ceil(len(all_tweets) * num_times_each_tweet_annotated / float(num_annotators))

file_types_to_copy = ['*.txt','*.conf','*.ann']
annotators = []
for i in range(num_annotators):
    dir_name = os.path.join(annotation_directory,'a_'+str(i))
    mkdir_no_err(dir_name)

    for ftype in file_types_to_copy:
        for fil in glob(os.path.join(annotation_directory,ftype)):
            shutil.copy2(fil,dir_name)
    annotators.append([dir_name, n_tweets_per_annotator])



i = 0

tweets_for_annotators = [list() for i in range(num_annotators)]

for tweet_num, tweet in enumerate(all_tweets):
    for j in range(num_times_each_tweet_annotated):
        if i == num_annotators:
            i = 0
        tweets_for_annotators[i].append(tweet)
        i += 1

fil = None

for ann_id,tweets_for_annotator in enumerate(tweets_for_annotators):
    fil_name = 0
    fil = create_file(annotators[ann_id][0],fil_name)
    for i, tweet in enumerate(tweets_for_annotator):

        fil.write(str(tweet.id))
        fil.write("\n" + get_tweet_text_sub_emoticons(tweet))
        fil.write("\n\n\n")

        if (i+1) % num_tweets_per_file == 0:
            fil_name += 1
            fil.close()
            if i < len(tweets_for_annotator):
                fil = create_file(annotators[ann_id][0],fil_name)

fil.close()

zipf = zipfile.ZipFile(os.path.join(annotation_directory,'to_annotate.zip'), 'w')
for annotator in annotators:
    for root, dirs, files in os.walk(annotator[0]):
        for file in files:
            zipf.write(os.path.join(root, file))
    shutil.rmtree(annotator[0])
zipf.close()
