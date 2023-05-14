from skimage.metrics import structural_similarity
from bs4 import BeautifulSoup
from art import tprint
from PIL import Image
import numpy as np
import imagehash
import requests
import shutil
import time
import cv2
import os

# unused function to write hash of all images in database folder
# def CheckAllHashes():
#     # get list of images
#     file_list = [f for f in listdir(
#         images_path) if isfile(join(images_path, f))]

#     # append every image to hashes file
#     hashes = []
#     for file in file_list:
#         if not "_NUDE" in file:
#             StoreHashes(imagehash.average_hash(
#                 Image.open(images_path + file)), file.split(".")[0])


# write hash to file
def StoreHashes(hash, file_name):
    with open(hash_file, "a") as f:
        f.write(str(hash) + ":" + file_name + "\n")


# check if hash is already stored
def IsHashStored(hash, name):
    # append hashes file contents to list
    cleaned_hashes = []
    with open(hash_file, "r") as f:
        hashes = f.readlines()
        for h in hashes:
            cleaned_hashes.append(h.replace("\n", ""))

    # compare the hashes
    hash_found = False
    for x in cleaned_hashes:
        if hash in x:
            hash_found = True
    if not hash_found:
        # add to database then return that it isn't already in database
        StoreHashes(hash, name)
        return True


# download image file from URL
def DownloadImage(url, name):
    img_data = requests.get(url).content
    with open(f'{name}', 'wb') as f:
        f.write(img_data)
    AddCheckedURL(url)


# add URL to list of previously checked
def AddCheckedURL(url):
    with open("CheckedURLs.txt", "a") as f:
        f.write(url + "\n")


# find a thread to pull from
def FindThread():
    threads = []

    source = requests.get("https://boards.4chan.org/b/catalog")
    split_source = source.text.split("},")
    for x in split_source:
        if "nudify" in x.lower():
            # get url of thread/s
            thread_index = split_source.index(x)
            id_index = split_source[thread_index - 1]
            id = id_index.split(":")[0]
            id = id.replace('"', "")
            thread_url = f"https://boards.4chan.org/b/thread/{id}"
            threads.append(thread_url)
    return threads
    

