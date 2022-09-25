import os
import time
from itertools import cycle

import nextcord
import pymongo
import jedi

from nextcord.ext import tasks
from table2ascii import table2ascii as t2a, PresetStyle
import flask

from Buddy_Reading import BuddyRead


# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By

# selenium chrome driver for emulating button-clicking
# chrome_options = webdriver.ChromeOptions()
# chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
# chrome_options.add_argument("--headless")
# chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.add_argument("--no-sandbox")
# chrome_options.add_experimental_option("detach", True)
# s = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH"))
# driver = webdriver.Chrome(service=s, options=chrome_options)
# # driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)
# REPLIT_URL = os.environ['REPLIT_URL']

intents = nextcord.Intents.default()
client = nextcord.Client(intents=intents)

# gif variables
tenor_str = "https://tenor.com/view/"
send_gif = f"{tenor_str}harry-potter-hedwig-4privet-drive-deathly-hallows-battle-of-the-seven-potters-gif-14134385"
receive_gif = f"{tenor_str}youve-got-mail-mail-get-the-mail-package-what-a-hoot-gif-18029581"
hot_damn_gif = f"{tenor_str}captain-ray-holt-hot-damn-hot-damn-brooklyn-nine-nine-gif-12390401"


# status variable changing status of discord bot
status = cycle(['with Python', 'JetHub'])


# MongoDB server details
conn_str = os.environ['uri']
cluster = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)  # set a 5-second connection timeout
db = cluster["HedwigDB"]
collection = db["BRProgress"]
try:
    print(cluster.server_info())  # prints sever info is connection works
except Exception:
    print("Unable to connect to the server.")


async def change_status_to_default():
    await client.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching,
                                                            name='BR progress on Book Servers'))


#
# async def change_status_to_command(username):
#     await client.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.listening,
#                                                             name=f"{username}'s command"))


@tasks.loop(seconds=300)
async def change_status():
    await client.change_presence(activity=nextcord.Game(next(status)))


