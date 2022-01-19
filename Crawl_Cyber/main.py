#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import warnings
warnings.filterwarnings('ignore')
from Data_analyzing import *
from Bleeping_Computer_Static_Thread import *
from iThome_Static import *
from Three_cltn_Dynamic import *
from Microsoft_Dynamic_Thread import *
from The_Hacker_News_Static_Thread import *
from HTML import *
from Email import *

import datetime
import wx
import os
import sqlite3 as lite
import random 
import wx.grid as gridlib
import pandas as pd
import time
import threading
import nltk

threadflag = False

# for loading pickle and sorting data
class LoadSort(threading.Thread):
    
    def __init__(self, frame, event):
        threading.Thread.__init__(self)
        self.frame = frame
        self.event = event
        self.start()
        
    def run(self):
        
        # means that the html can be produced(if the sorted data exists)
        self.producible = False
        
        pickle = self.frame.input9.GetValue()
        test = Data_Analyzing(self.frame.source_path)
        parent_path = os.path.abspath(os.path.join(self.frame.source_path, os.pardir))
        conn = lite.connect(f"{parent_path}\\{self.frame.input6.GetValue()}")
        
        # fetching keywords from /adjustments/System List.xlsx
        sys, ver, spl, meaning = self.frame.Keyword_Fetching()
        for system, version, splittable, meaningful in zip(sys, ver, spl, meaning):
            query = str(system) + " " + str(version)
            print(f"Key word: {system} {version}")
            test.search(pickle, system, version, splittable, meaningful)
            if not test.out_df.empty:
                self.producible = True
                test.out_df.to_sql(name = f"{query}", con = conn, if_exists = "replace", index = False)
        del test
        wx.CallAfter(self.frame.Sort_Over, self.event, self.producible)

# for sending email
class SendEmail(threading.Thread):
    
    def __init__(self, frame, event, producible):
        threading.Thread.__init__(self)
        self.frame = frame
        self.event = event
        self.producible = producible
        self.start()
        
    def run(self):
        self.frame.recipient_list = []
        
        # fetching recipients and sender
        path = os.getcwd() + "\\adjustments"
        with open(fr"{path}\recipient.txt", "a+") as rec:
            rec.seek(0)
            for line in rec.readlines():
                self.frame.recipient_list.append(line.strip("\n"))
        if len(self.frame.recipient_list) == 0 or self.frame.input14.GetValue() == "":
            wx.CallAfter(self.frame.Sending_error)
        else:
            test = Email(self.frame.html_dir, self.frame.input14.GetValue(), self.frame.recipient_list, self.producible)
            test.sending()
            del test
            wx.CallAfter(self.frame.Send_Over)

# for generating html table
class HTMLGEN(threading.Thread):
    
    def __init__(self, frame, event, producible):
        threading.Thread.__init__(self)
        self.frame = frame
        self.event = event
        self.producible = producible
        self.start()
        
    def run(self):
        if self.producible:
            database = self.frame.db_display_path
            path = self.frame.input13.GetValue()
            test = Generative_HTML(database, path)
            del test
        wx.CallAfter(self.frame.HTML_Over, self.event, self.producible)

# for building pickle and sorting
class BuildSort(threading.Thread):
    
    def __init__(self, frame, event):
        threading.Thread.__init__(self)
        self.frame = frame
        self.event = event
        self.start()
        
    def run(self):
        model_directory = self.frame.input7.GetValue()
        pickle_name = self.frame.input11.GetValue()
        
        test = Data_Analyzing(self.frame.source_path)
        test.new_model_build(model_directory, pickle_name)
        
        parent_path = os.path.abspath(os.path.join(self.frame.source_path, os.pardir))
        conn = lite.connect(f"{parent_path}\\{self.frame.input6.GetValue()}")
        
        # means that there is new data in the database need to be sorted(search through keywords)
        self.searchable = test.searchable
        
        # means that the html can be produced(if the sorted data exists)
        self.producible = False
        
        if self.searchable:
            # fetching keywords from /adjustments/System List.xlsx
            sys, ver, spl, meaning = self.frame.Keyword_Fetching()
            for system, version, splittable, meaningful in zip(sys, ver, spl, meaning):
                query = str(system) + " " + str(version)
                print(f"Key word: {system} {version}")
                test.search(f"{model_directory}\\{pickle_name}", system, version, splittable, meaningful)
                if not test.out_df.empty:
                    self.producible = True
                    test.out_df.to_sql(name = f"{query}", con = conn, if_exists = "replace", index = False)
            self.frame.input9.SetValue(f"{model_directory}\\{pickle_name}")
        del test
        wx.CallAfter(self.frame.Sort_Over, self.event, self.producible)

