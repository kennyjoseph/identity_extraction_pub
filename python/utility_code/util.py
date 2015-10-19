# -*- coding: utf-8 -*-

__author__ = 'kjoseph'

import re
from glob import glob
import cPickle as pickle
import codecs
from itertools import groupby
import string
from contextlib import closing
from itertools import chain, groupby
from seqlearn.evaluation import bio_f_score
from sklearn.metrics import accuracy_score
import gzip
import numpy as np


TWEEBOPARSER_LOCATION = '/Users/kennyjoseph/git/thesis/TweeboParser'
IDENTITY_DICTIONARIES_LOCATION = 'dictionaries/identity/'
NON_IDENTITY_DICTIONARIES_LOCATION = 'dictionaries/non_identity_words/'
BOOTSTRAPPED_DICTIONARY_LOCATION = 'processed_data/twitter_supervised_results.tsv'

EXPERT_NON_IDENTITIES = {'i','me',"i'd","i've","i'm","i'll","my","myself",
                         'u','you',"your","you're",
                         'we','us','our',"let's","they're",
                         "he","she"'his','her','him','shes','hes', "he's",
                         "others", "group of people","someone",'people',"anyone",
                         "everyone","y'all","humans", "human","human beings","nobody", "person","ppl",
                         "you guys",
                         'god','lord'
                         }

STOP_WORD_REGEX = re.compile("(^(the|a|an|your|my|those|you|this|his|her|these|those|their|our|some)[ ]+)|(#)",re.IGNORECASE|re.UNICODE)
POSSESSIVE_REGEX = re.compile(u"['’′]?[s]?['’′]?$",re.U|re.I)

try:
    # UCS-4
    EMOTICONS = re.compile(u'[\U00010000-\U0010ffff]')
    EMOTICONS_2 = re.compile(u'[\u2700-\u27BF\u2600-\u26FF\u2300-\u23FF]')
except re.error:
    # UCS-2
    EMOTICONS = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
    EMOTICONS_2 = re.compile(u'[\u2700-\u27BF\u2600-\u26FF\u2300-\u23FF]')
emoji_block0 = re.compile(u'[\u2600-\u27BF]')
emoji_block1 = re.compile(u'[\uD83C][\uDF00-\uDFFF]')
emoji_block1b = re.compile(u'[\uD83D][\uDC00-\uDE4F]')
emoji_block2 = re.compile(u'[\uD83D][\uDE80-\uDEFF]')

