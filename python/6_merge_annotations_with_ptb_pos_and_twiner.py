__author__ = 'kennyjoseph'
import HTMLParser

from utility_code.util import *
from utility_code.dependency_parse_object import DependencyParseObject
from identity_extraction.python.utility_code.dependency_parse_handlers import *

html_parser = HTMLParser.HTMLParser()


def do_twitter_ner_merge(dep_parse, twitter_nlp_list, i, j, output):
    if i == len(dep_parse) or j == len(twitter_nlp_list):
        return i, j, output

    dp_obj = DependencyParseObject(dep_parse[i])
    tn_id, tn_twid, tn_wd, tn_label = twitter_nlp_list[j].split("\t")
    tn_wd = html_parser.unescape(tn_wd)

    if dp_obj.text == tn_wd:
        output[dp_obj.id] = tn_label
        return do_twitter_ner_merge(dep_parse,twitter_nlp_list,i+1,j+1,output)

    # twitter_nlp substring of dependency parse text
    if tn_wd in dp_obj.text:
        # with theres something left in the twitter_nlp
        while j + 1 < len(twitter_nlp_list) and tn_wd in dp_obj.text:
            j+=1
            # check if combining leads to same string
            tn_wd += twitter_nlp_list[j].split("\t")[2]
        output[dp_obj.id] = tn_label
        return do_twitter_ner_merge(dep_parse,twitter_nlp_list,i+1,j,output)
    elif dp_obj.text in tn_wd:
        output[dp_obj.id] = tn_label
        dp_text = dp_obj.text
        while i + 1 < len(dep_parse):
            i += 1
            dp_obj = DependencyParseObject(dep_parse[i])
            # check if combining leads to same string
            dp_text += dp_obj.text
            if dp_text in tn_wd:
                output[dp_obj.id] = tn_label
            else:
                break

        return do_twitter_ner_merge(dep_parse,twitter_nlp_list,i,j+1,output)

    print 'this shouldnt happen', i, j, dep_parse.tweet_id


dep_parses = read_grouped_by_newline_file('processed_data/final_all_conll_data.txt')
twitter_nlp_data = read_grouped_by_newline_file('processed_data/twitter_nlp_tagged_data.txt')

## this is the output from PatternedIdentityOrPOSExtractor.java
output_from_java = read_grouped_by_newline_file('processed_data/java_out.txt')

twitter_nlp_map = {}
for d in twitter_nlp_data:
    twitter_nlp_map[d[0].split("\t")[1]] = d

dep_parse_map = {}
for d in dep_parses:
    obj = DependencyParseObject(d[0])
    dep_parse_map[obj.tweet_id] = d

java_out_map = {}
for d in output_from_java:
    java_out_map[d[0]] = d[1:]

i = 0
output_fil = codecs.open("processed_data/final_all_conll_w_all_features.txt","w","utf8")

for tw_id, dep_parse in dep_parse_map.items():

    twitter_nlp_list = twitter_nlp_map[tw_id]
    i, j, twitter_ner_output = do_twitter_ner_merge(dep_parse,twitter_nlp_list,0,0,{})

    java_data_for_parse = java_out_map[tw_id]

    for line in dep_parse:
        d = DependencyParseObject(line)
        spl_java = java_data_for_parse[d.id-1].split("\t")
        java_id, penn_pos_tag,word = spl_java[:3]
        java_features = '' if len(spl_java) == 3 else spl_java[3]
        d.features += [x for x in java_features.split("|") if x != '']
        d.features.append("penn_treebank_pos="+penn_pos_tag)
        d.features.append("twitter_ner="+twitter_ner_output.get(d.id,'O'))
        output_fil.write(d.get_conll_form()+"\n")

    output_fil.write("\n")

output_fil.close()