__author__ = 'kennyjoseph'
from utility_code.RitterDictionaries import *
from utility_code.evaluation import *
from utility_code.create_features import *
from twitter_dm.utility.tweet_utils import get_stopwords
from functools import partial
from twitter_dm.utility.general_utils import tab_stringify_newline as tsn
def run_baseline_on_conll_file(conll_filename, path_to_dicts, output_filename):

    features_from_conll, blah = get_all_features(conll_filename, None, None,None,None)
    labels, features, obj_inds = configure_features_for_wordvectors_and_remove_twitterner(features_from_conll)[0:3]
    
    ## for dictionary-based evaluation
    stopwords = get_stopwords()
    
    # get all the dictionaries together
    p_look_in_dict = partial(look_in_dict, sets=[stopwords], set_names=["stopwords"])
    act_dict = p_look_in_dict(conll_filename, Dictionaries(os.path.join(path_to_dicts,'identities.txt')))
    wordnet_dict = p_look_in_dict(conll_filename, Dictionaries(os.path.join(path_to_dicts,'wordnet_identities.txt')))
    racial_dict = p_look_in_dict(conll_filename, Dictionaries(os.path.join(path_to_dicts,'racial_slur_identities.txt')))
    national_dict = p_look_in_dict(conll_filename, Dictionaries(os.path.join(path_to_dicts,'national_identities.txt')))
    job_dict = p_look_in_dict(conll_filename, Dictionaries(os.path.join(path_to_dicts,'job_identities.txt')))
    
    all_ds = Dictionaries(os.path.join(path_to_dicts,'*identities.txt'))
    all_dict = p_look_in_dict(conll_filename,all_ds)
    
    # get hte bootstrapped dictionary together
    tw_distant_supervision_identity_dat = get_twitter_distant_supervision_identity_dat("../r/output_fil.tsv")
    stopwords = get_stopwords()
    twit_sets = []
    
    for v in [10, 100, 1000, 10000,50000]:
        twit_id = set(tw_distant_supervision_identity_dat[
                      (tw_distant_supervision_identity_dat.tot > v)].term.values)
        twit_id = twit_id - stopwords
        twit_sets.append([twit_id,"twit_identities"+str(v)])
    
    all_random_ids = get_test_ids(conll_filename, 0, -1, -1)
    
    y = np.array(labels)

    output_file = open(output_filename, "w")

    #test all the basic dicts
    for d in [['act_dict',act_dict],
              ['racial_dict',racial_dict],
              ['nat_dict',national_dict],
              ['job_dict',job_dict],
              ['wordnet_dict',wordnet_dict],
              ['all_dict',all_dict]]:
        preds = get_isin_array(d[1],obj_inds)
        out = evaluate(.4, y, preds , obj_inds, all_random_ids, print_eval=True)
        output_file.write(tsn([d[0]] + out[1:]))
    
    # test the bootstrapped dicts
    for twit_set, twit_set_id in twit_sets:
        d = look_in_dict(conll_filename,sets=[twit_set,stopwords],set_names=["twit_identities", "stopwords"])
        out = evaluate(.4, y, get_isin_array(d,obj_inds), obj_inds, all_random_ids, print_eval=True)
        output_file.write(tsn([twit_set_id+"_alone"] + out[1:]))
        d = look_in_dict(conll_filename,
                     all_ds,[twit_set, stopwords],[twit_set_id,"stopwords"])
        out = evaluate(.4, y, get_isin_array(d,obj_inds), obj_inds, all_random_ids, print_eval=True)
        output_file.write(tsn([twit_set_id+"_w_all"] + out[1:]))

    output_file.close()


run_baseline_on_conll_file("processed_data/final_all_conll_w_all_features.txt",
                           IDENTITY_DICTIONARIES_LOCATION,
                           'results/baselines_on_ferg_data.tsv')

run_baseline_on_conll_file("test_data/final_conll_pub.txt",
                           IDENTITY_DICTIONARIES_LOCATION,
                           'results/baselines_on_public_data.tsv')

