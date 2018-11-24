from __future__ import unicode_literals
from .models import Urls, Keywords_Count, Keywords_Search
from background_task import background
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
from django.conf import settings
import requests
from urllib import request
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from bs4 import BeautifulSoup

from math import log



def cal_tf(kword, url):
    k = Keywords_Count.objects.get(keyword = kword, url = url)
    count = k.count
    ke = Urls.obejects.get(url = url)
    count_doc = ke.count
    tf = count/count_doc
    return tf


def cal_idf(kword):
     count_word_col = Keywords_Count.objects.filter(keyword = kword).count() #no of documents containing keyword
     len_col = Urls.objects.all().count() #no of total documents in db
     idf = log(len_col/count_word_col)
     return idf

@csrf_exempt
def index(keywords,page):
    dict={}
    mystr = page.get_text()
    wordList = re.sub("[^\w]", " ", mystr).split()

    for word in wordList:
        word = word.lower()
        if word in keywords:
            #print(word)
            if word not in dict:
                dict[word] = 1
            else:
                dict[word] = dict[word] + 1
        #print(dict)

    return dict


def crawl(visited_link, links, keywords, depth):
    if depth == 2:
        return {}
    print(visited_link)
    new_links=[]
    dict1={}
    for link in links:

        if link not in visited_link:
            visited_link.append(link)

           # print(link)
            dict3 = link.split(".")
            if "pdf" in dict3:
                continue
            try:
                page = requests.get(link)


                # if requests.head(link).headers['Content-Type'] == "application/pdf":
                #     pass
                if page.status_code==200:
                    page = BeautifulSoup(page.text, "lxml")
                    [x.extract() for x in page.findAll(['script', 'style'])]
                    page1 = page.text.split()
                    doc_count = len(page1)
                    dict = {}
                    dict.update(index(keywords,page))
                    #print(dict)
                    if len(dict)!=0:
                        dict1[link]=dict
                        #print(dict1)
                        if depth+1 == 2:
                            continue
                        if depth == 1:
                            for key in page.find_all("a", {'target': '_blank', 'rel': 'noopener'}):
                                link = key.get('href')
                                if link not in new_links and links:
                                    new_links += [link]
                        else:
                            for key in page.find_all("a"):
                                link = key.get('href')
                                if link not in new_links and links:
                                    new_links += [link]
            except Exception as error:
                pass

    print(len(dict1))
    print(dict1)
    dict1.update(crawl(visited_link,new_links,keywords,depth+1))
    return dict1

@csrf_exempt
# Create your views here.
def show_form(request):
    template = loader.get_template('get_query.html')
    return HttpResponse(template.render())
@csrf_exempt

def find_results(query):
    query1 = query.replace(" ", '+')
    req = requests.get('http://api.springernature.com/metadata/json?q=keyword:' + query1 + "&api_key=" + settings.SPRINGER_KEY)
    req = req.json()
    #
    length = len(req['records'])

    result = []
    for i in range(0, length - 1):
        result += [req['records'][i]['url'][0]['value']]

    # extract all pages_object and keywords

    keywords = []
    links = [] + result
    visited_links = []

    for i in range(0, length - 1):
        page = requests.get(result[i])
        if page.status_code == 200:
            soup = BeautifulSoup(page.text, 'html.parser')
            for key in soup.find_all("span", {'class': 'Keyword'}):
                start = 0
                end = len(key.get_text()) - 1
                keyword = key.get_text()[start:end].lower()
                if keyword not in keywords:
                    keywords += [keyword]

    for keyword in keywords:
        try:
            key=Keywords_Search.objects.get(keyword=keyword)
        except Exception as error:
            key=Keywords_Search(keyword=keyword,search=False)
            key.save()
                # print(keywords)

    dict = {}
    dict.update(crawl(visited_links, links, keywords, 1))
    for key in dict.keys():
        urlv = dict[key]
        for word in urlv.keys():
            count = urlv[word]
            try:
                durls = Urls.objects.get(url=key)
            except Exception as error:
                soup = BeautifulSoup(request.urlopen(key))
                ti = soup.title.string
                page = requests.get(key)
                if page.status_code==200:
                    page = BeautifulSoup(page.text, "lxml")
                    [x.extract() for x in page.findAll(['script', 'style'])]
                    page1 = page.text.split()
                    doc_count = len(page1)
                #print(word+": "+ti)
                durls = Urls(url=key,title=ti,count=doc_count)
                durls.save()
                durls = Urls.objects.get(url=key)

            dword = Keywords_Search.objects.get(keyword=word)

            try:
                da=Keywords_Count.objects.get(keyword=dword,url=durls)
            except Exception as error:
                #initially count store
                count_td = cal_tf(dword,durls)
                da=Keywords_Count(keyword=dword,url=durls,count=count,tf_idf= count_td)
                da.save()
        if query not in urlv.keys():
            durls = Urls.objects.get(url=key)
            dword = Keywords_Search.objects.get(keyword=query)
            try:
                da=Keywords_Count.objects.get(keyword=dword,url=durls)
                print(da)
            except Exception as error:
                da=Keywords_Count(keyword=dword,url=durls,count=1)
                da.save()



@background(schedule=1)
def find_results1():

    while True:
        while len(list)==0:
            query_set = Keywords_Search.objects.all()
            list = []
            for query in query_set:
                list.append(query.keyword)
            list1 = []

        while len(list):
           # print(list)
            for word in list:
                 k = Keywords_Search.objects.get(keyword = word)
                 if(k.search == False):
                      print(word)
                      find_results(word)
                      k.search = True
                      k.save()

            query_set= Keywords_Search.objects.all()
            list2 = []
            for query in query_set:
                list2.append(query.keyword)
            list1.append(list)
            list =list2[len(list1):len(list2)]
            #list = [ x for x in list2 if not in list1]






def get_data(request):
    if request.method == 'POST':
        query = request.POST.get('q')
        query = query.lower()
        # REMOVE EXTRA SPACES
        query = query.strip()
        query = re.sub(' +', ' ', query)
        list = []
        list1 =[]
        ad=0
        if(len(query) == 0):
            return render(request, 'get_query.html', )
        else:
            stop_words = set(stopwords.words('english'))
            word_tokens = word_tokenize(query)
            filtered_query = []
            for w in word_tokens:
                if w not in stop_words:
                    filtered_query.append(w)
            query = ''
            for w in filtered_query:
                query = query + " " + w
            query = query.strip()
        #I am updating my column values for valid url
        try:
            key=Keywords_Search.objects.get(keyword=query)
            if key.search:
                print(query)
                list3 = Keywords_Count.objects.all().filter(keyword=query).order_by('-tf-idf')
                print(len(list3))
                for key in list3:
                    list += [key.url.url]
                    list1 += [key.url.title]
            else:
                ad = 1
        except Exception as error:
            p = Keywords_Search(keyword=query,search=False)
            p.save()
            ad=1
        if ad==1:
            print("hgjh")
            query=query.replace(' ','+')
            req = requests.get("http://api.springernature.com/metadata/json?q=keyword:" + query + "&p=100&api_key=a22eb2a96a01b2bbd164fc11ca2f07a3")
            req = req.json()
            length = len(req['records'])
            # extract all urls
            for i in range(0, length - 1):
                list += [req['records'][i]['url'][0]['value']]
                list1 += [req['records'][i]['title']]
        list = zip(list, list1)
         #Filter and save them in a list and show
        template = loader.get_template('show_result.html')
        return HttpResponse(template.render({'data':list}, request))
    else:
        template = loader.get_template('get_query.html')
        return HttpResponse(template.render())
