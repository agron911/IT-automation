#!/usr/bin/env python
# coding: utf-8

# In[1]:


import smtplib
import os
import datetime
import mimetypes
import base64

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header

class Email():
    
    def __init__(self, directory, sender, recipient, producible):
        
        self.directory = directory
        self.producible = producible
        self.msg = MIMEMultipart()
        self.msg['Subject'] = "Automatic Information Security Warning."
        self.msg['From'] = sender
        self.msg['To'] = ", ".join(recipient)
        
        if self.producible:
            if len(os.listdir(self.directory)) == 0:
                self.msg.attach(MIMEText("There is no new analyzed data/html.", "plain", "utf-8"))
            else:
#                 self.msg.attach(MIMEText("There were two empty mail sent to you, please ignore it. Now the error is fixed ", "plain", "utf-8"))
                self.msg.attach(MIMEText("The Analyzed Htmls of Automatic Information Security Warning.", "plain", "utf-8"))
                for filename in os.listdir(self.directory):
                    path = os.path.join(self.directory, filename)
                    if not os.path.isfile(path):
                        continue
                    
                    ctype, encoding = mimetypes.guess_type(path)
                    if ctype is None or encoding is not None:
                        ctype = "application/octet-stream"
                    maintype, subtype = ctype.split("/", 1)
                    
                    fname = os.path.basename(path)

                    with open(path, 'rb') as fp:
                        att = MIMEBase(maintype, subtype)
                        att.set_payload(fp.read())
                        encoders.encode_base64(att)
                        att.add_header('Content-Disposition', 'attachment', filename = (Header(fname, 'utf-8').encode()))
                        self.msg.attach(att)
        else:
            self.msg.attach(MIMEText("There is no new analyzed data/html.", "plain", "utf-8"))
            
    def sending(self):
        s = smtplib.SMTP("10.1.254.112")
        s.send_message(self.msg)
        s.quit()

