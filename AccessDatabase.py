from io import BytesIO
from PIL import Image
import imagehash
import requests

path = input("Image path/URL: ")

if "https://" in path:
    response = requests.get(path)
    img = Image.open(BytesIO(response.content))
    input_hash = imagehash.average_hash(img)
else:
    input_hash = imagehash.average_hash(Image.open(path))

with open("hashes.txt", "r") as f:
    hashes_txt = f.readlines()
    clean_hashes = []
    for x in hashes_txt:
        clean_hashes.append(imagehash.hex_to_hash(x.split(":")[0]))
    
        
for x in clean_hashes:
    if (x-input_hash) <= 2:
        for i in hashes_txt:
            if str(x) in i:
                full_hash = i
        file_name = i.split(":")[1].replace("\n", "")
        print("Image found in database")
        print(file_name + ".jpg")

    