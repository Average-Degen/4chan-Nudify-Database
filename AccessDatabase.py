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
    hashes = []
    for x in f.readlines():
        hashes.append(imagehash.hex_to_hash(x.replace("\n", "")))
        
for x in hashes:
    if (x-input_hash) <= 2:
        print("Image found in database")

    