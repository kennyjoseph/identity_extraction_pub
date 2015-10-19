from glob import glob
from twitter_dm.TwitterUser import TwitterUser
from datetime import datetime
import os
import langid
from utility_code.create_features import *
from utility_code.util import *
from twitter_dm.utility.general_utils import tab_stringify_newline as tsn
from twitter_dm.utility.general_utils import mkdir_no_err
import sys
import gzip
from utility_code.run_helpers import *
from utility_code.evaluation import *
from multiprocessing import Pool

MIN_ACCOUNT_AGE = datetime(2013,1,1)
BASE_DATA_DIR = "/Users/kennyjoseph/data/ferg/"

DP_DIR = os.path.join(BASE_DATA_DIR,"dep_parse")
PTB_DIR = os.path.join(BASE_DATA_DIR,"pos_tagged_penntreebank")
OUTPUT_DIR = os.path.join(BASE_DATA_DIR,"fin_conll_analysis")


def gen_conll_file(fil,ptb_dir, dp_dir):
    user = TwitterUser()
    user.populate_tweets_from_file(fil, do_tokenize=False)

    if 50 <= user.n_total_tweets <= 15000 and\
       user.followers_count <= 25000 and user.creation_date <= MIN_ACCOUNT_AGE:

        dp_filename = os.path.join(dp_dir,str(user.user_id)+".gz")
        ptb_filename = os.path.join(ptb_dir,str(user.user_id)+".txt.gz")

        if not os.path.exists(dp_filename) or not os.path.exists(ptb_filename):
            return ['no_dp_ptb',[user.user_id,os.path.exists(dp_filename),os.path.exists(ptb_filename)]]

        penntreebank = {x[0] : x[1:] for x in read_grouped_by_newline_file(ptb_filename)}
        dependency_parse =  read_grouped_by_newline_file(dp_filename)

        tweet_set = [(i,t) for i,t in enumerate(user.tweets) if t.retweeted is None and\
                       len(t.urls) == 0 and 'http:' not in t.text and\
                       langid.classify(t.text)[0] == 'en']

        # non english speaker or spam
        if len(tweet_set) < 40:
            return ['notweets',user.user_id]


        data_to_return = []
        for twit_it, tweet in tweet_set:

            data_for_tweet = []

            ptb_for_tweet = penntreebank[str(tweet.id)]
            dp_for_tweet = dependency_parse[twit_it]

            if ptb_for_tweet[0].split("\t")[2] != DependencyParseObject(dp_for_tweet[0]).text:
                print 'ahhhhh, weird stuff'
                continue

            for i, p in enumerate(dp_for_tweet):
                d = DependencyParseObject(tsn([p,tweet.id,user.user_id,tweet.created_at.strftime("%m-%d-%y")],newline=False))
                # get java features
                spl_java = ptb_for_tweet[i].split("\t")
                java_id, penn_pos_tag,word = spl_java[:3]
                java_features = '' if len(spl_java) == 3 else spl_java[3]
                d.features += [x for x in java_features.split("|") if x != '']
                d.features.append("penn_treebank_pos="+penn_pos_tag)
                data_for_tweet.append(d)
            data_to_return.append(data_for_tweet)

        return ['success', [user.user_id,data_to_return]]
    else:
        return ['baduser',user.user_id]


