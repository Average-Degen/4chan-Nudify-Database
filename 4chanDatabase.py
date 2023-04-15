from urllib.request import urlopen, Request
from os.path import isfile, join
from bs4 import BeautifulSoup
from os import listdir
from lxml import etree
import requests
import hashlib
import string
import random
import shutil
import time
import os
import re


def CheckAllHashes():
    file_list = [f for f in listdir(
        images_path) if isfile(join(images_path, f))]

    hashes = []
    for file in file_list:
        with open(images_path + file, "rb") as f:
            hashes.append(hashlib.sha256(f.read()).hexdigest())

    StoreHashes(hashes)


def StoreHashes(hashes):
    with open(hash_file, "a") as f:
        for hash in hashes:
            f.write(hash + "\n")


def GetHash(file):
    with open(file, "rb") as f:
        return (hashlib.sha256(f.read()).hexdigest())


def CompareHashes(hash, file_name):
    # read hashes of other files
    cleaned_hashes = []
    with open(hash_file, "r") as f:
        hashes = f.readlines()
        for h in hashes:
            cleaned_hashes.append(h.replace("\n", ""))

    # compare the hashes
    if not hash in cleaned_hashes:
        # hash doesnt exist in database then add
        print("New Image Found!")
        StoreHashes([hash])
        shutil.copy(file_name, images_path + file_name)
    os.remove(file_name)


def DownloadImage(url):
    # create name for file
    letters = string.ascii_lowercase
    rand_name = ''.join(random.choice(letters) for i in range(20))

    img_data = requests.get(url).content
    with open(f'{rand_name}.jpg', 'wb') as f:
        f.write(img_data)

    CompareHashes(GetHash(rand_name + ".jpg"), rand_name + ".jpg")

def ImagesFromThread(thread_url):
    urls = []
    
    # get urls
    source = requests.get(thread_url)
    soup = BeautifulSoup(source.content, "html.parser")
    
    imgs = soup.find_all("a")
    for img in imgs:
        try:
            if "//i.4cdn.org/b/" in img["href"]:
                urls.append(img["href"])
        except:
            pass        
    
    # get prev urls this run
    with open("CheckedURLs.txt", "r") as f:
        prev_urls = f.readlines()
    
    prev_urls_cleaned = []
    # clean prev_urls
    for x in prev_urls:
        prev_urls_cleaned.append(x.replace("\n", ""))
    
    # test images
    for url in set(urls):
        if not url in prev_urls_cleaned:
            DownloadImage("https:" + url)
            AddCheckedURLs(url)

def AddCheckedURLs(url):
    with open("CheckedURLs.txt", "a") as f:
        f.write(url + "\n")

def FindNewThread():
    full_thread = ""
    new_thread = ""
    
    source = requests.get("https://boards.4chan.org/b/catalog")
    split_source = source.text.split("},")
    for x in split_source:
        if "nudify" in x.lower():
            # get url of thread/s
            thread_index = split_source.index(x)    
            id_index = split_source[thread_index -1]
            id = id_index.split(":")[0]
            id = id.replace('"', "")
            new_url = f"https://boards.4chan.org/b/thread/{id}"
            
            # check image count in thread
            img_count = re.search('"i":(.*)', id_index)
            if int(img_count.group(1).split(",")[0]) >= 150:
                full_thread = new_url
            else:
                new_thread = new_url
    # check which thread to return
    if new_thread == "" and full_thread != "":
        return full_thread
    elif new_thread != "":
        return new_thread
    else:
        print("No nudify thread found")
        print("Sleeping for 1 minute")
        time.sleep(60)
        return ""
    
images_path = "ImageDatabase\\"
hash_file = "hashes.txt"
has_URL = False

open("CheckedURLs.txt", "w")

while True:
    thread_url = FindNewThread()
    if thread_url == "":
        continue
    ImagesFromThread(thread_url)