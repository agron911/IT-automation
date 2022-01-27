#!/usr/bin/env python
# coding: utf-8

# In[1]:


from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from datetime import date

import requests
import sqlite3 as lite
import pandas as pd
import numpy as np
import threading
import queue
import os
import time
import random
import re

class Worker(threading.Thread):
    counter = 1
    
    # getting all urls in database "crawled_data_consolidation.db", for not fetching duplicate data
    db_url = pd.DataFrame()
    
    def __init__(self, queue, lock, slock, conn):
        threading.Thread.__init__(self)
        self.queue = queue
        self.lock = lock
        self.slock = slock
        self.conn = conn
        self.cdc_conn = lite.connect(fr"{os.getcwd()}\databases\crawled_data_consolidation.db", check_same_thread=False)
        Worker.db_url = pd.read_sql_query("SELECT url FROM THEHACKERNEWS", self.cdc_conn)
        
    def run(self):
        df = pd.DataFrame(columns = ["title", "url", "content", "cvss"])
        
        # while still some works in queue
        while self.queue.qsize() > 0:
            url = self.queue.get()
            
            if Worker.db_url.T.iloc[0].astype(str).str.count(url).sum() == 0:
                
                # the lock for displaying current status
                self.lock.acquire()
                count = Worker.counter
                print(f"\nGetting article {Worker.counter}..")
                Worker.counter = Worker.counter + 1
                print(url)
                self.lock.release()

                headers = {
                    'user-agent' : UserAgent().random
                }
            
                r = requests.get(url)
                soup = BeautifulSoup(r.text, 'lxml')
                title = soup.find("h1", {"class" : "story-title"}).text
                body = soup.find("div", {"class" : "articlebody clear cf"}).text
                drop = body.find("Found this article interesting?")
                content = body[:drop].strip()
                
                # cvss detection
                cvss = re.finditer("CVSS", content)
                cvss_score = 0
                not_empty = any(True for _ in cvss)
                if not_empty:
                    cvss = re.finditer("CVSS", content)
                    for i in cvss:
                        temp = content[i.start() : i.start() + 50]
                        try:
                            new_cvss_score = 0
                            new_cvss_score_list = re.finditer("\d+\.\d+", temp)
                            for j in new_cvss_score_list:
                                new_cvss_score = float(temp[j.start():j.end()])
                                if new_cvss_score == 3.0:
                                    check = re.finditer("3.0", temp)
                                    for j in check:
                                        position = j.start()
                                    if position - i.end() <= 2:
                                        new_cvss_score = 0
                                        continue
                                break
                        except:
                            new_cvss_score = 0
                        if new_cvss_score > cvss_score:
                            cvss_score = new_cvss_score

                self.slock.acquire()
                df = pd.DataFrame([[title, url, content, cvss_score]], columns = ['title', 'url', 'content', 'cvss'])
                df.to_sql(name = "THEHACKERNEWS", con = self.conn, if_exists = "append", index = False)
                df.to_sql(name = "THEHACKERNEWS", con = self.cdc_conn, if_exists = "append", index = False)
                Worker.db_url = pd.read_sql_query("SELECT url FROM THEHACKERNEWS", self.cdc_conn)
                self.slock.release()
                time.sleep(random.randint(3, 6))

class The_Hacker_News():
    
    def page_list(self, current_url):
        
        headers = {
            'user-agent' : UserAgent().random
        }
        
        r = requests.get(current_url)
        soup = BeautifulSoup(r.text, "lxml")
        post = soup.find_all("div", {"class" : "body-post clear"})
        for i in post:
            self.queue.put(i.find("a").get("href"))
            
        next_page = soup.find("a", class_ = "blog-pager-older-link-mobile").get("href")
        self.current_url = next_page
    
    def __init__(self, database, page, mode):
        self.page = page
        self.mode = mode
        self.urls = []
        self.queue = queue.Queue()
        lock = threading.Lock()
        slock = threading.Lock()
        
        self.conn = lite.connect(database, check_same_thread=False)
        
        df = pd.DataFrame(columns = ['title', 'url', 'content', 'cvss'])
        df.to_sql(name = "THEHACKERNEWS", con = self.conn, if_exists = 'append', index = False)
        
        if self.mode == 0:
            n_page = int(self.page)
            self.current_url = "https://thehackernews.com/"
            for i in range(n_page):
                self.page_list(self.current_url)
                
        elif self.mode == 1:
            self.page_list(self.page)
        
        elif self.mode == 2:
            self.queue.put(self.page)
            
        worker1 = Worker(self.queue, lock, slock, self.conn)
        worker2 = Worker(self.queue, lock, slock, self.conn)
        worker3 = Worker(self.queue, lock, slock, self.conn)
        worker4 = Worker(self.queue, lock, slock, self.conn)
        
        worker1.start()
        worker2.start()
        worker3.start()
        worker4.start()
        
        worker1.join()
        worker2.join()
        worker3.join()
        worker4.join()
        Worker.counter = 1
        
        print("Thread over.")

