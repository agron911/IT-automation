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
from selenium.common.exceptions import TimeoutException

import random
import sqlite3 as lite
import pandas as pd
import time
import requests
import re
import math
import datetime
import queue
import threading
import os

class Worker(threading.Thread):
    
    counter = 0
    
    # getting all urls in database "crawled_data_consolidation.db", for not fetching duplicate data
    db_url = pd.DataFrame()
    
    def __init__(self, queue, conn, slock, lock):
        threading.Thread.__init__(self)
        self.queue = queue
        self.conn = conn
        self.slock = slock
        self.lock = lock
        self.cdc_conn = lite.connect(fr"{os.getcwd()}\databases\crawled_data_consolidation.db", check_same_thread=False)
        Worker.db_url = pd.read_sql_query("SELECT url FROM MICROSOFT", self.cdc_conn)
    
    def climb(self, soup, url):
        root = soup.find("div", {"class" : "ms-Grid-row"})
        title = root.find("h1").text
        
        content = soup.find("div", {"data-testid" : "page-vulnerability-detail"}).text
        
        # almost every report in Microsoft_SRC has cvss score
        try:
            cvss = content[content.find("CVSS:3.0") : content.find("Expand all")]
            score = float(re.findall("[0-9.]+", cvss)[1])
        except:
            score = 0
        
        # we pick the records that cvss >= 7
        if score >= 7.0:
            data = soup.find("div", {"data-testid" : "page-vulnerability-detail"})
            subtitle = [i.text for i in data.find_all("h2")]
            h2p = re.finditer("h2", str(content))
            h2l = []
            for i in h2p:
                h2l.append(i.start())
            h2 = [h2l[i] for i in range(0, len(h2l), 2)]
            
            block = []
            for title, position in zip(subtitle, h2):
                block.append([title, position])
                
            content_complete = ""
            for i in range(len(block)):
                if block[i][0] == "致謝" or block[i][0] == "免責聲明" or block[i][0] == "修訂":
                    continue
                else:
                    code = str(content)[block[i][1] - 1: block[i+1][1] - 1]
                    test = BeautifulSoup(code, "lxml")
                    content_complete = content_complete + test.text + "\n"
            load = content_complete.find("已載入")
            if load != -1:
                content_complete = content_complete[:load]
                            
            # lock for database synchronization
            self.slock.acquire()
            df = pd.DataFrame([[title, url, content, score]], columns = ['title', 'url', 'content', 'cvss'])
            df.to_sql(name = "MICROSOFT", con = self.conn, if_exists = 'append', index = False)
            df.to_sql(name = "MICROSOFT", con = self.cdc_conn, if_exists = 'append', index = False)
            Worker.db_url = pd.read_sql_query("SELECT url FROM MICROSOFT", self.cdc_conn)
            self.slock.release()
        
    
    def run(self):
        df = pd.DataFrame(columns = ["title", "url", "content", "cvss"])
        while self.queue.qsize() > 0:
            
            url = self.queue.get()
            
            # the lock for displaying current status
            self.lock.acquire()
            Worker.counter = Worker.counter + 1
            owncounter = Worker.counter
            print(Worker.counter, " ",url)
            self.lock.release()
            
            # dynamic web  crawling setting
            self.options = Options()
                
            # avoiding pop-up window to interfere web crawling
            self.options.add_argument("--disable-notifications")
                
            # don't open the website
            self.options.add_argument("--headless")
            self.options.add_argument("--disable-gpu")
            self.options.add_argument("--disable-software-rasterizer")
                
            # produce fake user to avoid web crawling detection
            self.options.add_argument(f"user-agent={UserAgent().random}")

            self.options.add_argument("--disable-infobars")
            self.options.add_argument("--disable-browser-side-navigation")
                
            # no unnecessary information
            self.options.add_experimental_option('excludeSwitches', ['enable-logging'])

            trying_time = 5
            while trying_time > 0:

                self.chrome = webdriver.Chrome('./chromedriver', options = self.options)
                try:
                    self.chrome.set_page_load_timeout(20)
                    self.chrome.get(url)

                    # waiting for getting certain element(dynamic element)
                    x = WebDriverWait(self.chrome, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[data-testid='page-vulnerability-detail']"))).click()
                    # waiting for the page loading
                    time.sleep(3)
                    
                    soup = BeautifulSoup(self.chrome.page_source, "lxml")
                    root = soup.find("div", {"class" : "ms-Grid-row"})
                    title = root.find("h1").text

                    if title == "Loading...":
                        print(f"Content {owncounter} detects loading.")
                        trying_time = trying_time - 1
                        if trying_time == 0:
                            print(f"Content {owncounter} Retrying failed.")
                            self.chrome.close()
                            self.chrome.quit()
                            break
                        self.chrome.close()
                        self.chrome.quit()
                        continue

                    whole = soup.find("div", {"data-testid" : "page-vulnerability-detail"})
                    date = whole.find("p")
                    
                    # there are some different settings for crawling between Microsoft_SRC and other website
                    # Microsoft update revisions in same url
                    # that is, using url to detect whether the data is new is not reliable
                    # not in database, then it must be crawled
                    if Worker.db_url.T.iloc[0].astype(str).str.count(url).sum() == 0:
                        self.climb(soup, url)

                    # in database, check the update date
                    else:
                        if "Last updated:" in date.text:
                            confirm = date.text[date.text.find("Last updated") + len("Lastupdated: "):]
                            digit = re.findall("[0-9]+", confirm)

                            # turning something like 8/7 to 08/07
                            for i in range(len(digit)):
                                if len(digit[i]) == 1:
                                    digit[i] = f"0{digit[i]}"

                            confirm = f"{digit[0]}年{digit[1]}月{digit[2]}日"
                            today = datetime.datetime.now().strftime("%Y年%m月%d日")
                            if confirm == today:
                                self.climb(soup, url)
                    self.chrome.close()
                    self.chrome.quit()
                    break
                    
                # selenium timeout exception may happen
                except TimeoutException as ex:
                    print(f"Content {owncounter} is in exception.")
                    trying_time = trying_time - 1
                    if trying_time == 0:
                        print(f"Content {owncounter} Retrying failed.\nException has been thrown. {str(ex)}")
                    self.chrome.close()
                    self.chrome.quit()

# Microsft_SRC
class Microsoft:
    
    def Microsoft_crawl(self, soup):
        target_scroll = soup.find_all("div", class_ = "ms-ScrollablePane--contentContainer contentContainer-89")[1]
        presentation = target_scroll.find_all("div", role = "presentation")[1]
        list_page = presentation.find_all("div", class_ = "ms-List-page")
        return list_page
    
    def __init__(self, database, page, mode):
        
        self.urls = []
        self.surls = []
        self.options = Options()
        self.page = page
        self.mode = mode
        
        self.conn = lite.connect(database, check_same_thread=False)

        # empty dataframe for building a database
        df = pd.DataFrame(columns = ['title', 'url', 'content', 'cvss'])
        df.to_sql(name = "MICROSOFT", con = self.conn, if_exists = 'append', index = False)
        
        # for latest page fetching(mode 0)
        if self.mode == 0:
            self.options.add_argument("--disable-notifications")
            self.options.add_argument(f"user-agent={UserAgent().random}")
            self.options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            chrome = webdriver.Chrome('./chromedriver', options = self.options)
            chrome.get("https://msrc.microsoft.com/update-guide/vulnerability")
            chrome.maximize_window()

            # web control
            element = WebDriverWait(chrome, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@data-icon-name="Calendar"]'))).click()
#             element = WebDriverWait(chrome, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="objectObject"]/div/div[2]/div[1]/div/div/div/div/div[1]/button'))).click()
            
            element = WebDriverWait(chrome, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automationid="splitbuttonprimary"]')))
            reset = chrome.find_elements_by_xpath('//*[@data-automationid="splitbuttonprimary"]')[-1]
            reset.click()
            
            element = WebDriverWait(chrome, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-live="polite"]')))
            model = chrome.find_elements_by_xpath('//*[@aria-live="polite"]')[2]
            model.click()
            
            element = WebDriverWait(chrome, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@title="Specific day"]'))).click()
            
            element = WebDriverWait(chrome, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@type="text"]'))).click()
            
            current_year = int(datetime.date.today().year)
            count = current_year - 2016

            # how many times needed to click on the the year control botton(calendar)
            while count > 0:
                element = WebDriverWait(chrome, 30).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div/div/div/div/div/div[2]/div/div/div/div/div[3]/div[1]/div[2]/div/button[1]'))).click()
                time.sleep(0.5)
                count = count - 1

            april = chrome.find_elements_by_class_name("ms-DatePicker-monthOption.monthOption_12df62b9")[3]
            april.click()
            day = chrome.find_elements_by_class_name("day_12df62b9.ms-DatePicker-day-button")[16]
            day.click()
            confirm = chrome.find_elements_by_xpath('//*[@data-automationid="splitbuttonprimary"]')[-3]
            confirm.click()

            # close calender
#             button = chrome.find_elements_by_xpath('//*[@data-icon-name="Calendar"]')[0]
#             button.click()
            
            # loading the scroll pane
            time.sleep(5)
#             last_update = chrome.find_elements_by_xpath('//*[@id="objectObject"]/div/div[2]/div[3]/div[2]/div/div[2]/div/div/div/div[1]/div/div/div/div/div[3]')[1]
#             last_update.click()
            
            last_update = chrome.find_elements_by_xpath('//*[@id="objectObject"]/div/div[2]/div[3]/div[2]/div/div[2]/div/div/div/div[1]/div/div/div/div/div[3]')[0]
            last_update.click()
            time.sleep(5)

            # roll the outer scroll pane to bottom
            js = 'document.getElementsByClassName("ms-ScrollablePane--contentContainer contentContainer-89")[0].scrollTop=document.getElementsByClassName("ms-ScrollablePane--contentContainer contentContainer-89")[0].scrollHeight'
            chrome.execute_script(js)

            time.sleep(3)
            soup = BeautifulSoup(chrome.page_source, 'lxml')
            current_total = soup.find_all("span", {"data-automationid" : "splitbuttonprimary"})
            string = current_total[-1].text
            integer = re.findall("[0-9]+", string)
            current, self.total = int(integer[0]), int(integer[1])
            print("current records: ", current, " total records: ", self.total, 'selfpage: ', self.page)
            
#             self.limit = int(self.page)
            self.limit = 400

            # how many times needed to click on the the scroll pane loading botton(calendar)
            if self.limit > current:

                click = math.ceil((self.limit - current)/current)
                while click > 0:
                    more = chrome.find_elements_by_xpath('//*[@id="objectObject"]/div/div[2]/div[3]/div[3]/button/span')[0]
                    more.click()
                    time.sleep(2)
                    click = click - 1

            elif self.limit == -1:
                click = math.ceil((self.total - current)/current)
                while click > 0:
                    more = chrome.find_elements_by_xpath('//*[@id="objectObject"]/div/div[2]/div[3]/div[3]/button/span')[0]
                    more.click()
                    time.sleep(2)
                    click = click - 1

            soup = BeautifulSoup(chrome.page_source, "html.parser")
            list_page = self.Microsoft_crawl(soup)


            # first 70 records, once search will produce 70 records
            for page in list_page:
                a = page.find_all("a")
                for url in a:
                    self.urls.append(url.get("href").split("/")[-1])

            if self.limit == -1:
                current = self.total
                self.limit = self.total
            else:
                soup = BeautifulSoup(chrome.page_source, 'lxml')
                current_total = soup.find_all("span", {"data-automationid" : "splitbuttonprimary"})
                string = current_total[-1].text
                integer = re.findall("[0-9]+", string)
                current, self.total = int(integer[0]), int(integer[1])

            # roll the inner scroll pane to bottom
            extend = 500
            while True:
                js = f'document.getElementsByClassName("ms-ScrollablePane--contentContainer contentContainer-89")[1].scrollTop={extend}'
                chrome.execute_script(js)

                soup = BeautifulSoup(chrome.page_source, "html.parser")
                list_page = self.Microsoft_crawl(soup)

                for page in list_page:
                    a = page.find_all("a")
                    for url in a:
                        self.urls.append(url.get("href").split("/")[-1])
                extend = extend + 500
                if len(set(self.urls)) >= current:
                    self.surls = list(dict.fromkeys(self.urls))
                    break
                elif len(set(self.urls)) ==0:  #  will run into infinite loop
                    break
                time.sleep(0.5)
                print('len(set(self.urls)): ',len(set(self.urls)) ,'  current:' ,current)

            print(f"All current files({current} files) in page is collected in index.")

            chrome.close()
            chrome.quit()
            
        # for specific page content fetching(mode 2)
        elif self.mode == 2:
            self.queue = queue.Queue()
            self.queue.put(self.page)
            lock = threading.Lock()
            slock = threading.Lock()
            worker1 = Worker(self.queue, self.conn, slock, lock)
            worker1.start()
            worker1.join()
            
            Worker.counter = 0
            
            print("Thread over.")
        
    # for latest data fetching
    def data_fetching_storing(self):
        
        self.queue = queue.Queue()
        
        for url in self.surls[:self.limit]:
            link = "https://msrc.microsoft.com/update-guide/vulnerability/" + url
            self.queue.put(link)
            
        # multi-thread control
        lock = threading.Lock()
        slock = threading.Lock()
        
        worker1 = Worker(self.queue, self.conn, slock, lock)
        worker2 = Worker(self.queue, self.conn, slock, lock)
        worker3 = Worker(self.queue, self.conn, slock, lock)
        worker4 = Worker(self.queue, self.conn, slock, lock)
        worker5 = Worker(self.queue, self.conn, slock, lock)
        worker6 = Worker(self.queue, self.conn, slock, lock)
        worker7 = Worker(self.queue, self.conn, slock, lock)
        worker8 = Worker(self.queue, self.conn, slock, lock)

        worker1.start()
        time.sleep(1)
        worker2.start()
        time.sleep(1)
        worker3.start()
        time.sleep(1)
        worker4.start()
        time.sleep(1)
        worker5.start()
        time.sleep(1)
        worker6.start()
        time.sleep(1)
        worker7.start()
        time.sleep(1)
        worker8.start()

        worker1.join()
        worker2.join()
        worker3.join()
        worker4.join()
        worker5.join()
        worker6.join()
        worker7.join()
        worker8.join()
        
        Worker.counter = 0
        
        print("Thread over.")

