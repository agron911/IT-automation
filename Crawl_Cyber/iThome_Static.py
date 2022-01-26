#!/usr/bin/env python
# coding: utf-8

# In[1]:


from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import date

import requests
import pandas as pd
import sqlite3 as lite
import threading
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
        Worker.db_url = pd.read_sql_query("SELECT url FROM ITHOME", self.cdc_conn)
        
    def crawl(self, url):
        
        # produce fake user to avoid web crawling detection
        headers = {
            'user-agent' : UserAgent().random
        }
        try:
            r = requests.get(url, headers = headers)
            self.soup = BeautifulSoup(r.text, 'html.parser')
        except:
            print("Error raised in web crawing.")
            self.soup = ""
        
    def run(self):
        df = pd.DataFrame(columns = ["title", "url", "content", "cvss"])
        
        # while still some works in queue
        while self.queue.qsize() > 0:
            url = self.queue.get()
            
            # duplicate detection
            if Worker.db_url.T.iloc[0].astype(str).str.count(url).sum() == 0:
                
                # the lock for displaying current status
                self.lock.acquire()
                count = Worker.counter
                print(f"\nGetting article {Worker.counter}..")
                Worker.counter = Worker.counter + 1
                print(url)
                self.lock.release()

                self.crawl(url)

                # three times of channces for retrying web data fetching
                retry = 3
                while retry > 0:
                    if retry != 3:
                        self.crawl(url)
                    try:
                        title = self.soup.find("h1", class_ = "page-header").text
                        section = self.soup.find("div", class_ = "field field-name-body field-type-text-with-summary field-label-hidden")
                        content = section.text
                        
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

                        # lock for database synchonization
                        self.slock.acquire()
                        df = pd.DataFrame([[title, url, content, cvss_score]], columns = ['title', 'url', 'content', 'cvss'])
                        df.to_sql(name = "ITHOME", con = self.conn, if_exists = 'append', index = False)
                        df.to_sql(name = "ITHOME", con = self.cdc_conn, if_exists = 'append', index = False)
                        Worker.db_url = pd.read_sql_query("SELECT url FROM ITHOME", self.cdc_conn)
                        self.slock.release()
                        break

                    except:
                        print(f"Error raised in {count} content fetching_storing. Retrying({retry})..")
                        retry = retry - 1
                        if retry == 0:
                            print("Content fetching failed, try next content..")
                time.sleep(random.randint(2, 5))

# iThome
class iThome:
    
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
            self.soup = ""
        
    def __init__(self, database, page, mode):
        
        self.soup = ""
        self.urls = []
        self.page = page
        self.mode = mode
        urls = []
        
        self.conn = lite.connect(database, check_same_thread=False)
        
        df = pd.DataFrame(columns = ["title", "url", "content", "cvss"])
        df.to_sql(name = "ITHOME", con = self.conn, if_exists = 'append', index = False)

        # for latest records fetching(mode 0)
        if self.mode == 0:
            
            # page control, three part: headline, weekreport, normal
            once_flag = True
            for i in range(int(self.page)):
                url = "https://www.ithome.com.tw/security" + f"?page={i}"
                print(f"\nGettig url page lists {i}..")
                print(url)
                self.crawl(url)
                retry = 3
                while retry > 0:
                    if retry != 3:
                        self.crawl(url)
                    try:
                        items = self.soup.find_all("div", class_ = "item")

                        if once_flag:
                            # headline, needs be crawled only in first time
                            head = self.soup.find("section", class_ = "block block-views clearfix")
                            a = head.find_all("a")
                            for url in a:
                                urls.append("https://www.ithome.com.tw" + url.get("href"))

                            # weekreport, needs be crawled only in first time
                            for item in items[:3]:
                                try:
                                    a = item.find("p", class_ = "title").find("a")
                                    urls.append("https://www.ithome.com.tw" + a.get("href"))
                                except:
                                    continue

                        # normal part, every page needs be crawled
                        for item in items[3:]:
                            try:
                                a = item.find("p", class_ = "title").find("a")
                                urls.append("https://www.ithome.com.tw" + a.get("href"))
                            except:
                                continue
                        once_flag = False
                        break
                    except:
                        print(f"Error raised in page list fetching. Retrying({retry})..")
                        retry = retry - 1
                        if retry == 0:
                            print("Page list fetching failed, try next page..")
                            
            # drop duplicate data
            urls = list(dict.fromkeys(urls))
            self.urls = urls
            
        # for specific page list fetching(mode 1)
        elif self.mode == 1:
            url = self.page
            print(url)
            self.crawl(url)
            retry = 3
            while retry > 0:
                if retry != 3:
                    self.crawl(url)
                try:
                    items = self.soup.find_all("div", class_ = "item")
                    
                    # headline
                    head = self.soup.find("section", class_ = "block block-views clearfix")
                    a = head.find_all("a")
                    for url in a:
                        urls.append("https://www.ithome.com.tw" + url.get("href"))
                    
                    # weekly
                    for item in items[:3]:
                        try:
                            a = item.find("p", class_ = "title").find("a")
                            urls.append("https://www.ithome.com.tw" + a.get("href"))
                        except:
                            continue
                    
                    # normal
                    for item in items[3:]:
                        try:
                            a = item.find("p", class_ = "title").find("a")
                            urls.append("https://www.ithome.com.tw" + a.get("href"))
                        except:
                            continue
                    urls = list(dict.fromkeys(urls))
                    self.urls = urls
                    break
                            
                except:
                    print(f"Error raised in page list fetching. Retrying({retry})..")
                    retry = retry - 1
                    if retry == 0:
                        print("Page list fetching failed.")
            
        elif self.mode == 2:
            urls.append(self.page)
            self.urls = urls
            
    # data crawling and database storing
    def data_fetching_storing(self):
        
        self.queue = queue.Queue()
        for url in self.urls:
            self.queue.put(url)
        
        lock = threading.Lock()
        slock = threading.Lock()
        
        # multi-thread control
        worker1 = Worker(self.queue, lock, self.conn, slock)
        worker2 = Worker(self.queue, lock, self.conn, slock)
        worker3 = Worker(self.queue, lock, self.conn, slock)
        worker4 = Worker(self.queue, lock, self.conn, slock)
        worker5 = Worker(self.queue, lock, self.conn, slock)
        worker6 = Worker(self.queue, lock, self.conn, slock)
        worker7 = Worker(self.queue, lock, self.conn, slock)
        worker8 = Worker(self.queue, lock, self.conn, slock)
        
        worker1.start()
        worker2.start()
        worker3.start()
        worker4.start()
        worker5.start()
        worker6.start()
        worker7.start()
        worker8.start()
        
        worker1.join()
        worker2.join()
        worker3.join()
        worker4.join()
        worker5.join()
        worker6.join()
        worker7.join()
        worker8.join()
        Worker.counter = 1
        
        self.urls = []
        
        print("Thread over.")

