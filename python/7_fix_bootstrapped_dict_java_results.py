import sys
from operator import add
from utility_code.util import *
from pyspark import SparkContext, SparkConf
import codecs
from collections import defaultdict,Counter

import glob

def list_files(i):
    print i
    g = glob.glob("../java/ark_search_out/"+str(i).zfill(3) + "*")
    print 'globbed'
    return g

def read_file(f):
    return codecs.open(f,"r","utf8").readlines()


def get_identities(x):
    try:
        user, tw_id, is_rt, rule, middle_string, identity, post_string = x.strip().lower().split("\t")
        #print(user, tw_id, is_rt, rule, middle_string, identity, post_string)
    except:
        return ('_','_'),1

    # can represent rule w/ first letter
    rule = str(rule[0])
    if rule =='y' or rule =='u':
        rule = 'y'
    identity_data = [x.rpartition("/") for x in identity.split(" ") if "/''" not in x and x != '']
    identities = [x[0] for x in identity_data]

    if not len(identities):
        return ('_','_'),1

    if rule != 'p':
        final_identity = identities[-1]
        if identities[-1] in {'person','ppl','people'}:
            if len(identities) > 1:
                final_identity = identities[-2] + " person"
            else:
                return ('_','_'),1
        #print('FINAL IDENTITY :::: ', final_identity)
        return (rule, final_identity),1
    elif " ".join(identities) in {'other','less','own', 'certain'}:
        return ('_','_'),1
    else:
        return (rule, " ".join(identities) + " person"), 1

if __name__ == "__main__":

    conf = (SparkConf()
         .setMaster("local[*]")
         .setAppName("My app")
         .set("spark.executor.memory", "1g")
         .set("spark.driver.memory", "1g"))
    sc = SparkContext(conf=conf)
    out = sc.parallelize(range(100,1000),200)\
            .flatMap(list_files)\
            .flatMap(read_file)\
            .map(get_identities)\
            .reduceByKey(add)\
            .collect()

    of = codecs.open("processed_data/twitter_supervised_results.tsv","w","utf8")
    for (word, count) in out:
       of.write("\t".join(word) + "\t" + str(count) + "\n")

    of.close()

    sc.stop()
