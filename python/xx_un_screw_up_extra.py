### I did something weird to make sure people only had to label exactly 150 tweets.
### it ended up backfiring, so I had to fix that. In general you shouldn't need this script
__author__ = 'kjoseph'

import glob
import codecs
from collections import Counter
from util import *

all_ids = set()
full_text = ""
i = 0
for fil in glob.glob("data/extra/*.txt"):

    text_file = codecs.open(fil,"r","utf8").readlines()

    line_index = 0
    text_index = 0
    # map tweets to indices in file
    tmp_text = ''
    while line_index < len(text_file):

        l, text_index,line_index,tmp_text = advance_file(text_file,line_index,text_index,tmp_text)

        tweet_start_index = text_index
        tweet_id = int(l.strip())

        while True:
            l, text_index,line_index,tmp_text = advance_file(text_file,line_index,text_index,tmp_text)
            if l == '\n' and is_id_or_end(text_file,line_index):
                tweet_end_index = text_index
                line_index += 1
                text_index += 1
                tmp_text += '\n'
                if tweet_id not in all_ids:
                    full_text += tmp_text
                    i += 1
                    all_ids.add(tweet_id)
                tmp_text = ''
                break

for f in ['extra_1','extra_2']:
    fil = codecs.open(f+".txt","w","utf8")
    fil.write(full_text)
    fil.close()