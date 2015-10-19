#!/bin/bash


pip install sklearn
pip install pandas
pip instally numpy
python -m nltk.downloader all


cd python
mkdir gensim_model
cd gensim_model
wget http://www-nlp.stanford.edu/data/glove.twitter.27B.50d.txt.gz

cd ../processed_data/
wget http://www.ark.cs.cmu.edu/TweetNLP/clusters/50mpaths2

cd ../..