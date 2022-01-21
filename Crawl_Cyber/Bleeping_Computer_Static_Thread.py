#!/usr/bin/env python
# coding: utf-8

# In[1]:


from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import date

import threading
import sqlite3 as lite
import requests
import pandas as pd
import queue
import random
import time
import os
import re

urls = []

class Worker(threading.Thread):
    
    counter = 1
    # getting all urls in database "crawled_data_consolidation.db", for not fetching duplicate data
    db_url = pd.DataFrame()
    
    def __init__(self, queue, lock, conn, slock):
        threading.Thread.__init__(self)
        self.queue = queue
        self.lock = lock
        self.conn = conn
        self.slock = slock
        self.cdc_conn = lite.connect(fr"{os.getcwd()}\databases\crawled_data_consolidation.db", check_same_thread=False)
        Worker.db_url = pd.read_sql_query("SELECT url FROM BLEEPINGCOMPUTER", self.cdc_conn)
        
    def crawl(self, url):
        
        # produce fake user to avoid web crawling detection
        headers = {
            'user-agent' : UserAgent().random
        }
        
        try:
            r = requests.get(url, headers = headers)
            
            # sometimes the web server return status code 503
            # where status code 200 is the only one we want
            if r.status_code == 200:
                self.soup = BeautifulSoup(r.text, 'html.parser')
            else:
                print(f"Status Code: {r.status_code}")
                self.soup = ""
        except:
            print("Error raised in web crawing.")
            self.soup = ""
        
    def run(self):
        df = pd.DataFrame(columns = ['title', 'url', 'content', 'cvss'])
        
        # while still some works in queue
        while self.queue.qsize() > 0:
            url = self.queue.get()
            
            # duplicate url detection
            if Worker.db_url.T.iloc[0].astype(str).str.count(url).sum() == 0:
                
                # the lock for displaying current status
                self.lock.acquire()
                count = Worker.counter
                print(f"\nGetting article {Worker.counter}..")
                Worker.counter = Worker.counter + 1
                print(url)
                self.lock.release()

                self.crawl(url)

                # three times of chances for retrying web data fetching
                retry = 3
                while retry > 0:
                    if retry != 3:
                        self.crawl(url)
                    try:
                        title = self.soup.find("div", class_ = "article_section").find("h1").string
                        body = self.soup.find("div", class_ = "articleBody")
                        drop = body.text.find("Related Articles:")
                        content = body.text[:drop].strip()
                        
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

                        # lock for database syncronization
                        self.slock.acquire()
                        df = pd.DataFrame([[title, url, content, cvss_score]], columns = ['title', 'url', 'content', 'cvss'])
                        df.to_sql(name = "BLEEPINGCOMPUTER", con = self.conn, if_exists = 'append', index = False)
                        df.to_sql(name = "BLEEPINGCOMPUTER", con = self.cdc_conn, if_exists = 'append', index = False)
                        Worker.db_url = pd.read_sql_query("SELECT url FROM BLEEPINGCOMPUTER", self.cdc_conn)
                        self.slock.release()
                        break

                    except:
                        print(f"\nError raised in {count} content fetching_storing. Retrying({retry})..")
                        retry = retry - 1
                        if retry == 0:
                            print("Content fetching failed, try next content..")
                time.sleep(random.randint(2, 8))

