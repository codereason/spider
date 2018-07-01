import json
import os
from urllib.parse import urlencode
import re
import pymongo
import requests
from bs4 import BeautifulSoup
import ast
from requests.exceptions import RequestException
from config import *
from hashlib import md5
from multiprocessing import Pool

client = pymongo.MongoClient(MONGO_URL,connect=False)
db = client[MONGO_DB]


def get_page_index(offset, keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': 20,
        'cur_tab': 1

    }
    url = "https://www.toutiao.com/search_content/?" + urlencode(data)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print("请求索引页出错")
        return None


def parse_page_index(html):
    data = json.loads(html)
    if data and 'data' in data.keys():
        for item in data.get('data'):
            yield item.get('article_url')


def get_page_detail(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print("请求详情页出错", url)
        return None


def parse_page_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')
    title = soup.select('title')[0].get_text()
    # print(title)
    image_pattern = re.compile('gallery: JSON.parse\((.*?)\),', re.S)
    result = re.search(image_pattern, html)
    if result:
        data = json.loads(result.group(1))
        data = ast.literal_eval(data)
        if data and 'sub_images' in data.keys():
            sub_images = data.get('sub_images')
            images = [item.get('url') for item in sub_images]
            for image in images:
                download_image(image)
            return {
                'title': title,
                'url': url,
                'images': images
            }


def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('saved to mongodb', result)
        return True


def download_image(url):
    print('正在下载', url.replace("\\", ''))
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36"
    }
    try:
        response = requests.get(url.replace("\\", ''), headers=headers)
        if response.status_code == 200:
            save_image(response.content)
        return None
    except RequestException:
        print("请求图片出错", url)
        return None


def save_image(content):
    file_path = '{0}/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()


def main(offset):
    html = get_page_index(offset, KEYWORD)
    for url in parse_page_index(html):
        html = get_page_detail(url)
        if html:
            result = parse_page_detail(html, url)
            if result: save_to_mongo(result)


if __name__ == '__main__':
    pool = Pool()
    pool.map(main, [i * 20 for i in range(START_OFFSET, END_OFFSET + 1)])
