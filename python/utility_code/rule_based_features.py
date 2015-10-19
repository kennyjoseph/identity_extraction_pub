#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'kennyjoseph'

from util import *
from dependency_parse_handlers import *
from dependency_parse_object import get_cleaned_text

def get_dependency_parse_features(dep_parses):
    features_dict = {}

    for dep_objs in dep_parses:

        features = defaultdict(list)

        for dp_obj in dep_objs:
            if dp_obj.head > 0:
                features[dp_obj.id-1].append("head_word:"+dep_objs[dp_obj.head-1].text)

        parse_out, term_map, map_to_head, non_terms = get_parse(dep_objs)
        entities, proper_nouns, entity_ids, proper_ids = get_entities_from_parse(term_map)

        for i, e in enumerate(entities):
            e = remove_emoji(e)

            if '@' in e or ('#' in e and len(e.split(" ")) == 1):
                continue

            atleast_one_noun = False
            for eid in entity_ids[i]:
                if dep_objs[eid-1].postag in ['N','^','A']:
                    atleast_one_noun = True
                    break
            if not atleast_one_noun:
                continue

            last_obj = dep_objs[entity_ids[i][-1]-1]
            features[entity_ids[i][-1]-1].append('last_word_in_entity')

            for fid in entity_ids[i][:-1]:
                features[fid-1].append('not_last_word_in_entity')
                features[fid-1].append('word_last_word_in_entity:'+last_obj.text)

            features[entity_ids[i][-1]-1].append('word_last_word_in_entity:'+last_obj.text)

            #for id in entity_ids[i]:
            #        features[id-1].append('solid_entity')

        for i, e in enumerate(proper_nouns):
            for id in proper_ids[i]:
                features[id-1].append('proper_noun')

        features_dict[dep_objs[0].tweet_id] = features
    return features_dict




def get_wordforms_to_lookup(obj):
    if remove_emoji(obj.text) == '':
        return {}
    orig = obj.text.lower().replace("'s","")
    cleaned_text = get_cleaned_text(obj.text.lower())
    cleaned_singular = get_cleaned_text(obj.singular_form)
    cleaned_lemma = get_cleaned_text(obj.lemma)
    to_ret = {}
    #specific order, for overwrites
    to_ret[cleaned_lemma]  = "clean_lemma"
    to_ret[cleaned_singular] = "clean_sing"
    to_ret[cleaned_text] = "clean_text"
    to_ret[orig] = "orig"
    #if len(cleaned_text) and cleaned_text[-1] == 's':
    #    to_ret[cleaned_text[:-1]] = 'no_s'

    spl = re.split("/|-",cleaned_text)
    if len(spl) > 1 and ' ' not in cleaned_text:
        for x in re.split("/",cleaned_text):
            to_ret[x] = 'cleaned_split'
    return to_ret

def look_in_dict(dep_parses,dictionary=None, sets=None,set_names=None):

    feature_dict = {}
    for dep_objs in dep_parses:

        features = defaultdict(set)

        for i in range(len(dep_objs)):
            for j in range(min(2,len(dep_objs) - i)):
                dp_objs = dep_objs[i:(i+j+1)]
                dp_obj = dp_objs[0] if len(dp_objs) == 1 else DependencyParseObject().join(dp_objs)
                # Do dictionary lookups
                word_forms = get_wordforms_to_lookup(dp_obj)
                for w, val in word_forms.items():
                    in_dicts = set()
                    if w == '':
                        continue
                    if dictionary:
                        in_dicts = dictionary.GetDictVector(w)

                    if sets:
                        for s_ind, s in enumerate(sets):
                            if w in s:
                                in_dicts.add(set_names[s_ind])

                    for dictname in in_dicts:
                        for oid in dp_obj.all_original_ids:
                            if j ==0:
                                features[oid-1].add("in_dict:"+dictname)
                            else:
                                features[oid-1].add("n_gram:in_dictionary:"+dictname)

        feature_dict[dep_objs[0].tweet_id] = features
    return feature_dict
