#!/usr/bin/env python
# coding: utf-8

# In[1]:


from rank_bm25 import BM25Okapi
from datetime import date
from nltk.corpus import stopwords
from nltk import word_tokenize
from nltk.tokenize import MWETokenizer

import sqlite3 as lite
import pandas as pd
import numpy as np
import pickle
import time
import os
import jieba

class Data_Analyzing():
    
    def __init__(self, database):
        self.conn = lite.connect(database)
        
        # chinese and english handled separately
        self.df_en = pd.DataFrame()
        self.df_ch = pd.DataFrame()
        
        table_list = []
        with self.conn:
            cur = self.conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            table = cur.fetchall()
            for i in table:
                table_list.append(i[0])
        
        # whether each table in the database
        bleep = "BLEEPINGCOMPUTER" in table_list
        it = "ITHOME" in table_list
        tcltn = "TCLTN" in table_list
        thn = "THEHACKERNEWS" in table_list
        micro = "MICROSOFT" in table_list
        
        print("Database Loading..")
        
        if bleep:
            self.bleepingcomputer = pd.read_sql_query("SELECT * FROM BLEEPINGCOMPUTER", self.conn)
            self.df_en = self.df_en.append(self.bleepingcomputer)
            
        if thn:
            self.thn = pd.read_sql_query("SELECT * FROM THEHACKERNEWS", self.conn)
            self.df_en = self.df_en.append(self.thn)
            
        if it:
            self.ithome = pd.read_sql_query("SELECT * FROM ITHOME", self.conn)
            self.df_ch = self.df_ch.append(self.ithome)
        
        if tcltn:
            self.tcltn = pd.read_sql_query("SELECT * FROM TCLTN", self.conn)
            self.df_ch = self.df_ch.append(self.tcltn)
        
        if micro:
            self.microsoft = pd.read_sql_query("SELECT * FROM MICROSOFT", self.conn)
            self.df_ch = self.df_ch.append(self.microsoft)
        
        self.en = False
        self.ch = False
        self.df = pd.DataFrame()
        
        if len(self.df_en) > 0:
            self.en = True
            self.df_en.reset_index(drop = True, inplace = True)
            self.df = self.df.append(self.df_en)
            
            
        if len(self.df_ch) > 0:
            self.ch = True
            self.df_ch.reset_index(drop = True, inplace = True)
            self.df = self.df.append(self.df_ch)
            
        self.df.reset_index(drop = True, inplace = True)
        
        print("Database Loading over.")
        
    def multiword_tokenize(self, text, mwe):
        
        protected_lists = [word_tokenize(word) for word in mwe]
        protected_underscore = ['_'.join(word) for word in protected_lists]
        tokenizer = MWETokenizer(protected_lists)
        tokenized_text = tokenizer.tokenize(word_tokenize(text))
        for i, token in enumerate(tokenized_text):
            if token in protected_underscore:
                tokenized_text[i] = mwe[protected_underscore.index(token)]
        return tokenized_text
        
    def new_model_build(self, storing_path, pickle_name):
        
        token_text = []
        
        keyword = fr"{os.getcwd()}\adjustments\System List.xlsx"
        key_df = pd.read_excel(keyword).replace(np.nan, "", regex = True)
        system = list(key_df.iloc[:, 0])
        version = list(key_df.iloc[:, 1])
        splittable = list(key_df.iloc[:, 2])
        meaningful = list(key_df.iloc[:, 3])
        
        merge = []
        with_ver = [f"{sys.lower()} {str(ver).lower()}".strip() for sys, ver in zip(system, version)]
        with_no_ver = [f"{sys.lower()}".strip() for sys, ver in zip(system, version)]
        with_no_space = ["".join(sys.lower().split()) for sys in system]
        merge.extend(with_ver)
        merge.extend(with_no_ver)
        merge.extend(with_no_space)
        merge.extend([sys.lower() for sys in system])
        merge.extend([str(version[i]).lower() for i in range(len(version)) if meaningful[i] == True])
        temp = []
        for i in range(len(system)):
            if splittable[i] == True:
                temp.extend(system[i].lower().split())
        merge.extend(temp)
        
        merge_list = list(dict.fromkeys(merge))
        
        mwe = [i for i in merge_list if len(i.split()) > 1]
        
        path = os.getcwd() + "\\adjustments"
        with open(fr"{path}\jieba.txt", "w", encoding='utf8') as rec:
            rec.writelines([f"{i}\n" for i in merge_list])
        
        print("Word splitting..",mwe)
        
        # nltk tokenizer
        if self.en:
            text_en = self.df_en["content"].astype(str).str.lower().values
            for content in text_en:
                word_tokens = self.multiword_tokenize(content, mwe)
                removing_stopwords = [word for word in word_tokens if word not in stopwords.words("english")]
                token_text.append(removing_stopwords)
        
        # jieba tokenizer
        if self.ch:
            text_ch = self.df_ch["content"].astype(str).str.lower().values
            path = os.getcwd() + "\\adjustments"
            jieba.load_userdict(fr"{path}\jieba.txt")
            for content in text_ch:
                word_tokens = jieba.lcut(content)
                token_text.append(word_tokens)
        print("Word splitting over.")
               
        
        print("BM25 calculating..")
        
        try:
            bm25 = BM25Okapi(token_text)
            
                       
#             print('+'*100)

            print('token_text',token_text)
            # bm25 = pickle.load(open("name.p", 'rb'))
            pickle.dump(bm25, open(storing_path + "\\" + pickle_name, "wb"))
            self.searchable = True
            
        # if token_text is empty, which means no data in crawled database
        except:
            self.searchable = False
        
        print("BM25 calculating over.")
        
    def search(self, pic, system, version, splittable, meaningful):
               
        bm25 = pickle.load(open(pic, 'rb'))

        query = []

        system, version = str(system).lower(), str(version).lower()
        if system =='windows':
            query.append(f"{system} {version}".strip())
        else:
            query.append(f"{system} {version}".strip())
            query.append("".join(system.split()))
            query.append(system)
            
        
        
        if meaningful:
            query.append(version)

        if splittable:
            query.extend(system.split())

        query = list( dict.fromkeys(query) )
        
        print(f"{query}\n")
        doc_scores = bm25.get_scores(query)
        sbm25 = pd.Series(doc_scores)
        print('sbm25',sbm25)
        self.df["bm25"] = sbm25
        
        self.df.to_csv('df.csv')
       
        self.df = self.df.sort_values(by = ["bm25"], ascending = False)

        self.bm25_df = self.df[self.df["bm25"] > 0].reset_index(drop = True)
        self.bm25_df["cvss"] = self.bm25_df["cvss"].astype(float)
        
        self.cvss_df = self.bm25_df[self.bm25_df["cvss"] > 0].sort_values(by = ["cvss"], ascending = False)
        self.uncvss_df = self.bm25_df[self.bm25_df["cvss"] == 0]
        
        self.out_df = self.cvss_df.append(self.uncvss_df).reset_index(drop = True)