# for the main flow of data crawling
class CrawlThread(threading.Thread):
    
    def __init__(self, frame, event):
        threading.Thread.__init__(self)
        self.frame = frame
        self.event = event
        self.start()
        
    def run(self):
        
        latest = self.frame.Rad1.GetValue()
        page_list = self.frame.Rad2.GetValue()
        content = self.frame.Rad3.GetValue()
        
        website = self.frame.combo1.GetValue()
        database = self.frame.combo2.GetValue()
        pages = self.frame.input2.GetValue()
        spl = self.frame.input3.GetValue()
        spc = self.frame.input4.GetValue()
        
        file = self.frame.combo2.GetValue()
        naming = file.split(".")[0]
        self.frame.source_path = self.frame.input1.GetValue() + "\\" + file
        self.frame.input5.SetValue(file)
        self.frame.input6.SetValue(f"{naming}_sorted.db")
        self.frame.input11.SetValue(f"{naming}.p")
        self.frame.input12.SetValue(f"{naming}_sorted.db")
        self.frame.db_display_path = self.frame.input1.GetValue() + "\\" + f"{naming}_sorted.db"
        
        # checking whether the way of naming database is legal
        filename_extension = database.find(".")
        if filename_extension == -1:
            database = database + ".db"
            self.frame.combo2.SetValue(database)
        check = database.split(".")
        if check[1] != "db":
            wx.CallAfter(self.frame.Wrong_DB)
        elif check[0] == "":
            wx.CallAfter(self.frame.Blank_DB)
        else:
            target_database = self.frame.input1.GetValue() + "\\" + database
            
            # crawling all of the five data sources web
            if website == "ALL":
                bleeping_computer = Bleeping_Computer(target_database, 5, 0)
                bleeping_computer.data_fetching_storing()
                del bleeping_computer
                
                ithome = iThome(target_database, 5, 0)
                ithome.data_fetching_storing()
                del ithome
                
                three_cltn = Three_cltn(target_database, 50, 0)
                three_cltn.data_fetching_storing()
                del three_cltn
                
                microsoft = Microsoft(target_database, 100, 0)
                microsoft.data_fetching_storing()
                del microsoft
                
                thn = The_Hacker_News(target_database, 15, 0)
                del thn
                wx.CallAfter(self.frame.Crawl_Over, self.event)
                
            # if not "ALL", we have three options, "latest", "page_list" and "content"
            elif latest:
                if pages == "":
                    wx.CallAfter(self.frame.Blank_Block)
                else:
                    if website == "Bleeping_Computer":
                        
                        # default value
                        if pages == "Latest n Pages(default 1) Crawling, n = " or pages == "":
                            pages = 1
                            bleeping_computer = Bleeping_Computer(target_database, pages, 0)
                            bleeping_computer.data_fetching_storing()
                            del bleeping_computer
                            wx.CallAfter(self.frame.Crawl_Over, self.event)
                            
                        else:
                            try:
                                pages = int(pages)
                                bleeping_computer = Bleeping_Computer(target_database, pages, 0)
                                bleeping_computer.data_fetching_storing()
                                del bleeping_computer
                                wx.CallAfter(self.frame.Crawl_Over, self.event)
                            except:
                                wx.CallAfter(self.frame.Integer_Block)

                    elif website == "iThome":
                        
                        # default value
                        if pages == "Latest n Pages(default 1) Crawling, n = " or pages == "":
                            pages = 1
                            ithome = iThome(target_database, pages, 0)
                            ithome.data_fetching_storing()
                            del ithome
                            wx.CallAfter(self.frame.Crawl_Over, self.event)
                            
                        else:
                            try:
                                pages = int(pages)
                                ithome = iThome(target_database, pages, 0)
                                ithome.data_fetching_storing()
                                del ithome
                                wx.CallAfter(self.frame.Crawl_Over, self.event)
                            except:
                                wx.CallAfter(self.frame.Integer_Block)

                    elif website == "Three_cltn":
                        
                        # default value
                        if pages == "n records (up to 300, default 1, all -1)fetching limit, n = " or pages == "":
                            pages = 1
                            three_cltn = Three_cltn(target_database, pages, 0)
                            three_cltn.data_fetching_storing()
                            del three_cltn
                            wx.CallAfter(self.frame.Crawl_Over, self.event)
                            
                        else:
                            try:
                                pages = int(pages)
                                if pages > 300:
                                    pages = 300
                                three_cltn = Three_cltn(target_database, pages, 0)
                                three_cltn.data_fetching_storing()
                                del three_cltn
                                wx.CallAfter(self.frame.Crawl_Over, self.event)
                            except:
                                wx.CallAfter(self.frame.Integer_Block)

                    elif website == "Microsoft_SRC":
                        
                        # default value
                        if pages == "Crawling n records from newest CVE(default 1, all -1), n = " or pages == "":
                            pages = 1
                            microsoft = Microsoft(target_database, pages, 0)
                            microsoft.data_fetching_storing()
                            del microsoft
                            wx.CallAfter(self.frame.Crawl_Over, self.event)
                            
                        else:
                            try:
                                pages = int(pages)
                                microsoft = Microsoft(target_database, pages, 0)
                                microsoft.data_fetching_storing()
                                del microsoft
                                wx.CallAfter(self.frame.Crawl_Over, self.event)
                            except:
                                wx.CallAfter(self.frame.Integer_Block)

                    elif website == "The_Hacker_News":
                        
                        # default value
                        if pages == "Latest n Pages Crawling(default 1), n = ":
                            pages = 1
                            thn = The_Hacker_News(target_database, pages, 0)
                            del thn
                            wx.CallAfter(self.frame.Crawl_Over, self.event)
                            
                        else:
                            try:
                                pages = int(pages)
                                thn = The_Hacker_News(target_database, pages, 0)
                                del thn
                                wx.CallAfter(self.frame.Crawl_Over, self.event)
                            except:
                                wx.CallAfter(self.frame.Integer_Block)

            # for specific page list fetching
            elif page_list:
                if spl == "":
                    wx.CallAfter(self.frame.Blank_Block)
                else:
                    if website == "Bleeping_Computer":
                        bleeping_computer = Bleeping_Computer(target_database, spl, 1)
                        bleeping_computer.data_fetching_storing()
                        del bleeping_computer
                        wx.CallAfter(self.frame.Crawl_Over, self.event)

                    elif website == "iThome":
                        ithome = iThome(target_database, spl, 1)
                        ithome.data_fetching_storing()
                        del ithome
                        wx.CallAfter(self.frame.Crawl_Over, self.event)

                    elif website == "Three_cltn":
                        wx.CallAfter(self.frame.None_Block)
                    elif website == "Microsoft_SRC":
                        wx.CallAfter(self.frame.None_Block)
                    elif website == "The_Hacker_News":
                        thn = The_Hacker_News(target_database, spl, 1)
                        del thn
                        wx.CallAfter(self.frame.Crawl_Over, self.event)

            # fro specific page content fetching
            elif content:
                if spc == "":
                    wx.CallAfter(self.frame.Blank_Block)
                else:
                    if website == "Bleeping_Computer":
                        bleeping_computer = Bleeping_Computer(target_database, spc, 2)
                        bleeping_computer.data_fetching_storing()
                        del bleeping_computer

                    elif website == "iThome":
                        ithome = iThome(target_database, spc, 2)
                        ithome.data_fetching_storing()
                        del ithome

                    elif website == "Three_cltn":
                        three_cltn = Three_cltn(target_database, spc, 2)
                        del three_cltn

                    elif website == "Microsoft_SRC":
                        microsoft = Microsoft(target_database, spc, 2)
                        del microsoft

                    elif website == "The_Hacker_News":
                        thn = The_Hacker_News(target_database, spc, 2)
                        del thn
                    wx.CallAfter(self.frame.Crawl_Over, self.event)