# such as class "Worker" above but for page fetching
class Page_Worker(threading.Thread):
    
    counter = 1
    
    def crawl(self, url):
        headers = {
            'user-agent' : UserAgent().random
        }
        try:
            r = requests.get(url, headers = headers)
            if r.status_code == 200:
                self.soup = BeautifulSoup(r.text, 'html.parser')
            else:
                print(f"Status Code: {r.status_code}")
                self.soup = ""
            
        except:
            print("Error raised in web page crawing.")
            self.soup = ""
    
    def __init__(self, queue, lock):
        threading.Thread.__init__(self)
        self.queue = queue
        self.lock = lock
        
    def run(self):
        while self.queue.qsize() > 0:
            url = self.queue.get()
            
            self.lock.acquire()
            count = Page_Worker.counter
            print(f"\nGettig url page lists {Page_Worker.counter}..")
            Page_Worker.counter = Page_Worker.counter + 1
            print(url)
            self.lock.release()
            
            self.crawl(url)
            
            retry = 3
            while retry > 0:
                if retry != 3:
                    self.crawl(url)
                try:
                    bc_latest = self.soup.find_all("div", class_ = "bc_latest_news_text")
                    for title in bc_latest:
                        a = title.find("h4").find("a")
                        urls.append(a.get('href'))
                    break
                    
                except:
                    print(f"\nError raised in {count} page list fetching. Retrying({retry})..")
                    retry = retry - 1
                    if retry == 0:
                        print("Page list fetching failed, try next page..")
            
    
            
# bleeping_computer
class Bleeping_Computer:
    
    def crawl(self, url):
        headers = {
            'user-agent' : UserAgent().random
        }
        try:
            r = requests.get(url, headers = headers)
            print(f"Status Code: {r.status_code}")
            self.soup = BeautifulSoup(r.text, 'html.parser')
        except:
            print("Error raised in web crawing.")
            return -1
    
    def __init__(self, database, page, mode):
        
        global urls
        urls = []
        
        self.soup = ""
        self.urls = []
        self.page_queue = queue.Queue()
        self.page = page
        self.mode = mode
        
        self.conn = lite.connect(database, check_same_thread=False)
        
        # empty dataframe for building a database
        df = pd.DataFrame(columns = ['title', 'url', 'content', 'cvss'])
        df.to_sql(name = "BLEEPINGCOMPUTER", con = self.conn, if_exists = 'append', index = False)    

        # page control
        # for latest page fetching(mode 0)
        if self.mode == 0:
            n_page = int(self.page)
            for i in range(int(n_page) + 1):
                if i == 1:
                    continue
                url = "https://www.bleepingcomputer.com/" + f"page/{i}/"
                self.page_queue.put(url)

            plock = threading.Lock()

            # multi-thread control
            pworker1 = Page_Worker(self.page_queue, plock)
            pworker2 = Page_Worker(self.page_queue, plock)
            pworker3 = Page_Worker(self.page_queue, plock)
            pworker4 = Page_Worker(self.page_queue, plock)

            pworker1.start()
            pworker2.start()
            pworker3.start()
            pworker4.start()

            pworker1.join()
            pworker2.join()
            pworker3.join()
            pworker4.join()

            print("Page Thread over")
            self.urls = urls
            
        # for specific page list fetching(mode 1)
        elif self.mode == 1:
            self.page_queue.put(self.page)
            plock = threading.Lock()
            pworker1 = Page_Worker(self.page_queue, plock)
            pworker1.start()
            pworker1.join()
            self.urls = urls
        
        # for specific page content(mode 2)
        elif self.mode == 2:
            urls.append(self.page)
            self.urls = urls
            
        Page_Worker.counter = 1
                        
    # data crawling
    def data_fetching_storing(self):
        
        self.queue = queue.Queue()
        for url in self.urls:
            self.queue.put(url)
        
        lock = threading.Lock()
        slock = threading.Lock()
        
        working = len(self.urls)
        
        # multi-thread control
        worker1 = Worker(self.queue, lock, self.conn, slock)
        worker2 = Worker(self.queue, lock, self.conn, slock)
        worker3 = Worker(self.queue, lock, self.conn, slock)
        worker4 = Worker(self.queue, lock, self.conn, slock)
        worker5 = Worker(self.queue, lock, self.conn, slock)
        worker6 = Worker(self.queue, lock, self.conn, slock)

        worker1.start()
        worker2.start()
        worker3.start()
        worker4.start()
        worker5.start()
        worker6.start()

        worker1.join()
        worker2.join()
        worker3.join()
        worker4.join()
        worker5.join()
        worker6.join()
            
        Worker.counter = 1
        self.urls = []
        
        print("Thread over.")

