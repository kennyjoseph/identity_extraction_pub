from utility_code.run_helpers import *
from utility_code.evaluation import *
from utility_code.create_features import *
from twitter_dm.utility.general_utils import tab_stringify_newline
import random


CONLL_FILE = "processed_data/final_all_conll_w_all_features.txt"

model, all_dictionaries, ark_clusters, sets, names = get_init_data('gensim_model/glove_twitter_50_raw_model.txt.gz',
                                                                   "processed_data/50mpaths2",
                                                                   "dictionaries/*/*",
                                                                   BOOTSTRAPPED_DICTIONARY_LOCATION)

features_from_conll_file, dictionary_data = get_all_features(CONLL_FILE,all_dictionaries,ark_clusters,sets,names)

# get ids of all random, put in a set, then iterate through
random.seed(0)
all_random_ids = get_test_ids(CONLL_FILE, 0, -1, -1)
random.shuffle(all_random_ids)

output_file = open("results/param_tuning_results.tsv","w")

for fold in range(5):

    output, models, preds = run_all_on_test_ids(fold,
                                                all_random_ids[(fold*150):( (fold+1)*150)],
                                                model,
                                                features_from_conll_file,
                                                dictionary_data,
                                                eval_params = [.4,.45,.5,.55,.6],
                                                cutoff_params=[.0001,.0005,.001],
                                                use_filtered_params=[True,False],
                                                datasets_to_use = ['x','wv','x_wv','all_wv','x_wv_ls','full'],
                                                regularization_params = [.53,.58,.6,.63,.65])
    for o in output:
        output_file.write(tab_stringify_newline(o))

output_file.close()