# for building the grid panel for inspecting the database content        
class GridPanel(wx.Panel):
    def __init__(self, parent, i, df_list):
        self.parent = parent
        wx.Panel.__init__(self, parent = parent)
        
        data_grid = gridlib.Grid(self)
        data_grid.CreateGrid(len(df_list[i]), len(df_list[i].columns))
        data_grid.SetDefaultColSize(200, True)
        data_grid.SetColSize(2, 300)
        data_grid.SetDefaultRowSize(70, True)
        data_grid.SetGridLineColour(wx.BLACK)
        for j in range(len(df_list[i].columns)):
            data_grid.SetColLabelValue(j, df_list[i].columns[j])
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(data_grid, 1, flag = wx.ALL | wx.EXPAND)
        self.SetSizer(sizer)
            
        for j in range(len(df_list[i])):
            for k in range(len(df_list[i].columns)):
                data_grid.SetCellValue(j, k, str(df_list[i].iloc[j, k]))
        
# for building the frame of database inspection
class DB_Frame(wx.Frame):
    
    def __init__(self, table_list, df_list):
        wx.Frame.__init__(self, None, title = "Database Inspection Grid", size = (950, 500))
        
        panel_list = []
        main_panel = wx.Panel(self)
        self.notebook = wx.Notebook(main_panel)
        
        for i in range(len(table_list)):
            panel = GridPanel(self.notebook, i, df_list)
            panel_list.append(panel)
            
        for i in range(len(panel_list)):
            self.notebook.AddPage(panel_list[i], table_list[i])
            
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, flag = wx.ALL | wx.EXPAND, border = 10)
        
        main_panel.SetSizer(sizer)
        
#         self.Centre()
        self.Show()

# the main GUI of the program
class MyFrame(wx.Frame):
    
    weblist = ["ALL","Bleeping_Computer", "iThome", "Three_cltn", "Microsoft_SRC", "The_Hacker_News"]
    
    def __init__(self):
        
        super().__init__(None, title = "Crawling Interface", size = (1220, 800))
