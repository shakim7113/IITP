# -*- coding: utf-8 -*-
"""
Created on Fri Nov 19 16:16:58 2021

@author: tmlab
"""


if __name__ == '__main__':
    
    import os
    import sys
    import pickle
    from copy import copy
    
    directory = os.path.dirname(os.path.abspath(__file__))
    directory = directory.replace("\\", "/") # window|
    os.chdir(directory)    
    
    
    #%% phase 1. data laod
    
    import data_preprocessing
    with open( directory+ '/input/DT_211118.pkl', 'rb') as fr :
        data = pickle.load(fr)
    
    data_sample = copy(data)
    data_sample = data_preprocessing.initialize(data_sample)
    data_sample = data_preprocessing.filter_by_year(data_sample)
    data_sample = data_preprocessing.filter_by_textsize(data_sample)
    data_sample = data_preprocessing.preprocess_text(data_sample, directory)
    
    
    #%% phase 2. embedding
    
    import embedding
    from gensim.corpora import Dictionary
    
    # CPC embedding    
    with open( directory+ '/input/CPC_definition.pkl', 'rb') as fr :
        CPC_definition = pickle.load(fr)

    CPC_dict =  embedding.generate_CPC_dict(data_sample)
    CPC_dict_filtered = embedding.filter_CPC_dict(data_sample, CPC_dict,  CPC_definition)
    encoded_CPC = embedding.CPC_embedding(CPC_definition, CPC_dict_filtered)
    
    texts = data_sample['TAC_keyword']
    
    # document embedding, ready to LDA
    keyword_dct = Dictionary(texts)
    keyword_dct.filter_extremes(no_below = 10, no_above=0.1)
    keyword_list = keyword_dct.token2id.keys()
    
    corpus = [keyword_dct.doc2bow(text) for text in texts]
    # encoded_keyword = embedding.keyword_embedding(keyword_list)
    
    docs = data_sample['TAC_keyword'].apply(lambda x : " ".join(x))
    encoded_docs = embedding.docs_embedding(docs)
    
    
    #%% phase 3. LDA tunning and modelling
    
    import LDA
    import pandas as pd
    
    if os.path.isfile(directory + '/lda_tuning_results.csv') :
        tunning_results = pd.read_csv(directory + '/lda_tuning_results.csv')
    else :
        tunning_results = LDA.tunning(texts, keyword_dct, corpus)
        tunning_results.to_csv(directory + '/lda_tuning_results.csv', index=False)
    
    lda_model = LDA.model_by_tunning(tunning_results, corpus, keyword_dct)
    
    #%% phase 4. 
    import LDA
    
    topic_doc_df = LDA.get_topic_doc(lda_model, corpus)
    
    #%% 
    import numpy as np 
    
    x = np.linalg.solve(encoded_docs, topic_doc_df)
    
    
    #%% phase 3. genearte sim matrix
    import pandas as pd
    import numpy as np
    import embedding
    
    class_matrix = embedding.get_sim_matrix(CPC_dict_filtered['class_list'], encoded_CPC, encoded_keyword)
    subclass_matrix = embedding.get_sim_matrix(CPC_dict_filtered['subclass_list'], encoded_CPC, encoded_keyword)
    group_matrix = embedding.get_sim_matrix(CPC_dict_filtered['group_list'], encoded_CPC, encoded_keyword)
    
    standard = {}
    standard['class'] = np.percentile(class_matrix, 95)
    standard['subclass'] = np.percentile(subclass_matrix, 95)
    standard['group'] = np.percentile(group_matrix, 95)
    
    class_matrix_ = class_matrix.applymap(lambda x : 1 if x > standard['class'] else 0)
    subclass_matrix_ = subclass_matrix.applymap(lambda x : 1 if x > standard['subclass'] else 0)
    group_matrix_ = group_matrix.applymap(lambda x : 1 if x > standard['group'] else 0)
    
    #%%
    
    import embedding
    
    word_cls_df = pd.DataFrame()
    
    for matrix in [class_matrix_, subclass_matrix_, group_matrix_] :
        DICT = embedding.classify_keyword(matrix)
        word_cls_df = word_cls_df.append(DICT, ignore_index=1)
        
    word_cls_df = word_cls_df.transpose()    
    word_cls_df.columns = ['class', 'subclass' , 'group']
    #%% phase 4. classifying keyword
    
    
    
    
    #%% test
    
    import matplotlib.pyplot as plt
    import numpy as np 
    
    temp = embedding.get_sim_dist(encoded_CPC['G05B'],encoded_keyword)
    
    plt.hist(temp, bins=50)

    plt.axvline(np.percentile(temp, 90), color = 'red')  # Q1
    plt.show()