#,all_dictionaries,ark_clusters,sets,names,orig_feature_names,predict_model, word_vector_model
def run_prediction(json_file_name):
    try:
        err_code, data = gen_conll_file(json_file_name,PTB_DIR,DP_DIR)
        if err_code == 'success':
            pass
        else:
            return err_code, data
        uid, parse = data
        pub_conll, dict_for_filter = get_all_features("",all_dictionaries,ark_clusters,sets, names, parse=parse)

        labels, features, obj_inds,\
        word_list, head_list, word_minus_one_list,\
        last_entity_word_list = configure_features_for_wordvectors_and_remove_twitterner(pub_conll)

        cv = CountVectorizer(tokenizer=lambda x: x.split("|"),vocabulary=orig_feature_names)
        X = cv.fit_transform(features)

        w_vec = get_vector_rep_from_wordlist(word_list, word_vector_model, 50,True)
        head_vec = get_vector_rep_from_wordlist(head_list, word_vector_model, 50,True)
        last_vec = get_vector_rep_from_wordlist(last_entity_word_list, word_vector_model,50,True)

        test_inds,a,  stopword_test_inds, b = get_train_test_inds_w_filter([],
                                                                           dict_for_filter,
                                                                           obj_inds)

        y = np.array(labels)
        D = np.concatenate((X.todense(),w_vec,head_vec,last_vec),axis=1)

        predicted_prob = predict_model.predict_proba(D[test_inds,:])

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
            y = np.concatenate((y[test_inds],np.array([0]*extra_tn),np.array([1]*extra_fn)),axis=0)
            predicted_prob = np.concatenate((predicted_prob,[[1,0]]*(extra_tn+extra_fn)),axis=0)
            test_inds = test_inds + stopword_test_inds_0 + stopword_test_inds_1


        pred_labs = defaultdict(dict)
        for i in range(len(y)):
            obj = obj_inds[test_inds[i]]
            if predicted_prob[i,1] >= .5:
                pred_labs[obj.tweet_id][obj.id] = "Identity"
            else:
                pred_labs[obj.tweet_id][obj.id] = "O"

        final_out_filename = os.path.join(OUTPUT_DIR,str(uid)+".txt.gz")
        test_data = {x[0].tweet_id : x for x in parse}
        outfil = gzip.open(final_out_filename, "wb")
        for k, row in test_data.items():
            i = 1
            tweet_has_identity = False
            tweet = []
            for x in row:
                lab = pred_labs[k][i]
                if lab != 'O':
                    tweet_has_identity = True
                tweet.append(x.get_conll_form() + "\t" + lab)
                i += 1
            if tweet_has_identity:
                outfil.write(("\n".join(tweet) +"\n\n").encode("utf8"))

        outfil.close()
        return ['success', final_out_filename]
    except:
        print 'UNKNOWN ERROR: ', json_file_name
        return ['no_dp_ptb',False,False]




mkdir_no_err(OUTPUT_DIR)

users_to_ignore = open("results/u_ignore.txt","w")
users_no_tweets = open("results/u_notweets.txt","w")
users_need_dp = open("results/u_needdp.txt","w")
users_need_ptb = open("results/u_need_ptb.txt","w")


word_vector_model, all_dictionaries, ark_clusters, sets, names = get_init_data(
                                                                    'gensim_model/glove_twitter_50_raw_model.txt.gz',
                                                                   "processed_data/50mpaths2",
                                                                   "dictionaries/*/*",
                                                                   BOOTSTRAPPED_DICTIONARY_LOCATION)
CONLL_FILE = "processed_data/all_conll_pub_and_nonpub.txt"
features_from_conll_file, dict_for_filter = get_all_features(CONLL_FILE,
                                                             all_dictionaries,
                                                             ark_clusters,sets,names)

cutoff_param = .0005
output, models, preds = run_all_on_test_ids(0, [], word_vector_model,
                                            features_from_conll_file,
                                            dict_for_filter,
                                            eval_params = [.5],
                                            cutoff_params=[cutoff_param],
                                            use_filtered_params=[True],
                                            datasets_to_use = ['full'],
                                            regularization_params = [.58])

predict_model = models[0]

labels, features, obj_inds,\
word_list, head_word_list,word_minus_one_list,\
last_entity_word_list = configure_features_for_wordvectors_and_remove_twitterner(features_from_conll_file)

count_vec = CountVectorizer(tokenizer=lambda x: x.split("|"),min_df=cutoff_param)
count_vec.fit_transform(features)
orig_feature_names = count_vec.get_feature_names()


pool = Pool(processes=int(3))
results = pool.map(run_prediction,glob(os.path.join(BASE_DATA_DIR,"json/*")))


for err_code, data in results:
#for f in glob(os.path.join(BASE_DATA_DIR,"json/*"))[:4]:
#    err_code, data = run_prediction(f)
    if err_code == 'success':
        continue
    elif err_code == 'baduser':
        users_to_ignore.write(str(data)+"\n")
    elif err_code =='notweets':
        users_no_tweets.write(str(data)+"\n")
    elif err_code == 'no_dp_ptb':
        uid, has_dp, has_ptb = data
        if not has_dp:
            users_need_dp.write(str(uid)+"\n")
        if not has_ptb:
            users_need_ptb.write(str(uid) + "\n")

users_to_ignore.close()
users_no_tweets.close()
users_need_dp.close()
users_need_ptb.close()