INSTAGRAM_EMOJI_RE = re.compile(u"(?:[\xA9\xAE\u203C\u2049\u2122\u2139\u2194-\u2199\u21A9\u21AA\u231A\u231B\u2328\u2388\u23CF\u23E9-\u23F3\u23F8-\u23FA\u24C2\u25AA\u25AB\u25B6\u25C0\u25FB-\u25FE\u2600-\u2604\u260E\u2611\u2614\u2615\u2618\u261D\u2620\u2622\u2623\u2626\u262A\u262E\u262F\u2638-\u263A\u2648-\u2653\u2660\u2663\u2665\u2666\u2668\u267B\u267F\u2692-\u2694\u2696\u2697\u2699\u269B\u269C\u26A0\u26A1\u26AA\u26AB\u26B0\u26B1\u26BD\u26BE\u26C4\u26C5\u26C8\u26CE\u26CF\u26D1\u26D3\u26D4\u26E9\u26EA\u26F0-\u26F5\u26F7-\u26FA\u26FD\u2702\u2705\u2708-\u270D\u270F\u2712\u2714\u2716\u271D\u2721\u2728\u2733\u2734\u2744\u2747\u274C\u274E\u2753-\u2755\u2757\u2763\u2764\u2795-\u2797\u27A1\u27B0\u27BF\u2934\u2935\u2B05-\u2B07\u2B1B\u2B1C\u2B50\u2B55\u3030\u303D\u3297\u3299]|\uD83C[\uDC04\uDCCF\uDD70\uDD71\uDD7E\uDD7F\uDD8E\uDD91-\uDD9A\uDE01\uDE02\uDE1A\uDE2F\uDE32-\uDE3A\uDE50\uDE51\uDF00-\uDF21\uDF24-\uDF93\uDF96\uDF97\uDF99-\uDF9B\uDF9E-\uDFF0\uDFF3-\uDFF5\uDFF7-\uDFFF]|\uD83D[\uDC00-\uDCFD\uDCFF-\uDD3D\uDD49-\uDD4E\uDD50-\uDD67\uDD6F\uDD70\uDD73-\uDD79\uDD87\uDD8A-\uDD8D\uDD90\uDD95\uDD96\uDDA5\uDDA8\uDDB1\uDDB2\uDDBC\uDDC2-\uDDC4\uDDD1-\uDDD3\uDDDC-\uDDDE\uDDE1\uDDE3\uDDEF\uDDF3\uDDFA-\uDE4F\uDE80-\uDEC5\uDECB-\uDED0\uDEE0-\uDEE5\uDEE9\uDEEB\uDEEC\uDEF0\uDEF3]|\uD83E[\uDD10-\uDD18\uDD80-\uDD84\uDDC0]|(?:0\u20E3|1\u20E3|2\u20E3|3\u20E3|4\u20E3|5\u20E3|6\u20E3|7\u20E3|8\u20E3|9\u20E3|#\u20E3|\\*\u20E3|\uD83C(?:\uDDE6\uD83C(?:\uDDEB|\uDDFD|\uDDF1|\uDDF8|\uDDE9|\uDDF4|\uDDEE|\uDDF6|\uDDEC|\uDDF7|\uDDF2|\uDDFC|\uDDE8|\uDDFA|\uDDF9|\uDDFF|\uDDEA)|\uDDE7\uD83C(?:\uDDF8|\uDDED|\uDDE9|\uDDE7|\uDDFE|\uDDEA|\uDDFF|\uDDEF|\uDDF2|\uDDF9|\uDDF4|\uDDE6|\uDDFC|\uDDFB|\uDDF7|\uDDF3|\uDDEC|\uDDEB|\uDDEE|\uDDF6|\uDDF1)|\uDDE8\uD83C(?:\uDDF2|\uDDE6|\uDDFB|\uDDEB|\uDDF1|\uDDF3|\uDDFD|\uDDF5|\uDDE8|\uDDF4|\uDDEC|\uDDE9|\uDDF0|\uDDF7|\uDDEE|\uDDFA|\uDDFC|\uDDFE|\uDDFF|\uDDED)|\uDDE9\uD83C(?:\uDDFF|\uDDF0|\uDDEC|\uDDEF|\uDDF2|\uDDF4|\uDDEA)|\uDDEA\uD83C(?:\uDDE6|\uDDE8|\uDDEC|\uDDF7|\uDDEA|\uDDF9|\uDDFA|\uDDF8|\uDDED)|\uDDEB\uD83C(?:\uDDF0|\uDDF4|\uDDEF|\uDDEE|\uDDF7|\uDDF2)|\uDDEC\uD83C(?:\uDDF6|\uDDEB|\uDDE6|\uDDF2|\uDDEA|\uDDED|\uDDEE|\uDDF7|\uDDF1|\uDDE9|\uDDF5|\uDDFA|\uDDF9|\uDDEC|\uDDF3|\uDDFC|\uDDFE|\uDDF8|\uDDE7)|\uDDED\uD83C(?:\uDDF7|\uDDF9|\uDDF2|\uDDF3|\uDDF0|\uDDFA)|\uDDEE\uD83C(?:\uDDF4|\uDDE8|\uDDF8|\uDDF3|\uDDE9|\uDDF7|\uDDF6|\uDDEA|\uDDF2|\uDDF1|\uDDF9)|\uDDEF\uD83C(?:\uDDF2|\uDDF5|\uDDEA|\uDDF4)|\uDDF0\uD83C(?:\uDDED|\uDDFE|\uDDF2|\uDDFF|\uDDEA|\uDDEE|\uDDFC|\uDDEC|\uDDF5|\uDDF7|\uDDF3)|\uDDF1\uD83C(?:\uDDE6|\uDDFB|\uDDE7|\uDDF8|\uDDF7|\uDDFE|\uDDEE|\uDDF9|\uDDFA|\uDDF0|\uDDE8)|\uDDF2\uD83C(?:\uDDF4|\uDDF0|\uDDEC|\uDDFC|\uDDFE|\uDDFB|\uDDF1|\uDDF9|\uDDED|\uDDF6|\uDDF7|\uDDFA|\uDDFD|\uDDE9|\uDDE8|\uDDF3|\uDDEA|\uDDF8|\uDDE6|\uDDFF|\uDDF2|\uDDF5|\uDDEB)|\uDDF3\uD83C(?:\uDDE6|\uDDF7|\uDDF5|\uDDF1|\uDDE8|\uDDFF|\uDDEE|\uDDEA|\uDDEC|\uDDFA|\uDDEB|\uDDF4)|\uDDF4\uD83C\uDDF2|\uDDF5\uD83C(?:\uDDEB|\uDDF0|\uDDFC|\uDDF8|\uDDE6|\uDDEC|\uDDFE|\uDDEA|\uDDED|\uDDF3|\uDDF1|\uDDF9|\uDDF7|\uDDF2)|\uDDF6\uD83C\uDDE6|\uDDF7\uD83C(?:\uDDEA|\uDDF4|\uDDFA|\uDDFC|\uDDF8)|\uDDF8\uD83C(?:\uDDFB|\uDDF2|\uDDF9|\uDDE6|\uDDF3|\uDDE8|\uDDF1|\uDDEC|\uDDFD|\uDDF0|\uDDEE|\uDDE7|\uDDF4|\uDDF8|\uDDED|\uDDE9|\uDDF7|\uDDEF|\uDDFF|\uDDEA|\uDDFE)|\uDDF9\uD83C(?:\uDDE9|\uDDEB|\uDDFC|\uDDEF|\uDDFF|\uDDED|\uDDF1|\uDDEC|\uDDF0|\uDDF4|\uDDF9|\uDDE6|\uDDF3|\uDDF7|\uDDF2|\uDDE8|\uDDFB)|\uDDFA\uD83C(?:\uDDEC|\uDDE6|\uDDF8|\uDDFE|\uDDF2|\uDDFF)|\uDDFB\uD83C(?:\uDDEC|\uDDE8|\uDDEE|\uDDFA|\uDDE6|\uDDEA|\uDDF3)|\uDDFC\uD83C(?:\uDDF8|\uDDEB)|\uDDFD\uD83C\uDDF0|\uDDFE\uD83C(?:\uDDF9|\uDDEA)|\uDDFF\uD83C(?:\uDDE6|\uDDF2|\uDDFC))))[\ufe00-\ufe0f\u200d]?",re.U)