#         self.Centre()
        self.root = os.getcwd()
        panel = wx.Panel(self)
        
        # directories building
        self.multi_path_build()
        
        # layout
        # horizontal 1
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        text1 = wx.StaticText(panel, label = "Target Web Crawling: ", size = (130, -1))
        self.combo1 = wx.ComboBox(panel, -1, choices = self.weblist, value = "ALL", style = wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, lambda event: self.page_hint(event), self.combo1)
        hbox1.Add(text1, 0, flag = wx.ALL, border = 10)
        hbox1.Add(self.combo1, 0, flag = wx.ALL, border = 10)
        
        text2 = wx.StaticText(panel, label = "Storing Path: ")
        hbox1.Add(text2, 0, flag = wx.ALL, border = 10)
        self.input1 = wx.TextCtrl(panel, style = wx.TE_READONLY, size = (500, -1))
        self.input1.SetValue(os.getcwd() + f"\databases\\{date.today()}")
        hbox1.Add(self.input1, 0, flag = wx.ALL | wx.EXPAND, border = 10)
        
        button0 = wx.Button(panel, -1, label = "Change Path")
        self.Bind(wx.EVT_BUTTON, lambda event: self.storing_path(event), button0)
        hbox1.Add(button0, 0, flag = wx.ALL, border = 10)
        
        # horizontal 2
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.db_counting()
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        text3 = wx.StaticText(panel, label = "Storing Database: ", size = (130, -1))
        self.combo2 = wx.ComboBox(panel, -1, choices = self.db_list, value = f"{date.today()}_crawled.db")
        self.Bind(wx.EVT_COMBOBOX_DROPDOWN, lambda event: self.database_refresh(event), self.combo2)
        hbox2.Add(text3, 0, flag = wx.ALL, border = 10)
        hbox2.Add(self.combo2, 0, flag = wx.ALL, border = 10)
        
        # horizontal 3
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        
        text4 = wx.StaticText(panel, label = "Pages/records Latest: ", size = (130, -1))
        self.input2 = wx.TextCtrl(panel, style=wx.TE_RICH)
        self.input2.SetValue("Latest n Pages(default 1) Crawling, n = ")
        self.input2.SetForegroundColour(wx.LIGHT_GREY)
        hbox3.Add(text4, 0, flag = wx.ALL, border = 10)
        hbox3.Add(self.input2, 20, flag = wx.ALL | wx.EXPAND, border = 10)
        
        text5 = wx.StaticText(panel, label = "Specific Page List:")
        self.input3 = wx.TextCtrl(panel, style=wx.TE_RICH)
        self.input3.SetValue("https://www.ithome.com.tw/security?page=0")
        self.input3.SetForegroundColour(wx.LIGHT_GREY)
        hbox3.Add(text5, 0, flag = wx.ALL, border = 10)
        hbox3.Add(self.input3, 20, flag = wx.ALL | wx.EXPAND, border = 10)
        
        # horizontal 4
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        
        text6 = wx.StaticText(panel, label = "Specific Page Content:", size = (130, -1))
        self.input4 = wx.TextCtrl(panel, style=wx.TE_RICH, size = (500, -1))
        self.input4.SetValue("https://www.ithome.com.tw/news/145496")
        self.input4.SetForegroundColour(wx.LIGHT_GREY)
        hbox4.Add(text6, 0, flag = wx.ALL, border = 10)
        hbox4.Add(self.input4, 20, flag = wx.ALL | wx.EXPAND, border = 10)
        
        hbox4.Add(100, 0, wx.EXPAND)
        
        self.Rad1 = wx.RadioButton(panel, -1, label = "Latest: ", style = wx.RB_GROUP)
        self.Rad2 = wx.RadioButton(panel, -1, label = "List: ")
        self.Rad3 = wx.RadioButton(panel, -1, label = "Content: ")
        self.Rad1.SetValue(True)
        self.Bind(wx.EVT_RADIOBUTTON, lambda event : self.changing_color(event), self.Rad1)
        self.Bind(wx.EVT_RADIOBUTTON, lambda event : self.changing_color(event), self.Rad2)
        self.Bind(wx.EVT_RADIOBUTTON, lambda event : self.changing_color(event), self.Rad3)
        hbox4.Add(self.Rad1, 1, wx.EXPAND)
        hbox4.Add(self.Rad2, 1, wx.EXPAND)
        hbox4.Add(self.Rad3, 1, wx.EXPAND)
        
        
        button1 = wx.Button(panel, -1, label = "Submit")
        hbox4.Add(button1, 0, flag = wx.ALL, border = 10)
        self.Bind(wx.EVT_BUTTON, lambda event: self.submittion(event), button1)
        
        # horizontal medium
        hboxm = wx.BoxSizer(wx.HORIZONTAL)
        hboxm.Add((0, 30))
        
        # horizontal 5
        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        text7 = wx.StaticText(panel, label = "Source database: ", size = (130, -1))
        self.input5 = wx.TextCtrl(panel, style = wx.TE_READONLY, size = (190, -1))
        self.input5.SetValue("crawled_data_consolidation.db")
        self.source_path = fr"{os.getcwd()}\databases\crawled_data_consolidation.db"
        hbox5.Add(text7, 0, flag = wx.ALL, border = 10)
        hbox5.Add(self.input5, 0, flag = wx.ALL, border = 10)
        
        button2 = wx.Button(panel, -1, label = "Browsing", size = (90, -1))
        hbox5.Add(button2, 0, flag = wx.ALL, border = 10)
        self.Bind(wx.EVT_BUTTON, lambda event: self.browsing(event), button2)
        
        # horizontal 6
        hbox6 = wx.BoxSizer(wx.HORIZONTAL)
        text9 = wx.StaticText(panel, label = "Sorted database: ", size = (130, -1))
        self.input6 = wx.TextCtrl(panel, size = (190, -1))
        self.input6.SetValue("crawled_data_consolidation_sorted.db")
        hbox6.Add(text9, 0, flag = wx.ALL, border = 10)
        hbox6.Add(self.input6, 0, flag = wx.ALL, border = 10)
        
        # horizontal 7
        hbox7 = wx.BoxSizer(wx.HORIZONTAL)
        text10 = wx.StaticText(panel, label = "Model saving path: ", size = (130, -1))
        self.input7 = wx.TextCtrl(panel, style = wx.TE_READONLY, size = (450, -1))
        self.input7.SetValue(os.getcwd() + f"\models\\{date.today()}")
        hbox7.Add(text10, 0, flag = wx.ALL, border = 10)
        hbox7.Add(self.input7, 0, flag = wx.ALL, border = 10)
        
        button3 = wx.Button(panel, -1, label = "Change Path", size = (90, -1))
        self.Bind(wx.EVT_BUTTON, lambda event: self.model_path(event), button3)
        hbox7.Add(button3, 0, flag = wx.ALL, border = 10)
        
        # horizontal 8
        hbox8 = wx.BoxSizer(wx.HORIZONTAL)
        text13 = wx.StaticText(panel, label = "Model name: ", size = (130, -1))
        self.input11 = wx.TextCtrl(panel, size = (215, -1))
        self.input11.SetValue("crawled_data_consolidation.p")
        hbox8.Add(text13, 0, flag = wx.ALL, border = 10)
        hbox8.Add(self.input11, 0, flag = wx.ALL, border = 10)
        
        button5 = wx.Button(panel, -1, label = "Building_model && Sorting", size = (170, -1))
        hbox8.Add(button5, 0, flag = wx.ALL, border = 10)
        self.Bind(wx.EVT_BUTTON, lambda event: self.building_sorting(event), button5)
        
        # horizontal medium2
        hboxm2 = wx.BoxSizer(wx.HORIZONTAL)
        hboxm2.Add((0, 30))
        
        # horizontal 10
        hbox10 = wx.BoxSizer(wx.HORIZONTAL)
        text12 = wx.StaticText(panel, label = "Load pickle model: ", size = (130, -1))
        self.input9 = wx.TextCtrl(panel, style = wx.TE_READONLY | wx.TE_RICH, size = (300, -1))
        self.input9.SetValue("*.p")
        self.input9.SetForegroundColour(wx.LIGHT_GREY)
        hbox10.Add(text12, 0, flag = wx.ALL, border = 10)
        hbox10.Add(self.input9, 0, flag = wx.ALL, border = 10)
        
        button6 = wx.Button(panel, -1, label = "Load pickle", size = (90, -1))
        hbox10.Add(button6, 0, flag = wx.ALL, border = 10)
        self.Bind(wx.EVT_BUTTON, lambda event: self.pickle_load(event), button6)
        
        button7 = wx.Button(panel, -1, label = "Use loaded model Sorting", size = (170, -1))
        hbox10.Add(button7, 0, flag = wx.ALL, border = 10)
        self.Bind(wx.EVT_BUTTON, lambda event: self.loading_sorting(event), button7)
        
        # horizontal 11
        hbox11 = wx.BoxSizer(wx.HORIZONTAL)
        text14 = wx.StaticText(panel, label = "* Noticing that*.p file is related to Source database.\n* Sorted database will be put in the same path of Source database.")
        hbox11.Add(text14, 0, flag = wx.ALL, border = 10)
        
        # horizontal medium3
        hboxm3 = wx.BoxSizer(wx.HORIZONTAL)
        hboxm3.Add((0, 30))
        
        # horizontal 12
        hbox12 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.db_display_path = f"{os.getcwd()}\databases\crawled_data_consolidation.db"
        self.input12 = wx.TextCtrl(panel, -1, style = wx.TE_READONLY, size = (200, -1))
        self.input12.SetValue("crawled_data_consolidation.db")
        hbox12.Add(self.input12, 0, flag = wx.ALL, border = 10)
        
        button8 = wx.Button(panel, -1, label = "DataBase Browsing")
        hbox12.Add(button8, 0, flag = wx.ALL, border = 10)
        self.Bind(wx.EVT_BUTTON, lambda event: self.db_path(event), button8)
        
        button9 = wx.Button(panel, -1, label = "DataBase Inspection")
        hbox12.Add(button9, 0, flag = wx.ALL, border = 10)
        self.Bind(wx.EVT_BUTTON, lambda event: self.db_display(event), button9)
        
        self.Rad4 = wx.RadioButton(panel, -1, label = "Automatic: ", style = wx.RB_GROUP)
        self.Rad5 = wx.RadioButton(panel, -1, label = "Manual: ")
        self.Rad5.SetValue(True)
        
        self.text15 = wx.StaticText(panel, wx.ID_ANY, time.strftime("%Y-%m-%d  %H:%M:%S"))
        hbox12.Add((350, 0))
        hbox12.Add(self.Rad4, 0, wx.EXPAND)
        hbox12.Add(self.Rad5, 0, wx.EXPAND)
        hbox12.Add(self.text15, 0, flag = wx.ALL, border = 10)
        
        # time control
        self.old_dateconfirm = datetime.datetime.now().strftime("%d")
        self.DeadLine = datetime.datetime.now() + datetime.timedelta(seconds = int(5))
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda event: self.Counter(event), self.timer)
        self.timer.Start(1000)
        
        # horizontal 13
        hbox13 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.html_dir = f"{os.getcwd()}\\htmls\\{date.today()}"
        self.input13 = wx.TextCtrl(panel, -1, style = wx.TE_READONLY, size = (347, -1))
        self.input13.SetValue(self.html_dir)
        hbox13.Add(self.input13, 0, flag = wx.ALL, border = 10)
        
        button11 = wx.Button(panel, -1, label = "HTML Path Change", size = (137, -1))
        hbox13.Add(button11, 0, flag = wx.ALL, border = 10)
        self.Bind(wx.EVT_BUTTON, lambda event: self.html_path(event), button11)
        
        button10 = wx.Button(panel, -1, label = "HTML generating", size = (137, -1))
        hbox13.Add(button10, 0, flag = wx.ALL, border = 10)
        self.Bind(wx.EVT_BUTTON, lambda event: self.html_generating(event, True), button10)
        
        hbox13.Add((250, 0))
        
        self.looplist = ["Every Day"]
        self.combo3 = wx.ComboBox(panel, -1, choices = self.looplist, value = "Every Day", style = wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, lambda event: self.Able(event), self.combo3)
        hbox13.Add(self.combo3, 0, flag = wx.ALL, border = 10)
        
        hlist = [str(i)+":00" for i in range(0, 24)]
        slist = ["0"+i for i in hlist[:10]]
        self.hourlist = slist + hlist[10:]
        text17 = wx.StaticText(panel, label = "Hour: ")
        self.combo5 = wx.ComboBox(panel, -1, choices = self.hourlist, value = "08:00", style = wx.CB_READONLY)
        hbox13.Add(text17, 0, flag = wx.ALL, border = 10)
        hbox13.Add(self.combo5, 0, flag = wx.ALL, border = 10)
        
        # horizontal 14
        hbox14 = wx.BoxSizer(wx.HORIZONTAL)
        text18 = wx.StaticText(panel, label = "Sender:", size = (85, -1), style = wx.TE_READONLY)
        hbox14.Add(text18, 0, flag = wx.ALL, border = 10)
        
        path = self.root + "\\adjustments"
        with open(fr"{path}\sender.txt", "a+") as sed:
            sed.seek(0)
            self.sender = sed.readline()
        
        self.input14 = wx.TextCtrl(panel, -1, size = (137, -1), style = wx.TE_READONLY)
        self.input14.SetValue(self.sender)
        hbox14.Add(self.input14, 0, flag = wx.ALL, border = 10)
        
        text19 = wx.StaticText(panel, label = "Recipient List:", size = (85, -1))
        hbox14.Add(text19, 0, flag = wx.ALL, border = 10)
        
        self.recipient_list = []
        with open(fr"{path}\recipient.txt", "a+") as rec:
            rec.seek(0)
            for line in rec.readlines():
                self.recipient_list.append(line)
        
        self.combo6 = wx.ComboBox(panel, -1, choices = self.recipient_list, style = wx.CB_READONLY, size = (137, -1))
        try:
            self.combo6.SetValue(self.recipient_list[0])
        except:
            self.combo6.SetValue("")
        hbox14.Add(self.combo6, 0, flag = wx.ALL, border = 10)
        self.Bind(wx.EVT_COMBOBOX_DROPDOWN, lambda event: self.rec_refresh(event), self.combo6)
        
        button12 = wx.Button(panel, -1, label = "Send Email", size = (137, -1))
        hbox14.Add(button12, 0, flag = wx.ALL, border = 10)
        self.Bind(wx.EVT_BUTTON, lambda event: self.email_sending(event, True), button12)
        
        # horizontal 15
        hbox15 = wx.BoxSizer(wx.HORIZONTAL)
        text20 = wx.StaticText(panel, label = "* Sender && recipient should be set in corresponding txt file in the same directory, not in this GUI.")
        hbox15.Add(text20, 0, flag = wx.ALL, border = 10)
        
        
        # total vbox
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox1,  0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hbox2,  0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hbox3,  0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hbox4,  0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hboxm,  0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hbox5,  0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hbox6,  0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hbox7,  0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hbox8,  0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hboxm2, 0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hbox10, 0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hbox11, 0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hboxm3, 0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hbox12, 0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hbox13, 0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hbox14, 0, flag = wx.ALL | wx.EXPAND)
        vbox.Add(hbox15, 0, flag = wx.ALL | wx.EXPAND)
        
        panel.SetSizer(vbox)
    
    # building directories
    def multi_path_build(self):
        path = os.getcwd()
        try:
            os.mkdir(path + "\\adjustments")
        except:
            pass
        try:
            os.mkdir(path + "\databases")
        except:
            pass
        try:
            os.mkdir(path + "\models")
        except:
            pass
        try:
            os.mkdir(path + "\htmls")
        except:
            pass
        
        parent_dir = path + "\databases"
        target_dir = str(date.today())
        self.path = os.path.join(parent_dir, target_dir)
        try:
            os.mkdir(self.path)
        except:
            pass
        parent_dir = path + "\models"
        target_dir = str(date.today())
        self.path = os.path.join(parent_dir, target_dir)
        try:
            os.mkdir(self.path)
        except:
            pass
        parent_dir = path + "\htmls"
        target_dir = str(date.today())
        self.path = os.path.join(parent_dir, target_dir)
        try:
            os.mkdir(self.path)
        except:
            pass
            
    # main flow of automatic
    
    # first crawling
    def submittion(self, event):
        print("Starting crawling.")
        thread = CrawlThread(self, event)
    
    # crawling over, if automatic then go to building and sorting
    def Crawl_Over(self, event):
        if not self.threadflag:
            confirm = wx.MessageDialog(None, "Crawling has finished.")
            confirm.ShowModal()
        else:
            print("Starting Sorting.")
            self.building_sorting(event)
    
    # building and sorting
    def building_sorting(self, event):
        thread = BuildSort(self, event)
    
    # sorting over, if automatic then go to html generating
    def Sort_Over(self, event, producible):
        if not self.threadflag:
            if producible:
                confirm = wx.MessageDialog(None, "Sorting over.", style = wx.ICON_INFORMATION)
                confirm.ShowModal()
            else:
                confirm = wx.MessageDialog(None, "There is no new data needed to be analyzed.", style = wx.ICON_INFORMATION)
                confirm.ShowModal()
        else:
            print("Starting HTML generating.")
            self.html_generating(event, producible)
    
    # html generating
    def html_generating(self, event, producible):
        thread = HTMLGEN(self, event, producible)
    
    # html generating over, if automatic then go to mail sending
    def HTML_Over(self, event, producible):
        if not self.threadflag:
            if producible:
                confirm = wx.MessageDialog(None, "HTML generating over.", style = wx.ICON_INFORMATION)
                confirm.ShowModal()
        else:
            print("Starting mail sending.")
            self.email_sending(event, producible)
    
    # mail sending
    def email_sending(self, event, producible):
        thread = SendEmail(self, event, producible)
        
    # mail sending over
    def Send_Over(self):
        if not self.threadflag:
            confirm = wx.MessageDialog(None, "Mail sending over.", style = wx.ICON_INFORMATION)
            confirm.ShowModal()
        else:
            print("Mail sending over.")
            global threadflag
            threadflag = False
            self.threadflag = False
    
    # detecting that sender.txt recipient.txt is empty
    def Sending_error(self):
        confirm = wx.MessageDialog(None, "Sender or Recipient shouldn't be blank.", style = wx.ICON_WARNING)
        confirm.ShowModal()
    # end of flow    
    
    # for manul operation, loading pickle and sorting
    def loading_sorting(self, event):
        thread = LoadSort(self, event)
    
    # illegal databases naming detection
    def Wrong_DB(self):
        if not self.threadflag:
            confirm = wx.MessageDialog(None, "The name of the entered database is not allowed.\nPlease renaming it.", style = wx.ICON_WARNING)
            confirm.ShowModal()
    
    def Blank_DB(self):
        if not self.threadflag:
            confirm = wx.MessageDialog(None, "Blanking database name is not allowed.\nPlease naming it.", style = wx.ICON_WARNING)
            confirm.ShowModal()
    
    # illegal number of pages as input
    def Integer_Block(self):
        if not self.threadflag:
            confirm = wx.MessageDialog(None, "Please input an integer or using default.", style = wx.ICON_WARNING)
            confirm.ShowModal()
            
    # for "Microsoft_SRC" and "Three_cltn", pagelist is not existed
    def None_Block(self):
        if not self.threadflag:
            confirm = wx.MessageDialog(None, "This movement can not apply to this website.", style = wx.ICON_WARNING)
            confirm.ShowModal()
        
    def Blank_Block(self):
        if not self.threadflag:
            confirm = wx.MessageDialog(None, "Blanking is not allowed.\nPlease input a correct URL.", style = wx.ICON_WARNING)
            confirm.ShowModal()
    
    # time counter, display on GUI
    def Counter(self, event):
        global threadflag
        self.threadflag = threadflag
        self.text15.SetLabel(time.strftime("%Y-%m-%d  %H:%M:%S"))
        automatic = self.Rad4.GetValue()
        manual = self.Rad5.GetValue()
        condition = self.combo3.GetValue()
        hour = self.combo5.GetValue()
        
        # read the content of the file "sender.txt" per second
        with open(fr"{self.root}\\adjustments\sender.txt", "a+") as sed:
            sed.seek(0)
            self.sender = sed.readline()
        self.input14.SetValue(self.sender)
        
        # day crossing detection
        loop = datetime.datetime.now()
        self.new_dateconfirm = loop.strftime("%d")
        if self.new_dateconfirm != self.old_dateconfirm:
            self.multi_path_build()
            self.input1.SetValue(os.getcwd() + f"\databases\\{date.today()}")
            self.combo2.SetValue(f"{date.today()}_crawled.db")
            self.input7.SetValue(os.getcwd() + f"\models\\{date.today()}")
            self.html_dir = f"{os.getcwd()}\\htmls\\{date.today()}"
            self.input13.SetValue(self.html_dir)
            
        self.old_dateconfirm = self.new_dateconfirm
        
        # automatic detection
        if automatic and not self.threadflag:
            if (self.DeadLine - datetime.datetime.now()).total_seconds() <= 0:
                if condition == "Every Day":
                    if hour == f"{loop.strftime('%H')}:{loop.strftime('%M')}":
                        self.threadflag = True
                        threadflag = self.threadflag
                        print("Crawl && Sort Operation Starting.")
                        
                        # the start of automatic
                        self.submittion(event)
                        
        # the automatic option will be effective after five seconds
        else:
            self.DeadLine = datetime.datetime.now() + datetime.timedelta(seconds = int(5))
    
    # the button of inspecting database
    def db_display(self, event):
        dataframe_list = []
        table_name_list = []
        con = lite.connect(self.db_display_path)
        with con:
            cur = con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            all_table = cur.fetchall()
            for i in all_table:
                table_name_list.append(i[0])
            table_name_list = sorted(table_name_list)
            
        for i in table_name_list:
            df = pd.DataFrame()
            dataframe_list.append(pd.read_sql_query(f"SELECT * FROM [{i}]", con))

        frm = DB_Frame(table_name_list, dataframe_list)
    
    # database path changing
    def db_path(self, event):
        path = os.getcwd()
        with wx.FileDialog(self, "Open database as source", f"{path}\databases",
                           wildcard = "Database files (*.db)|*.db",
                           style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.db_display_path = fileDialog.GetPath()
            self.input12.SetValue(self.db_display_path.split("\\")[-1])
    
    # html table storing path changing
    def html_path(self, event):
        path = os.getcwd()
        with wx.DirDialog(self, "Open database as source", f"{path}\htmls",
                           style = wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.html_dir = dirDialog.GetPath()
            self.input13.SetValue(dirDialog.GetPath())
    
    # fetching keywords from "\adjustments\System List.xlsx"
    def Keyword_Fetching(self):
        path = fr"{os.getcwd()}\adjustments\System List.xlsx"
        df = pd.read_excel(path).replace(np.nan, "", regex = True)
        system = df.iloc[:, 0]
        version = df.iloc[:, 1]
        splittable = df.iloc[:, 2]
        meaning = df.iloc[:, 3]
        return system, version, splittable, meaning
    
    # pickle storing path changing
    def model_path(self, event):
        path = os.getcwd()
        with wx.DirDialog(self, "Open database as source", f"{path}\models",
                           style = wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.input7.SetValue(dirDialog.GetPath())
    
    # pickle loading path
    def pickle_load(self, event):
        path = os.getcwd()
        with wx.FileDialog(self, "Open database as source", f"{path}\models",
                           wildcard = "Pickle files (*.p)|*.p",
                           style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.input9.SetValue(fileDialog.GetPath())
            self.input9.SetForegroundColour(wx.BLACK)
    
    # database storing path changing
    def storing_path(self, event):
        path = os.getcwd()
        with wx.DirDialog(self, "Open database as source", f"{path}\databases",
                           style = wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.input1.SetValue(dirDialog.GetPath())
    
    # recipients file refreshing
    def rec_refresh(self, event):
        
        self.recipient_list = []
        path = self.root + "\\adjustments"
        with open(fr"{path}\recipient.txt", "a+") as rec:
            rec.seek(0)
            for line in rec.readlines():
                self.recipient_list.append(line)
        self.combo6.Clear()
        self.combo6.Append(self.recipient_list)
        self.combo6.SetValue(self.recipient_list[0])
    
    # database browsing
    def browsing(self, event):
        path = os.getcwd()
        with wx.FileDialog(self, "Open database as source", f"{path}\databases",
                           wildcard = "Database files (*.db)|*.db",
                           style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.source_path = fileDialog.GetPath()
            name = self.source_path.split("\\")[-1]
            self.input5.SetValue(name)
        apart = name.split(".")
        self.input6.SetValue(f"{apart[0]}_sorted.db")
        self.input11.SetValue(f"{apart[0]}.p")
    
    # different table count
    def table_counting(self):
        
        source_db = self.input5.GetValue()
        
        current_path = os.getcwd()
        conn = lite.connect(f"{current_path}\\databases\\{source_db}")
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            table = cur.fetchall()
        if len(table) == 0:
            self.table_list = []
        else:
            self.table_list = []
            for i in table:
                self.table_list.append(i[0])
            self.table_list.append("ALL")
            self.table_list = sorted(self.table_list)
            
    # database refresh
    def database_refresh(self, event):
        self.db_list = []
        self.combo2.Clear()
        self.db_counting()
        self.combo2.Append(self.db_list)
    
    # how many database in the directory
    def db_counting(self):
        files = os.listdir(self.input1.GetValue())
        self.db_list = [file for file in files if file.endswith(".db") and file != str(date.today()) + "_crawled.db"]
        self.db_list.append(str(date.today()) + "_crawled.db")
        self.db_list = sorted(self.db_list, reverse = True)
    
    # text color changing
    def changing_color(self, event):
        website = self.combo1.GetValue()
        latest = self.Rad1.GetValue()
        page_list = self.Rad2.GetValue()
        content = self.Rad3.GetValue()
        
        if website != "ALL":
            if latest:
                self.input2.SetForegroundColour(wx.BLACK)
                self.input3.SetForegroundColour(wx.LIGHT_GREY)
                self.input4.SetForegroundColour(wx.LIGHT_GREY)
            elif page_list:
                self.input2.SetForegroundColour(wx.LIGHT_GREY)
                self.input3.SetForegroundColour(wx.BLACK)
                self.input4.SetForegroundColour(wx.LIGHT_GREY)
            else:
                self.input2.SetForegroundColour(wx.LIGHT_GREY)
                self.input3.SetForegroundColour(wx.LIGHT_GREY)
                self.input4.SetForegroundColour(wx.BLACK)
    
    # default value setting
    def page_hint(self, event):
        website = self.combo1.GetValue()
        if website == "ALL":
            self.input2.SetForegroundColour(wx.LIGHT_GREY)
            self.input3.SetForegroundColour(wx.LIGHT_GREY)
            self.input4.SetForegroundColour(wx.LIGHT_GREY)
        else:
            self.changing_color(event)
            if website == "Bleeping_Computer":
                self.input2.SetValue("Latest n Pages(default 1) Crawling, n = ")
                self.input3.SetValue("https://www.bleepingcomputer.com/page/0/")
                self.input4.SetValue("https://www.bleepingcomputer.com/news/security/trickbot-updates-its-vnc-module-for-high-value-targets/")

            elif website == "iThome":
                self.input2.SetValue("Latest n Pages(default 1) Crawling, n = ")
                self.input3.SetValue("https://www.ithome.com.tw/security?page=1")
                self.input4.SetValue("https://www.ithome.com.tw/news/145496")

            elif website == "Three_cltn":
                self.input2.SetValue("n records (up to 300, default 1, all -1)fetching limit, n = ")
                self.input3.SetValue("None")
                self.input4.SetValue("https://3c.ltn.com.tw/news/45050")

            elif website == "Microsoft_SRC":
                self.input2.SetValue("Crawling n records from newest CVE(default 1, all -1), n = ")
                self.input3.SetValue("None")
                self.input4.SetValue("https://msrc.microsoft.com/update-guide/vulnerability/CVE-2021-34527")

            elif website == "The_Hacker_News":
                self.input2.SetValue("Latest n Pages Crawling(default 1), n = ")
                self.input3.SetValue("https://thehackernews.com/")
                self.input4.SetValue("https://thehackernews.com/2021/07/update-your-chrome-browser-to-patch-new.html")

# the initialize of wxPython
class App(wx.App):
    
    # the constructor of App
    def OnInit(self):
        frame = MyFrame()
        frame.Show()
        return True
    def OnExit(self):
        print("Exit the program.")
        return 0

# main
if __name__ == "__main__":
    app = App()
    app.MainLoop()


# In[ ]:




