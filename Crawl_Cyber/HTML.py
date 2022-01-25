#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import sqlite3 as lite
import os
import datetime
from collections import defaultdict
def get_key(dict,value):
            return [k for k,v in dict.items() if v ==value]
    
class Generative_HTML():
    
    def __init__(self, database, path):
        self.conn = lite.connect(database)
        self.path = path
        self.table_name_list = []
        
        with self.conn:
            cur = self.conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            table = cur.fetchall()
            for i in table:
                self.table_name_list.append(i[0])
            
# table [('Windows 10',), ('Vmware vCenter 6.5',), ('Vmware vCenter 6.7',), ('Chrome 90',), ('Check point R80.10',), ('群 暉 NAS ',), ('Synology NAS ',), ('QNAP NAS ',), ('ransom 勒索 ',), ('CVE ',)]
         
        check_repeat = {}
        num=0
        pd.set_option('display.width', 1800)
        pd.set_option('colheader_justify', 'center')   # FOR TABLE <th>
        html_string = '''
        <html>
          <head><title>HTML Pandas Dataframe with CSS</title>
              <style>
                  .my body{{
                      font-size: 23pt; 
                      font-family: Arial;
                      width:1800px;
                      border-collapse: collapse; 
                      border: 1px solid silver;
                  }}
                  .my tr{{
                      width:300px;
                  }}
                  .my th{{
                      padding: 5px;
                      width : 100px;
                  }}
                  .my td{{
                      padding: 5px;
                      width : 450px;
                  }}
                  .my tr:nth-child(even) {{
                      background: #E0E0E0;
                  }}
                  .my a:hover {{
                      background: silver;
                      cursor: pointer;
                  }}
                  
              </style>
          </head>
          <link rel="stylesheet" type="text/css" href="../df_style.css"/>
          <body>
              {table}
          </body>
        </html>
        '''
        for i in self.table_name_list:
            cts = pd.read_sql_query(f"SELECT * FROM [{i}]", self.conn)
            
            check_repeat[i]=[]
            for k in range(len(cts['url'])):
                check_repeat[i].append(cts.loc[k,'url'])
        new_dict={}
        
        
        for k, v in check_repeat.items():
            for value in v:
                new_dict.setdefault(value, []).append(k)
        for k,v in new_dict.items():
            v = list(set(v))
            new_dict[k]=v
#        print(new_dict)
        check=[]
#https://thehackernews.com/2021/11/blackmatter-ransomware-reportedly.html': ['ransom 勒索 ', 'Vmware vCenter 6.7', 'Vmware vCenter 6.5']
        for i in self.table_name_list:
            cts = pd.read_sql_query(f"SELECT * FROM [{i}]", self.conn)
            # we no longer using "content" column
            cts = cts.drop_duplicates(keep='first')
            cts = cts.reset_index()
            cts_drop = cts.drop("content", axis = 1)
            
            for j in range(len(cts)):
                list_of_key = new_dict[cts.loc[j,'url']]
                list_of_key = '+'.join(list_of_key)
              
                if cts_drop.loc[j]['url'] in check:
                    print('continue',cts_drop.loc[j]['url'])
                    continue
                else:
                    check.append(cts_drop.loc[j]['url'])
#                 print('\nelse', cts_drop.loc[j]['url'])
#                 print(cts_drop.loc[j])
#                 result = cts_drop.loc[j].to_frame().T.to_html(render_links=True, escape = False)
                result = html_string.format(table=cts_drop.loc[j].to_frame().T.iloc[:,1:].to_html(render_links=True, escape = False,classes='my'))
#                 print(result)
                if (len(new_dict[cts_drop.loc[j,'url']]) >=2) & ('CVE ' in new_dict[cts_drop.loc[j,'url']]):
                    with open(fr"{self.path}\\..{list_of_key}.html", "a", encoding = "utf-8") as html:
                        html.write(result)
                        cts_drop = cts_drop.drop(cts_drop[cts_drop['url']==cts.loc[j,'url']].index)
                elif len(new_dict[cts_drop.loc[j,'url']]) >=2:
                    with open(fr"{self.path}\\.{list_of_key}.html", "a", encoding = "utf-8") as html:
                        html.write(result)
                        cts_drop = cts_drop.drop(cts_drop[cts_drop['url']==cts.loc[j,'url']].index)
                        
                else:
#                     with open(fr"{self.path}\\{list_of_key}.html", "w", encoding = "utf-8") as html:
#                         result = cts_drop.to_html(render_links=True, escape = False)
#                         html.write(result)
                    if list_of_key == 'Chrome 90':
                        continue
                    else:
                        with open(fr"{self.path}\\{list_of_key}.html", "a", encoding = "utf-8") as html:
                            html.write(result)
                            cts_drop = cts_drop.drop(cts_drop[cts_drop['url']==cts.loc[j,'url']].index)
                        
          
        
