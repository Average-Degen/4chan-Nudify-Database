from skimage.metrics import structural_similarity
from os.path import isfile, join
from bs4 import BeautifulSoup
from os import listdir
import numpy as np
import requests
from art import tprint
import hashlib
import string
import random
import shutil
import time
import cv2
import os
import re

tprint("PROGRAM     LOADED")

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
        StoreHashes([hash])
        return True

def DownloadImage(url, name):
    img_data = requests.get(url).content
    with open(f'{name}', 'wb') as f:
        f.write(img_data)
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
            if int(img_count.group(1).split(",")[0]) >= 145:
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

# credit nathancy & bfontaine - stackoverflow 
def DetectSimilar(file_name):
    first = cv2.imread(f'{file_name}.jpg')
    second = cv2.imread(f'{file_name}_NUDE.jpg')

    first = cv2.resize(first, (512, 512))
    second = cv2.resize(second, (512, 512))

    # Convert images to grayscale
    first_gray = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
    second_gray = cv2.cvtColor(second, cv2.COLOR_BGR2GRAY)

    # Compute SSIM between two images
    score, diff = structural_similarity(first_gray, second_gray, full=True)
    #print("Similarity Score: {:.3f}%".format(score * 100))

    # The diff image contains the actual image differences between the two images
    # and is represented as a floating point data type so we must convert the array 
    # to 8-bit unsigned integers in the range [0,255] before we can use it with OpenCV
    diff = (diff * 255).astype("uint8")

    # Threshold the difference image, followed by finding contours to
    # obtain the regions that differ between the two images
    thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    # Highlight differences
    mask = np.zeros(first.shape, dtype='uint8')
    filled = second.copy()

    for c in contours:
        area = cv2.contourArea(c)
        if area > 100:
            x,y,w,h = cv2.boundingRect(c)
            cv2.rectangle(first, (x, y), (x + w, y + h), (36,255,12), 2)
            cv2.rectangle(second, (x, y), (x + w, y + h), (36,255,12), 2)
            cv2.drawContours(mask, [c], 0, (0,255,0), -1)
            cv2.drawContours(filled, [c], 0, (0,255,0), -1)
    
    # window displaying differences  
    # cv2.imshow('diff', diff)
    # cv2.waitKey()
    
    return score*100

def FindReferences(url):
    # get previously check URLs
    prev_urls = []
    with open("CheckedURLs.txt", "r") as f:
        prev_urls = f.readlines()
    
    source = requests.get(url)
    soup = BeautifulSoup(source.content, "html.parser")
    
    # get posts in thread
    posts = soup.find_all("div", class_="post")
    for post in posts:
        has_ref = False
        has_img = False
        
        # find if post refs other post
        quote = post.find("blockquote")
        try:
            ref = quote.find("a")["href"]
            has_ref = True
        except:
            has_ref = False
            pass
        
        # find if post contains image
        try:
            img = post.find("a", class_="fileThumb")["href"]
            has_img = True
        except:
            has_img = False
            pass
        
        
        # if image is nudified reply
        if has_ref and has_img:
            # create name for files
            letters = string.ascii_lowercase
            rand_name = ''.join(random.choice(letters) for i in range(20))
            
            
            # download referenced non-nude image
            reffed = soup.find_all(class_="post")
            for post in reffed:
                try:
                    if post["id"] == ref.replace("#", ""):
                        img_url = post.find("a", class_="fileThumb")["href"]
                except:
                    pass   
            try:
                if not "https:" + img_url in prev_urls and not "https:" + img in prev_urls:
                    try:
                        # download requested image
                        DownloadImage(
                            url = "https:" + img_url,
                            name = ref.replace("#p", "") + ".jpg"
                        )
                        
                        # download nudified version
                        DownloadImage(
                            url = "https:" + img,
                            name = ref.replace("#p", "") + "_NUDE.jpg"
                            )
                        
                        path = ref.replace("#p", "")

                        nudify_is_new = CompareHashes(GetHash(path + "_NUDE.jpg"), path + "_NUDE.jpg")
                        
                        if nudify_is_new:
                            # if images are related
                            similarity = DetectSimilar(ref.replace("#p", ""))
                            if  similarity >=50:
                                shutil.copy(path + ".jpg", f"ImageDatabase\\{path}.jpg")
                                shutil.copy(path + "_NUDE.jpg", f"ImageDatabase\\{path}_NUDE.jpg")
                                # print(similarity)
                                # print(ref.replace("#p", ""))
                                # print("https:" + img_url) # original
                                # print("https:" + img) # nudified
                                # print("-------------------------------------------------")
                            else:
                                # print("Removed: " + ref.replace("#p", "") + ".jpg")
                                # print("-------------------------------------------------")
                                pass
                        os.remove(ref.replace("#p", "") + ".jpg")
                        os.remove(ref.replace("#p", "") + "_NUDE.jpg")
                    except:
                        # one of them didnt have an image and I'm lazy
                        pass
            except:
                # the amount of nested loops/error handlers is getting scary now
                pass
            
        
images_path = "ImageDatabase\\"
hash_file = "hashes.txt"
has_URL = False

open("CheckedURLs.txt", "w")

while True:
    thread_url = FindNewThread()
    if thread_url == "":
        continue
    print("Accessing thread: " + thread_url)
    FindReferences(thread_url)