# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 05:30:34 2020

@author: johnv
"""

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer

import pickle

picklefile = open('final_df_bag','rb')
df = pickle.load(picklefile)
picklefile.close()

count = CountVectorizer()
count_matrix = count.fit_transform(df['keywords'])
cosine_sim = cosine_similarity(count_matrix, count_matrix)
#print(cosine_sim)

picklefile = open('co_sim','wb')
pickle.dump(cosine_sim, picklefile)