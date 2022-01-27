#!/usr/bin/env python
# coding: utf-8

# In[1]:


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import date

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import sqlite3 as lite
import time
import requests
import re
import math
import datetime
import random
import os

# 3cltn
class Three_cltn:
    
    def __init__(self, database, page, mode):
        
        self.urls = []
        self.page = page
        self.mode = mode
        
        self.conn = lite.connect(database, check_same_thread=False)
        
        df = pd.DataFrame(columns = ['title', 'url', 'content', 'cvss'])
        df.to_sql(name = "TCLTN", con = self.conn, if_exists = 'append', index = False)
        
        # getting all urls in database "crawled_data_consolidation.db", for not fetching duplicate data
        self.cdc_conn = lite.connect(fr"{os.getcwd()}\databases\crawled_data_consolidation.db", check_same_thread=False)
        self.db_url = pd.read_sql_query("SELECT url FROM TCLTN", self.cdc_conn)
        
        # for latest data fetching(mode 0)
        if self.mode == 0:
            
            # dynamic web crawling setting
            options = Options()
            
            # avoiding pop-up window to interfere web crawling
            options.add_argument("--disable-notifications")
            
            # produce fake user to avoid web crawling detection
            options.add_argument(f"user-agent={UserAgent().random}")
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            chrome = webdriver.Chrome('./chromedriver', options = options)
            chrome.get("https://3c.ltn.com.tw/list/212")

            # getting the current height of scroll pane
            height = chrome.execute_script("return document.body.scrollHeight")

            not_bottom = True
            while not_bottom:

                # roll the scroll pane to bottom
                chrome.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                # getting new height of the scroll pane
                new = chrome.execute_script("return document.body.scrollHeight")
                
                # if the height not changing, meaning it is the true bottom of the scroll pane
                if new > height:
                    height = new
                else:
                    break

            soup = BeautifulSoup(chrome.page_source, "html.parser")
            chrome.close()
            chrome.quit()
            list_box = soup.find("ul", class_ = "list_box listpage_news boxTitle")
            li_tag = list_box.find_all("li")

            url = "https://3c.ltn.com.tw/"
            counter = 0
            for tag in li_tag:
                a = tag.find("a").get("href")
                if counter < 20:
                    self.urls.append(url + a)
                else:
                    self.urls.append(a)
                counter = counter + 1
                
        # for specific page content fetching(mode 2)
        elif self.mode == 2:
            if self.db_url.T.iloc[0].astype(str).str.count(self.page).sum() == 0:
                print(self.page)
                agent = UserAgent()
                r = requests.get(self.page, headers = {"user-agent" : agent.random})
                print(f"Status Code: {r.status_code}")
                soup = BeautifulSoup(r.text, "html.parser")
            
                box = soup.find("div", class_ = "whitecon borderline boxTitle boxText")
                title = box.find("h1").text
                content = box.find("div", class_ = "text").text.strip()
                
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

                df = pd.DataFrame([[title, self.page, content, cvss_score]], columns = ['title', 'url', 'content', 'cvss'])
                df.to_sql(name = "TCLTN", con = self.conn, if_exists = 'append', index = False)
                df.to_sql(name = "TCLTN", con = self.cdc_conn, if_exists = 'append', index = False)
                self.db_url = pd.read_sql_query("SELECT url FROM TCLTN", self.cdc_conn)

    def data_fetching_storing(self):
        self.limit = int(self.page)
        agent = UserAgent()
        counter = 1
        if self.limit == -1:
            self.limit = len(self.urls)
        for url in self.urls[:self.limit]:
            if self.db_url.T.iloc[0].astype(str).str.count(url).sum() == 0:
                print(f"\nGetting article {counter}..")
                print(url)
                r = requests.get(url, headers = {"user-agent" : agent.random})
                print(f"Status Code: {r.status_code}")
                soup = BeautifulSoup(r.text, "html.parser")

                # three times of chances for retrying web data fetching
                retry = 3
                while retry > 0:
                    if retry != 3:
                        soup = BeautifulSoup(r.text, "html.parser")
                    try:
                        box = soup.find("div", class_ = "whitecon borderline boxTitle boxText")
                        title = box.find("h1").text
                        content = box.find("div", class_ = "text").text.strip()
                        
                        # dealing with some unnecessary string
                        drop = content.replace("請繼續往下閱讀...", "")
                        want = drop.find("你可能也想看")
                        if want != -1:
                            content = drop[:want]
                        elif drop.find("《你可能還想看》") != -1:
                            content = drop[:drop.find("《你可能還想看》")]
                        else:
                            nocacha = drop.find("不用抽")
                            content = drop[:nocacha]
                            
                        sop = re.finditer("（圖", content)
                        eop = re.finditer("）", content)
                        adjust = 0
                        for s, e in zip(sop, eop):
                            drop = content[:s.start() - adjust] + content[e.end() - adjust:]
                            adjust = e.end() - s.start()
                            content = drop
                        cvss = re.finditer("CVSS", content)
                        cvss_score = 0
                        not_empty = any(True for _ in cvss)
                        if not_empty:
                            cvss = re.finditer("CVSS", content)
                            for i in cvss:
                                temp = content[i.start() : i.start() + 50]
                                try:
                                    new_cvss_score = 0
                                    new_cvss_score_list = re.finditer("[0-9].[0-9]", temp)
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
            
                        df = pd.DataFrame([[title, url, content, cvss_score]], columns = ['title', 'url', 'content', 'cvss'])
                        df.to_sql(name = "TCLTN", con = self.conn, if_exists = 'append', index = False)
                        df.to_sql(name = "TCLTN", con = self.cdc_conn, if_exists = 'append', index = False)
                        self.db_url = pd.read_sql_query("SELECT url FROM TCLTN", self.cdc_conn)
                        break
                    except:
                        print(f"Error raised in content fetching_storing. Retrying({retry})..")
                        retry = retry - 1
                        if retry == 0:
                            print("Content fetching failed, try next content..")

                counter = counter + 1

                time.sleep(random.uniform(2, 5))
        print("Thread over.")

