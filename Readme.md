# Introduction

This is the public code repository for the paper submitted to WWW.

The repository contains code and data necessary to reproduce results from the paper


# Requirements

- Apache Spark & pyspark s(for the case study)
- The ```twitter_dm``` library, which you can find at https://github.com/kennyjoseph/twitter_dm and then install on your machine

# Installation

Run ```install.sh``` from this directory to pull down the GloVe and Brown Cluster data and to install a few python libraries. NOTE that it will install all nltk data files and pip install numpy, scikit-learn and pandas


# Overview

The ```python``` directory contains almost all code written for the model, save for the generation of the Penn Treebank POS tags and the rule-based features. The files are ordered numerically based on the order in which they were run to generate results (e.g. ```1_*_.py``` was run first, ```2_*.py``` was run second, etc).   The ```r``` directory is an R Project file (for RStudio) that simply has the one R file we used to generate the plots in the article. Finally, the ```java``` folder has a gradle project for how we ran the rule-based stuff to generate the bootstrapped dictionary. We also used this code to generate PTB POS tags and the rule-based model features.

While you're welcome to explore the full code base and re-run everything, we have provided processed data that allows you to simply replicate the results obtained:

- ```10_run_baselines.py``` will replicate results from the baseline models
- ```11_run_param_tuning.py``` will rerun the parameter tuning
- ```12_run_final_model_on_pub_data.py``` will run the final model on the validation set
- ```13_run_model_on_case_study_data.py``` will run the model on case study data - this code can be modified to run the model on a directory of gzipped (or uncompressed) .json files where each file contains the tweet stream for a particular user
- ```14_case_study_analysis.ipynb``` will replicate all results in our case study. Note that you need Spark to do so, and further that it will take a while if this machine isn't big. We ran it on a machine with 64 virtual cores and 512 GB of RAM

# Notes

The one thing that you will not be able to explore is the raw json for any of the tweets we use, as Twitter's API prohibits us from releasing this data. The directory ```pickled_random_for_labeling``` is thus not included.