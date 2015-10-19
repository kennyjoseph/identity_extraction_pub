__author__ = 'kennyjoseph'

from utility_code.run_helpers import *
from utility_code.evaluation import *
from gensim.models.word2vec import Word2Vec
from twitter_dm.utility.general_utils import tab_stringify_newline as tsn


CONLL_FILE = "processed_data/final_all_conll_w_all_features.txt"


model, all_dictionaries, ark_clusters, sets, names = get_init_data('gensim_model/glove_twitter_50_raw_model.txt.gz',
                                                                   "processed_data/50mpaths2",
                                                                   "dictionaries/*/*",
                                                                   BOOTSTRAPPED_DICTIONARY_LOCATION)

features_from_conll_file, dict_for_filter = get_all_features(CONLL_FILE,
                                                             all_dictionaries,
                                                             ark_clusters,
                                                             sets, names)

cutoff_param = .0001
output, models, preds = run_all_on_test_ids(0,
                                            [],
                                            model,
                                            features_from_conll_file,
                                            dict_for_filter,
                                            eval_params = [.45],
                                            cutoff_params=[cutoff_param],
                                            use_filtered_params=[True],
                                            datasets_to_use = ['full'],
                                            regularization_params = [.65])

labels, features, obj_inds,\
word_list, head_word_list,word_minus_one_list,\
last_entity_word_list = configure_features_for_wordvectors_and_remove_twitterner(features_from_conll_file)

count_vec = CountVectorizer(tokenizer=lambda x: x.split("|"),min_df=cutoff_param)
count_vec.fit_transform(features)
orig_feature_names = count_vec.get_feature_names()





print 'here... '

pub_conll, dict_for_filter_pub = get_all_features("test_data/final_conll_pub.txt",
                                                  all_dictionaries,
                                                  ark_clusters,
                                                  sets,names)

labels_pub, features_pub, obj_inds_pub,\
word_list_pub, head_list_pub, word_minus_one_list_pub,\
last_entity_word_list_pub = configure_features_for_wordvectors_and_remove_twitterner(pub_conll)

cv_pub = CountVectorizer(tokenizer=lambda x: x.split("|"),vocabulary=orig_feature_names)
X_pub = cv_pub.fit_transform(features_pub)

w_vec_pub = get_vector_rep_from_wordlist(word_list_pub, model, 50,True)
head_vec_pub = get_vector_rep_from_wordlist(head_list_pub, model, 50,True)
last_vec_pub = get_vector_rep_from_wordlist(last_entity_word_list_pub, model,50,True)


test_inds, a,  stopword_test_inds, b = get_train_test_inds_w_filter([],
                                                                   dict_for_filter_pub,
                                                                   obj_inds_pub)

y_pub = np.array(labels_pub)
D = np.concatenate((X_pub.todense(),w_vec_pub,head_vec_pub,last_vec_pub),axis=1)
predicted_prob = models[0].predict_proba(D[test_inds,:])

stopword_test_inds_0 = []
stopword_test_inds_1 = []

for x in stopword_test_inds:
    if y_pub[x] == 1:
        stopword_test_inds_1.append(x)
    else:
        stopword_test_inds_0.append(x)


if len(stopword_test_inds):
    extra_tn = len(stopword_test_inds_0)
    extra_fn = len(stopword_test_inds_1)
    y_pub = np.concatenate((y_pub[test_inds],np.array([0]*extra_tn),np.array([1]*extra_fn)),axis=0)
    predicted_prob = np.concatenate((predicted_prob,[[1,0]]*(extra_tn+extra_fn)),axis=0)
    test_inds = test_inds + stopword_test_inds_0 + stopword_test_inds_1


output_file = open("results/final_model_pub_res.tsv","w")
eval_out = evaluate(.5, y_pub, predicted_prob,obj_inds_pub,test_inds,True,True,True)
output_file.write(tsn(["final_model"] + eval_out[1:]))
output_file.close()

from utility_code.dependency_parse_object import DependencyParseObject
test_data = {DependencyParseObject(x[0]).tweet_id : x for x in
                             read_grouped_by_newline_file("test_data/final_conll_pub.txt")}

write_out_predictions("results/predictions_pub_data.txt",test_data,obj_inds_pub,test_inds,y_pub,predicted_prob)