def get_tweet_text_sub_emoticons(tweet):
    return EMOTICONS_2.sub("*",EMOTICONS.sub("*",tweet.text))


def remove_emoji(text):
    for expr in [emoji_block0,emoji_block1,emoji_block1b,emoji_block2]:
        text = expr.sub("", text)
    return text


def get_cleaned_text(text):
    try:
        return remove_emoji(text.lower().replace("'s","").strip(string.punctuation))
    except:
        return text



def mkdir_no_err(dir_name):
    try:
        os.mkdir(dir_name)
    except:
        pass

def powerset(iterable,combs=None):
    from itertools import combinations
    from itertools import chain
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    if not combs:
        combs = range(1,len(s)+1)
    return chain.from_iterable(combinations(s, r) for r in combs)

def read_grouped_by_newline_file(filename):
    if not filename.endswith(".gz"):
        contents = codecs.open(filename,'r','utf8')
    else:
        zf = gzip.open(filename, 'rb')
        reader = codecs.getreader("utf-8")
        contents = reader(zf)
    lines = (line.strip() for line in contents)
    data = (grp for nonempty, grp in groupby(lines, bool) if nonempty)
    return [list(g) for g in data]

def extract_tarfile(tar_url, extract_path='.'):
    import tarfile
    print tar_url
    tar = tarfile.open(tar_url, 'r')
    for item in tar:
        tar.extract(item, extract_path)
        if item.name.find(".tgz") != -1 or item.name.find(".tar") != -1:
            extract(item.name, "./" + item.name[:item.name.rfind('/')])