# check if images are related
# credit nathancy & bfontaine - stackoverflow
def DetectSimilar(file_name):
    for test_num in range(2):
        first = cv2.imread(f'{file_name}.jpg')
        second = cv2.imread(f'{file_name}_NUDE.jpg')

        # resize to uniform scale
        first = cv2.resize(first, (512, 512))
        second = cv2.resize(second, (512, 512))
        
        h1, w1 = first.shape[:2]
        
        if test_num == 1:
            # divide the images into segments of 50x50 pixels
            segments1 = []
            segments2 = []
            for r in range(0, h1, 64):
                for c in range(0, w1, 64):
                    # crop the segments from the images
                    segment1 = first[c:c+64, r:r+64]
                    segment2 = second[c:c+64, r:r+64]
                    # append the segments to the lists
                    segments1.append(segment1)
                    segments2.append(segment2) 
            
            loop_num = range(len(segments1))
        else:
            loop_num = 1
            
        for x in range(loop_num):
            # convert images to grayscale
            if test_num == 1:
                first_gray = cv2.cvtColor(segments1[x], cv2.COLOR_BGR2GRAY)
                second_gray = cv2.cvtColor(segments2[x], cv2.COLOR_BGR2GRAY)
            else:
                first_gray = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
                second_gray = cv2.cvtColor(second, cv2.COLOR_BGR2GRAY)
            # Compute SSIM between two images
            score, diff = structural_similarity(first_gray, second_gray, full=True)

            # The diff image contains the actual image differences between the two images
            # and is represented as a floating point data type so we must convert the array
            # to 8-bit unsigned integers in the range [0,255] before we can use it with OpenCV
            diff = (diff * 255).astype("uint8")

            # Threshold the difference image, followed by finding contours to
            # obtain the regions that differ between the two images
            thresh = cv2.threshold(
                diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            contours = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = contours[0] if len(contours) == 2 else contours[1]
            
            if test_num == 1:
                if score*100 >= 98:
                    return True
            else:
                if score*100 >= 40:
                    return True
    return False
 
# check if URL has been checked previously
def HasBeenChecked(url):
    prev_urls = []
    with open("CheckedURLs.txt", "r") as f:
        for x in f.readlines():
            prev_urls.append(x.replace("\n", ""))
    return url in prev_urls


# find all potential nudifies & originals 
def FindPosts(url):
    source = requests.get(url)
    soup = BeautifulSoup(source.content, "html.parser")

    # get posts in thread
    posts = soup.find_all("div", class_="post")
    for post in posts:
        # find if post is a reply
        quote = post.find("blockquote", class_="postMessage")
        try:
            nfy_ref = quote.find("a", class_="quotelink")["href"]
        except:
            continue

        # find if post contains image
        try:
            nfy_img = post.find("a", class_="fileThumb")["href"]
        except:
            continue

        # find image from original post
        reffed = soup.find_all(class_="post")
        for post in reffed:
            try:
                if post["id"] == nfy_ref.replace("#", ""):
                    orig_img = post.find("a", class_="fileThumb")["href"]
            except:
                continue

        try:
            nfy_checked = HasBeenChecked("https:" + nfy_img)

            if not nfy_checked:
                try:
                    # download requested image
                    DownloadImage(
                        url="https:" + orig_img,
                        name=nfy_ref.replace("#p", "") + ".jpg"
                    )

                    # download nudified version
                    DownloadImage(
                        url="https:" + nfy_img,
                        name=nfy_ref.replace("#p", "") + "_NUDE.jpg"
                    )

                    path = nfy_ref.replace("#p", "")

                    # if images are related
                    similarity = DetectSimilar(nfy_ref.replace("#p", ""))
                    if similarity:
                        hash = str(imagehash.average_hash(Image.open(path + ".jpg")))
                        is_new = IsHashStored(hash, path)
                        if is_new:
                            shutil.copy(path + ".jpg",
                                        f"ImageDatabase\\{path}.jpg")
                            shutil.copy(path + "_NUDE.jpg",
                                        f"ImageDatabase\\{path}_NUDE.jpg")
                            
                            os.remove(nfy_ref.replace("#p", "") + ".jpg")
                            os.remove(nfy_ref.replace("#p", "") + "_NUDE.jpg")

                            # find and store user that nudified unless anon
                            try:
                                name = post.find("span", class_="name").text
                                
                                if not os.path.exists("NudifierList.txt"):
                                    open("NudifierList.txt", "w")
                                    
                                with open("NudifierList.txt", "a") as f:
                                    f.write(path + ":" + name + "\n")
                            except:
                                print("Poster not found!")
                                pass
                            
                            print("Image pair added to database!")
                        else:
                            # save the repost for image feed
                            shutil.copy(path + ".jpg",
                                        f"ImageDatabase\\{path}.jpg")
                            shutil.copy(path + "_NUDE.jpg",
                                        f"ImageDatabase\\{path}_NUDE.jpg")
                            
                            os.remove(nfy_ref.replace("#p", "") + ".jpg")
                            os.remove(nfy_ref.replace("#p", "") + "_NUDE.jpg")
                    else:
                        pass
                except:
                    # one of them didnt have an image and I'm lazy
                    pass
                os.remove(nfy_ref.replace("#p", "") + ".jpg")
                os.remove(nfy_ref.replace("#p", "") + "_NUDE.jpg")
        except:
            pass


images_path = "ImageDatabase\\"
hash_file = "hashes.txt"

open("CheckedURLs.txt", "w")

if __name__ == "__main__":    
    while True:
        # clear output
        os.system('cls' if os.name == 'nt' else 'clear')

        tprint("AVERAGE     DEGEN")
        print("**DO NOT CLOSE PROGRAM UNTIL TOLD SO**")
        print()

        # find thread and check if it valid
        threads = FindThread()
        for t in threads:
            if "!DOCTYPE" in t or t == "":
                continue
            print()
            print("Accessing thread: " + t)

            FindPosts(t)

        print()
        print("Sleeping for 30 seconds")
        print("Program can be safely closed if desired")
        print("---------------------------------------------------------------")
        time.sleep(30)
