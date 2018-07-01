import json
import os
from urllib.parse import urlencode
import re

import pymongo
import  requests
from bs4 import BeautifulSoup
import ast
from requests.exceptions import RequestException
from config import *
from hashlib import md5

def download_image(url):
    print('正在下载',url)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36"
    }
    try:
        response = requests.get(url,headers=headers)
        if response.status_code==200:
            save_image(response.content)
        return None
    except RequestException:
        print("请求图片出错",url)
        return None
def save_image(content):
    file_path = '{0}/{1}.{2}'.format(os.getcwd(),md5(content).hexdigest(),'jpg')
    if not os.path.exists(file_path):
        with open(file_path,'wb') as f:
            f.write(content)
            f.close()
url = "http:\\/\\/p3.pstatp.com\\/origin\\/pgc-image\\/1530272272064a0f431e420".replace("\\",'')
download_image(url)