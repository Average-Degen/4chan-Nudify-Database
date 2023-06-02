from discord.ext import commands
from collections import Counter
from io import BytesIO
from PIL import Image
import imagehash
import discord
import aiohttp
import aiofiles
import asyncio
import os

###################### TOKEN ######################
TOKEN = ""
###################################################

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", intents=intents)

curr_dir = os.getcwd()
hash_dir = os.path.dirname(curr_dir)

async def CheckURL(url):
    try:
        # get img from url
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    img_bytes = await response.read()
                    img = Image.open(BytesIO(img_bytes))
    except:
        pass

    # hash value from input string
    in_hash = imagehash.average_hash(img)

    # get hashes list
    hashes_list = []
    file_list = []
    
    with open(f"{hash_dir}\\hashes.txt", "r") as f:
        for x in f.readlines():
            file_list.append(x.split(":")[1])
            hashes_list.append(imagehash.hex_to_hash(x.split(":")[0]))

    # compare all hashes against input
    for x in hashes_list:
        if (x-in_hash) <= 2:
            ind = hashes_list.index(x)
            return file_list[ind]
    return "None"

async def statusTask():
    try:
        channel = bot.get_channel(1099635954832125982)
    except:
        pass
    while True:
        
        with open(hash_dir + "\\hashes.txt", "r") as f:
            hashes_count = len(f.readlines())
        
        try:
            await channel.edit(name=str(hashes_count) + "-unique-images")
        except:
            pass
        
        await asyncio.sleep(333)
        
async def imageFeed():
    while True:
        try:
            channel = bot.get_channel(1106542353587638392)
        except:
            pass
        
        if not os.path.exists("UploadedList.txt"):
            open("UploadedList.txt", "w")
        
        images = list(os.listdir(hash_dir + "\\ImageDatabase"))
        
        uploaded_files = []
        with open("UploadedList.txt", "r") as f:
            for x in f.readlines():
                uploaded_files.append(x.replace("\n", ""))
        
        async with aiofiles.open("UploadedList.txt", "a+") as f:
            for x in images:
                if not "_NUDE" in x:
                    if not x in uploaded_files:
                        nudified_x = x.split(".")[0] + "_NUDE.jpg"
                        x_dir = hash_dir + "\\ImageDatabase\\"
                        await f.write(x + "\n")
                        await channel.send(files=[discord.File(x_dir + x), discord.File(x_dir + nudified_x)])
                    
        await asyncio.sleep(15)
    
async def LeaderBoard():
    while True:
        channel = bot.get_channel(1106537597435662378)
        
        nudifiers = []
        async with aiofiles.open(hash_dir + "\\NudifierList.txt", "r") as f:
            for x in await f.readlines():
                try:
                    nudifiers.append(str(x.replace("\n", "").split("<:>")[1]))
                except:
                    continue
        
        ordered_common = [item for items, c in Counter(nudifiers).most_common() for item in [items] * c]
        
        leaderboard = []
        for x in ordered_common:
            if not x + ": " + str(ordered_common.count(x)) in leaderboard:
                leaderboard.append(x + ": " + str(ordered_common.count(x)))
        
        leaderboard_str = ""
        for x in leaderboard:
            leaderboard_str += str(leaderboard.index(x) + 1) + ". " + x + "\n"
        
        try:
            msg = await channel.fetch_message(channel.last_message_id)
            await msg.edit(content=leaderboard_str)
        except:
            await channel.send(leaderboard_str)
        
        await asyncio.sleep(30)

@bot.event
async def on_ready():
    print("logged in as {0.user}".format(bot))
    await bot.change_presence(activity=discord.Game("?check <url>"))
    bot.loop.create_task(statusTask())
    bot.loop.create_task(imageFeed())
    bot.loop.create_task(LeaderBoard())

@bot.command()
async def hello(ctx):
    await ctx.channel.send(ctx.author.mention + "\nm'lady :wink:")
    
@bot.command()
async def check(ctx, arg):
    ret = await CheckURL(arg)
    if ret == "None":
        await ctx.channel.send(ctx.author.mention + "\nImage not in database")
    else:
        #await ctx.channel.send(ctx.author.mention + "\nImage found in database")
        with open(hash_dir + "\\ImageDatabase\\" + ret.replace("\n", "") + "_NUDE.jpg", 'rb') as f:
            nfy_img = discord.File(f)
            nfy_img.filename = "SPOILER_" + nfy_img.filename
            await ctx.channel.send(ctx.author.mention + "\nImage found in database", file=nfy_img)     

bot.run(TOKEN)
