import os

if not os.path.exists("ImageDatabase"):
    os.mkdir("ImageDatabase")
    
if not os.path.exists("hashes.txt"):
    open("hashes.txt", "w")

with open("requirements.txt", "r") as f:
    req = []
    for x in f.readlines():
        req.append(x.replace("\n", ""))
        
for x in req:
    os.system(f"python -m pip install {x}")

input("Press enter to close")