@client.event
async def on_message(message):
    author_name = message.author.name
    channel_id = message.channel.id
    author_id = message.author.id
    author_id_str = str(author_id)

    if message.author == client.user:  # For ignoring bots messages
        return

    if message.content.startswith("!br update "):
        await client.change_presence(
            activity=nextcord.Activity(
                type=nextcord.ActivityType.listening,
                name=f"{message.author.name}'s command"))

        progress_msg = message.content[11:]
        temp = progress_msg

        if '/' in progress_msg:
            pg = temp.split('/')
            progress_msg = round((int(pg[0]) / int(pg[1])) * 100, 2)

        if int(progress_msg) > 100:
            await message.channel.send("Progress should be less than are equal to 100")
            await change_status_to_default()
            return

        try:
            if int(progress_msg) >= 100:
                pass
        except:
            await message.channel.send("Progress should be a number")
            await change_status_to_default()
            return

        if int(progress_msg) == 100:
            await message.channel.send("Well Done!")
            time.sleep(2)

        br_details = {author_id_str: {
            'username': author_name,
            'BRprogress': int(progress_msg)
        }}
        br_data_dict = {
            "_id": channel_id,
            "name": client.get_channel(channel_id).name,
            "br-details": br_details
        }
        try:
            collection.insert_one(br_data_dict)
        except:
            search_query = {"_id": channel_id}
            update_query = {"$set": {
                f"br-details.{author_id_str}.BRprogress": progress_msg,
                f"br-details.{author_id_str}.username": author_name
            }}
            collection.update_one(filter=search_query, update=update_query)

        await message.channel.send(f"{author_name}'s progress for this buddy-read is set to {progress_msg}%")
        await change_status_to_default()

    #
    if message.content.startswith("!br status"):
        await client.change_presence(
            activity=nextcord.Activity(
                type=nextcord.ActivityType.listening,
                name=f"{message.author.name}'s command"))

        msg = await message.channel.send(send_gif)
        time.sleep(5)
        await msg.edit(receive_gif)
        time.sleep(3)
        await msg.delete()

        search_query = {"_id": channel_id}
        try:
            brtable_dict = collection.find(search_query)[0]
        except:
            await message.channel.send("Buddy Read Data for this channel doesn't exist")
            await change_status_to_default()
            return

        brtable = []
        for user_id in brtable_dict["br-details"]:
            user = await client.fetch_user(int(user_id))
            brprogress_var = brtable_dict["br-details"][user_id]['BRprogress']
            brtable.append([user.name, brprogress_var])
            time.sleep(0.2)

        # brtable.sort(key=lambda x: x[1], reverse=True)
        # brtable = sorted(brtable, key = lambda x: x[1],reverse=True)
        output = t2a(header=["Username", "% Progress"], body=brtable, style=PresetStyle.thin_compact)
        await message.channel.send(f"```{output}```")
        await change_status_to_default()



    mess = message.content
    username = message.author

    # Searches for the book on goodreads and sends an embed message
    if mess.strip(" \n").lower().startswith("!b"):
        mess = mess.strip(" \n").lower()
        try:
            temp = eval(BuddyRead(mess.strip(), username)())
            print(temp)
            embed = nextcord.Embed.from_dict(temp["embeds"][-1])
        except Exception as exc_:
            await message.channel.send(
                "Sorry, couldn't process Book request. Exception: {}"
                .format(exc_))
        if mess.startswith("!br") and (
                message.channel.id in [900145851844935681, 911854338803109929, 876497506849144892]):
            try:
                msg = await message.channel.send(temp["content"],
                                                 embed=embed)
                await msg.add_reaction("✅")
                await message.delete()
            except Exception as exc_:
                await message.channel.send(
                    "Sorry, couldn't process Buddy read request. Exception: {}"
                    .format(exc_))
        else:
            embed.remove_field(1)  # end date
            embed.remove_field(0)  # start date
            msg = await message.channel.send("Is this the book you searched for?",
                                             embed=embed)


    # if mess.startswith("!botm"):
    #     l = mess.split(" ", 2)
    #     gr_link = l[1]
    #     discussion_date = l[2]
    #     b = BOTM(gr_link)
    #     b.setDetails()
    #     e = nextcord.Embed(
    #         title=b.botm["title"],
    #         description=b.botm["description"],
    #         color=nextcord.Colour.from_rgb(247, 31, 31),
    #         url=gr_link
    #     )
    #     g = ",".join(b.botm["genres"])
    #     e.set_author(name="BOOK OF THE MONTH",
    #                     icon_url="https://cdn.discordapp.com/attachments/911854338803109929/933443876021235732/final_61c041e9b5e7ac0053eae0e3_541544-9.png")
    #     e.add_field(name="Author", value=b.botm["author_name"], inline=True)
    #     e.add_field(name="Rating", value=b.botm["rating"] + "⭐", inline=True)
    #     e.add_field(name="Pages", value=str(b.botm["num_pages"]) + "🗐", inline=True)
    #     e.add_field(name="Genres", value=g, inline=False)
    #     e.add_field(name="Voice Chat Discussion On", value=discussion_date, inline=False)
    #     e.set_thumbnail(url=b.botm["thumbnail"])
    #     e.set_footer(text="Happy Reading!")
    #
    #     boo = await message.channel.send(
    #         "<@&876495352277106759> Please react with :white_check_mark:  if you'd like to participate in the discussions. Discussion will take place in <#878288705587122186> channel.",
    #         embed=e)
    #     await boo.add_reaction("✅")
    # if message.content.startswith("!help"):  # HELPPPPPP!!!
    #     pass

    # if message.content.startswith("!br del"):
    #
    #     await client.change_presence(
    #         activity=nextcord.Activity(
    #             type=nextcord.ActivityType.listening,
    #             name=f"{message.author.name}'s command"))
    #
    #     search_query = {"_id": channel_id}
    #     try:
    #         brtable_dict = collection.find(search_query)[0]
    #     except:
    #         await message.channel.send("Buddy Read Data for this channel doesn't exist")
    #         await change_status_to_default()
    #         return
    #
    #     for user_id in brtable_dict["br-details"]:
    #         user = await client.fetch_user(int(user_id))
    #         if user.name == author_name:
    #             brprogress_var = brtable_dict["br-details"][user_id]['BRprogress']
    #             search_query = {f"br-details.{author_id_str}": f"[{user.name}, {brprogress_var}]" }  # Wrong Query. Need to work on this bit.
    #             try:
    #                 result = collection.delete(search_query)
    #                 await message.channel.send(result)
    #                 await message.channel.send("Your progress for this BR is deleted.")
    #             except:
    #                 await message.channel.send("You need to update progress first before deleting it.")
    #                 await message.channel.send(hot_damn_gif)
    #     await change_status_to_default()
    #
    # if message.content.startswith("!wake up mavayya"):
    #     await message.channel.send("Mavayya: Lesthanlera oka 5 min aagaraa babu.. goppodivi ra babu!")
    #     driver.get(REPLIT_URL)
    #     print(driver.page_source)
    #     run_button = driver.find_element(by=By.XPATH,
    #                                      value='//*[@id="__next"]/div/main/div[2]/div/div/div[3]/div[1]/div/header/div[2]/div[3]/button/div/span')
    #     run_button.click()
    #     await message.channel.send("Mavayya oka 5 min lo lesthadu..")
    #     time.sleep(600)
    #     await message.channel.send("Mavayya lechado ledo check chey okasari..")
    #     driver.quit()

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    change_status.start()
    await client.get_channel(931066517360115753).send("Beep. Boop. Beep. I am online. :owl:  *hoots*")
    await client.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching,
                                                            name='BR progress on Book Servers'))


my_secret = os.environ['token']
client.run(my_secret)
