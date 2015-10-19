__author__ = 'kennyjoseph'
import numpy as np
from evaluation import evaluate
from util import get_cleaned_text
from sklearn.feature_extraction.text import CountVectorizer
from functools import partial
from sklearn.linear_model import LogisticRegression
from create_features import *
import codecs
from collections import defaultdict
from twitter_dm.utility.tweet_utils import get_stopwords

npcat = partial(np.concatenate, axis=1)
stopwords = get_stopwords()

def run_all_on_test_ids(fold,
                        test_ids,
                        word_vector_model,
                        features_from_conll,
                        dict_for_filter,
                        eval_params = [0.25,0.3,0.35,0.4,.45,.5,.6],
                        cutoff_params=[.0001],
                        use_filtered_params=[True],
                        datasets_to_use = ['full'],#'x','wv','x_wv','all_wv',
                        regularization_params = [.6]
                        ):

    return_info = []
    models = []
    predictions = []

    labels, features, obj_inds,\
    word_list, head_word_list,word_minus_one_list,\
    last_entity_word_list = configure_features_for_wordvectors_and_remove_twitterner(features_from_conll)


    train_inds,\
    test_inds,\
    stopword_train_inds,\
    stopword_test_inds = get_train_test_inds_w_filter(test_ids,dict_for_filter, obj_inds)


    w_vec = get_vector_rep_from_wordlist(word_list, word_vector_model, 50, True)
    head_vec = get_vector_rep_from_wordlist(head_word_list, word_vector_model, 50, True)
    last_vec = get_vector_rep_from_wordlist(last_entity_word_list, word_vector_model, 50, True)

    for cutoff_param in cutoff_params:

        count_vec = CountVectorizer(tokenizer=lambda x: x.split("|"),min_df=cutoff_param)
        X = count_vec.fit_transform(features).todense()
        y = np.array(labels)

        for use_filtered in use_filtered_params:
            to_use_train = train_inds
            to_use_test = test_inds
            to_use_stopword_inds = stopword_test_inds

            if not use_filtered:
                to_use_train = sorted(train_inds+stopword_train_inds)
                to_use_test = sorted(test_inds+stopword_test_inds)
                to_use_stopword_inds = []

            dataset_dict = {'x' : X,
                            'wv' : w_vec,
                            'x_wv' : npcat((X,w_vec)),
                            'all_wv': npcat((w_vec,head_vec,last_vec)),
                            'x_wv_ls' : npcat((X,w_vec,last_vec)),
                            'full' : npcat((X,w_vec,head_vec,last_vec)),
                            }

            for dataset_key in datasets_to_use:
                if dataset_key not in dataset_dict:
                    print 'KEY::: ', dataset_key, ' NOT IN DATASET OPTIONS, SKIPPING'
                    continue

                dataset = dataset_dict[dataset_key]

                pre_mod_out = [fold,cutoff_param,use_filtered,dataset_key]
                for c_val in regularization_params:

                    res,model,pred = run_and_output_model(dataset,y,
                                                          LogisticRegression(C=c_val,penalty='l1'),
                                                          obj_inds,
                                                          to_use_train,to_use_test,
                                                          eval_params,
                                                          pre_mod_out+[c_val],
                                                          to_use_stopword_inds)

                    return_info += res
                    models.append( model)
                    predictions.append(pred)
                print 'd ', fold
    return return_info, models, predictions




def run_and_output_model(X, y, model, obj_inds,
                         train_inds, test_inds,
                         eval_params, other_params,
                         stopword_test_inds):
    X_train = X[train_inds, :]
    y_train = y[train_inds]
    X_test = X[test_inds, :]
    y_test = y[test_inds]
    model = model.fit(X_train,y_train)

    if X_test.shape[0] == 0:
        return [], model, []

    predicted_prob = model.predict_proba(X_test)

    ret_dat = []

    stopword_test_inds_0 = []
    stopword_test_inds_1 = []

    for x in stopword_test_inds:
        if y[x] == 1:
            stopword_test_inds_1.append(x)
        else:
            stopword_test_inds_0.append(x)

    if len(stopword_test_inds):
        extra_tn = len(stopword_test_inds_0)
        extra_fn = len(stopword_test_inds_1)
        y_test = np.concatenate((y_test,np.array([0]*extra_tn),np.array([1]*extra_fn)),axis=0)
        predicted_prob = np.concatenate((predicted_prob,[[1,0]]*(extra_tn+extra_fn)),axis=0)
        test_inds = test_inds + stopword_test_inds_0 + stopword_test_inds_1

    for p in eval_params:
        o = evaluate(p, y_test, predicted_prob,obj_inds,test_inds,print_eval=False)
        ret_dat.append(other_params+o)

    return ret_dat, model, predicted_prob



def get_train_test_inds_w_filter(test_ids, dict_for_filter,obj_inds):
    train_inds = []
    test_inds = []
    stopword_train_inds = []
    stopword_test_inds = []
    for i, obj in enumerate(obj_inds):
        filter_out = should_filter(obj,dict_for_filter,lambda x: False)

        if obj.tweet_id in test_ids:
            if filter_out:
                stopword_test_inds.append(i)
            else:
                test_inds.append(i)
        else:
            if filter_out:
                stopword_train_inds.append(i)
            else:
                train_inds.append(i)

    return train_inds, test_inds, stopword_train_inds, stopword_test_inds


def write_out_predictions(outfile_name,test_data,obj_inds, test_inds, y, predicted_prob):
    pred_labs = defaultdict(dict)
    for i in range(len(y)):
        obj = obj_inds[test_inds[i]]
        if predicted_prob[i,1] >= .5:
            pred_labs[obj.tweet_id][obj.id] = "Identity"
        else:
            pred_labs[obj.tweet_id][obj.id] = "O"

    out_fil = codecs.open(outfile_name,"w","utf8")
    for k, row in test_data.items():
        i = 1
        for x in row:
            lab = pred_labs[k][i]
            out_fil.write(x + "\t" + lab  + "\n")
            i += 1
        out_fil.write("\n")
    out_fil.close()