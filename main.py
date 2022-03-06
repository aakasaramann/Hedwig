import nextcord
import time
from table2ascii import table2ascii as t2a, PresetStyle
import shelve
from itertools import cycle
from nextcord.ext import tasks
import os
import json

intents = nextcord.Intents.default()

client = nextcord.Client(intents=intents)

tenor_str = "https://tenor.com/view/"
send_gif = f"{tenor_str}harry-potter-hedwig-4privet-drive-deathly-hallows-battle-of-the-seven-potters-gif-14134385"
receive_gif = f"{tenor_str}youve-got-mail-mail-get-the-mail-package-what-a-hoot-gif-18029581"

status = cycle(['with Python', 'JetHub'])


@client.event
async def on_ready():
    change_status.start()
    print("Your bot is ready")


@tasks.loop(seconds=10)
async def change_status():
    await client.change_presence(activity=nextcord.Game(next(status)))


@client.event
async def on_message(message):
    msg_author = message.author.name
    channel = str(message.channel.id)
    author = str(message.author.id)

    if message.author == client.user:
        return

    if message.content.startswith("!pro update "):
        await client.change_presence(
            activity=nextcord.Activity(type=nextcord.ActivityType.listening, name=f"{message.author.name}'s command"))

        '''msg = await message.channel.send(send_gif)
        time.sleep(5)
        await msg.edit(receive_gif)
        time.sleep(3)
        await msg.delete()'''

        progress_msg = message.content[12:]
        temp = progress_msg

        if '/' in progress_msg:
            pg = temp.split('/')
            progress_msg = round((int(pg[0]) / int(pg[1])) * 100, 2)

        if int(progress_msg) == 100:
            await message.channel.send("Shabhash ra, pusthakam aipogottav!")
            time.sleep(2)

        db = shelve.open("BRProgressDB", writeback=True)
        try:
            db[channel][author] = progress_msg
        except:
            db[channel] = {author: progress_msg}
        await message.channel.send(f"{msg_author}'s progress for this br is set to {progress_msg}%")

        await client.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching,
                                                                name='Telugu Lit Soc BRs'))
        db.sync()
        db.close()

    if message.content.startswith("!pro view all") or message.content.startswith("!pro br status"):
        await client.change_presence(
            activity=nextcord.Activity(type=nextcord.ActivityType.listening, name=f"{message.author.name}'s command"))

        msg = await message.channel.send(send_gif)
        time.sleep(5)
        await msg.edit(receive_gif)
        time.sleep(3)
        await msg.delete()

        brtable = []

        db = shelve.open("BRProgressDB", writeback=True)

        for username in db[channel]:
            user = await client.fetch_user(int(username))
            brtable.append([user.name, float(db[channel][username])])
            time.sleep(0.2)

        brtable.sort(key=lambda x: x[1], reverse=True)
        # brtable = sorted(brtable, key = lambda x: x[1],reverse=True)
        output = t2a(header=["Username", "% Progress"], body=brtable, style=PresetStyle.thin_compact)
        await message.channel.send(f"```{output}```")

        await client.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching,
                                                                name='Telugu Lit Soc BRs'))
        db.sync()
        db.close()

    if message.content.startswith("!pro del"):
        db = shelve.open("BRProgressDB", writeback=True)
        await client.change_presence(
            activity=nextcord.Activity(type=nextcord.ActivityType.listening, name=f"{message.author.name}'s command"))
        db[channel].pop(author, None)
        await message.channel.send(f"{msg_author}'s progress for this BR is deleted.")

        db.sync()
        db.close()

    if message.content.startswith("!pro push "):
        initial_push = message.content[10:]
        db = shelve.open("BRProgressDB", writeback=True)
        await client.change_presence(
            activity=nextcord.Activity(type=nextcord.ActivityType.listening, name=f"{message.author.name}'s command"))
        init = json.loads(initial_push)
        for key, value in init:
            db[key] = value
        await message.channel.send("All initial values loaded")
        db.sync()
        db.close()

    if message.content.startswith("!pro all"):
        db = shelve.open("BRProgressDB", writeback=True)
        await message.channel.send(dict(db))
        db.sync()
        db.close()

    if message.content.startswith("!pro clear"):
        db = shelve.open("BRProgressDB", writeback=True)
        db.clear()
        await message.channel.send(dict(db))
        db.sync()
        db.close()

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    await client.get_channel(931066517360115753).send("Beep. Boop. Beep. I am online. :owl:  *hoots*")
    await client.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching,
                                                            name='Telugu Lit Soc BRs'))

my_secret = os.environ['token']
client.run(my_secret)
