"""
This script cleans up the lexicon in vader to remove identity terms.

You can find an implementation of Vader that I've forked at

https://github.com/kennyjoseph/vaderSentiment

"""

__author__ = 'kennyjoseph'
from utility_code.util import *

def get_wordforms(text):
    ret = [text.lower().replace("'s","")]
    if text[-1] == 's':
        ret.append(get_cleaned_text(text[-1].lower()))
    ret.append(text)
    return ret

all_identity_words = set()

for fil in glob("dictionaries/*/*identities*"):
    for x in open(fil):
        for z in get_wordforms(x.strip()):
            all_identity_words.add(z)

print len(all_identity_words)

vsent2 = open("/Users/kennyjoseph/git/vaderSentiment/vaderSentiment/vader_sentiment_lex_no_identities.txt","w")
for f in open("/Users/kennyjoseph/git/vaderSentiment/vaderSentiment/vader_sentiment_lexicon.txt"):
    if f.split("\t")[0] not in all_identity_words:
        vsent2.write(f)
    else:
        print f.split("\t")[0]

vsent2.close()