def advance_file(text_file,line_index,text_index,full_text):
    l = text_file[line_index]
    line_index += 1
    text_index += len(l)
    full_text += l
    return l, text_index,line_index,full_text


def is_id_or_end(text_file, line_index):
    if line_index +1 >= len(text_file):
        return True
    try:
        int(text_file[line_index+1].strip())
        return True
    except:
        return False


# read in everything in output into dictionary
def get_original_tweet_data():
    tweets_to_type = {}
    for fil in glob("picl/*"):
        #print fil
        d = fil.replace(".p","").split("_")
        term = d[0]
        type = "non_reply" if len(d) == 3 else "reply"

        dat = pickle.load(open(fil,"rb"))
        for tweet in dat:
            tweets_to_type[tweet.id] = TweetInfo(tweet,term,type)
    print 'done loading original'
    return tweets_to_type


def create_dp_text(dp_terms):
    dp_text = dp_terms[0]
    if len(dp_terms) == 1:
        return dp_text

    for term in dp_terms[1:]:
        if term not in string.punctuation:
            dp_text += ' '
        dp_text += term

    return dp_text


class TweetInfo:

    def __init__(self,tweet,term,type):
        self.tweet = tweet
        self.term = term
        self.type = type
        self.annotations_map = {}


class Annotation:

    def __init__(self,text=None,type=None,starting_index=None,ending_index=None):
        self.text = text
        self.type = type
        self.starting_index = starting_index
        self.ending_index = ending_index

    def __unicode__(self):
        return " ".join([self.text, self.type, str(self.starting_index), str(self.ending_index)])

    def from_text(self, text_string):
        text_spl = text_string.split(" ")
        self.ending_index = int(text_spl[-1])
        self.starting_index = int(text_spl[-2])
        self.type = text_spl[-3]
        self.text = " ".join(text_spl[0:-3])
        return self


    def find_match(self, list_of_annotations):
        for i, ann in enumerate(list_of_annotations):
            if ann.type != self.type:
                continue
            if ann.starting_index == self.starting_index and ann.ending_index == self.ending_index:
                return i, ann, "exact"
            if (abs(ann.starting_index - self.starting_index) == 1  and ann.ending_index == self.ending_index) or\
               (abs(ann.ending_index - self.ending_index) == 1 and ann.starting_index == self.starting_index):
                return i, ann, 'off_by_1'
            if STOP_WORD_REGEX.sub("",ann.text) == STOP_WORD_REGEX.sub("",self.text) and\
               ann.ending_index == self.ending_index:
                return i, ann, 'stop_word'
            if POSSESSIVE_REGEX.sub("",ann.text) == POSSESSIVE_REGEX.sub("",self.text) and\
               ann.starting_index == self.starting_index:
                return i, ann, 'possessive'
            #if ann.ending_index == self.ending_index:
            #    return i, ann, "ending_ind"
        return -1, None, "no_match"

    #def __str__(self):
    #    return " ".join([self.text, self.type, str(self.starting_index), str(self.ending_index)])



def analyze_results(y_true,y_pred):
    print len(y_true), len(y_pred)

    #for v in ['B-Iden','B-Ind']:

    print("Accuracy: %.3f" % (100 * accuracy_score(y_true, y_pred)))
    print("CoNLL F1: %.3f" % (100 * bio_f_score(y_true, y_pred)))
    got_id = 0
    tot_true_id = 0
    tot_false_id = 0
    for i, lab in enumerate(y_true):
        if lab != 'O':
            tot_true_id +=1
        if y_pred[i] != 'O':
            tot_false_id += 1
        if lab != 'O' and y_pred[i] != 'O':
            got_id +=1
    if tot_true_id > 0 and tot_false_id > 0:
        print got_id/float(tot_true_id), got_id/float(tot_false_id)







