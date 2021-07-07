from bs4 import BeautifulSoup
import requests
import time
import wordcloud
import numpy as np
from matplotlib import pyplot as plt

url = "https://www.gutenberg.org/files/36/36-0.txt"
page = requests.get(url)
file_contents = BeautifulSoup(page.text, 'html.parser')


def calculate_frequencies(file_contents):
    # Here is a list of punctuations and uninteresting words you can use to process your text
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
    uninteresting_words = ["for","the","in", "a", "to", "if", "is", "it", "of", "and", "or", "an", "as", "i", "me", "my", \
    "we", "our", "ours", "you", "your", "yours", "he", "she", "him", "his", "her", "hers", "its", "they", "them", \
    "their", "what", "which", "who", "whom", "this", "that", "am", "are", "was", "were", "be", "been", "being", \
    "have", "has", "had", "do", "does", "did", "but", "at", "by", "with", "from", "here", "when", "where", "how",'over','up','there','one','saw','towards','people', \
    "all", "any", "both", "each", "few", "more", "some", "such", "no", "nor", "too", "very", "can", "will", "just","not","on","into","out",'so','upon','about','came']
    
    # LEARNER CODE START HERE
    words =''
    dic={}
    file = str(file_contents).split()
    for word in file:
        if word.lower() not in uninteresting_words:
            for letter in word:
                if letter in punctuations:
                    letter.replace(punctuations,"")
            if word not in dic:
                dic[word]=0
            else:
                dic[word]+=1
    #wordcloud
    cloud = wordcloud.WordCloud()
    cloud.generate_from_frequencies(dic)
    return cloud.to_array()
# Display your wordcloud image

myimage = calculate_frequencies(file_contents)
plt.imshow(myimage, interpolation = 'nearest')
plt.axis('off')
plt.show()