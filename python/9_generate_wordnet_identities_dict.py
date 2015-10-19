__author__ = 'kennyjoseph'
from glob import glob
from utility_code.util import IDENTITY_DICTIONARIES_LOCATION,NON_IDENTITY_DICTIONARIES_LOCATION
from nltk.corpus import wordnet as wn
from Queue import Queue

from pywsd.baseline import max_lemma_count as most_frequent_sense
import os

def wordnet2():
    to_visit_queue = Queue()
    identities = set()

    act_identities = [x.strip() for x in open(os.path.join(IDENTITY_DICTIONARIES_LOCATION,"identities.txt"))]
    to_visit_queue.put(wn.synset('person.n.01'))

    all_identity_terms = set()

    while not to_visit_queue.empty():
        val = to_visit_queue.get()
        hypos = val.hyponyms()
        #if len(hypos):
        [to_visit_queue.put(x) for x in hypos]
        for lemma in val.lemmas():
            all_identity_terms.add(lemma.name().lower())
            mf_synset = most_frequent_sense(lemma.name())
            if mf_synset == val and len(lemma.name()) > 2:
                #print 'yep: ', lemma.name().lower()
                identities.add(lemma.name().lower())
            #else:
            #    print 'nope: ', lemma.name().lower()

    f = open(os.path.join(IDENTITY_DICTIONARIES_LOCATION,"wordnet_identities.txt"),"w")

    for p in identities:
        f.write(p.replace("_"," ")+"\n")
    f.close()

    a_f = open("tmp/all_wordnet_identities_terms.txt","w")
    for p in all_identity_terms:
        a_f.write(p.replace("_"," ")+"\n")
    a_f.close()


    all_person = set(wn.synset('person.n.01').closure(lambda s: s.hyponyms()))
    f = open(os.path.join(NON_IDENTITY_DICTIONARIES_LOCATION,"wordnet.txt"),"w")
    all_non_people = set()
    for s in list(wn.all_synsets('n'))+list(wn.all_synsets('a')):
        if s not in all_person and 'person' not in s.definition():
            for lemma in s.lemmas():
                lem_name = lemma.name().lower()
                if lem_name not in act_identities and lem_name not in all_identity_terms and lem_name[:-1] not in identities and 'person' not in str(lemma)\
                        and 'people' not in lem_name and 'police' not in lem_name and 'body' not in lem_name\
                        and 'girl' not in lem_name and ' boy' not in lem_name and ' man' not in lem_name and \
                                ' woman' not in lem_name and len(lem_name) > 2:
                    all_non_people.add(lem_name)

    for lem_name in all_non_people:
        f.write(lem_name.replace("_"," ").lower()+"\n")
    f.close()

wordnet2()