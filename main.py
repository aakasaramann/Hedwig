import ast
import os
import re
import time
from itertools import cycle

import discord
import pymongo
from discord.ext import commands, tasks
from table2ascii import PresetStyle
from table2ascii import table2ascii as t2a

from Buddy_Reading import BuddyRead

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# status variable changing status of discord bot
status = cycle(["Announcements", "BR Progress", "Book Recommendations"])

# MongoDB server details
conn_str = os.environ["uri"]
cluster = pymongo.MongoClient(
    conn_str,
    serverSelectionTimeoutMS=5000)  # set a 5-second connection timeout
db = cluster["HedwigDB"]
collection = db["BRProgress"]
try:
    print(cluster.server_info())  # prints sever info is connection works
except Exception:
    print("Unable to connect to the server.")


async def change_status_to_default():
    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="BR progress on Book Servers")
    )


@tasks.loop(seconds=300)
async def change_status():
    await client.change_presence(activity=discord.Game(next(status)))


@client.event
async def on_message(message):
    author_name = message.author.name
    channel_id = message.channel.id
    author_id = message.author.id
    author_id_str = str(author_id)

    if message.author == client.user:  #For ignoring its own messages
        return

    if message.author.bot: #Ignores bots messages
        return

    if message.content.startswith("!br update "):
        await client.change_presence(activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{message.author.name}'s command",
        ))

        progress_msg = message.content[11:]
        temp = progress_msg

        if "/" in progress_msg:
            pg = temp.split("/")
            progress_msg = round((int(pg[0]) / int(pg[1])) * 100, 2)

        if int(progress_msg) > 100:
            await message.channel.send(
                "Progress should be less than are equal to 100")
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

        br_details = {
            author_id_str: {
                "username": author_name,
                "BRprogress": int(progress_msg)
            }
        }
        br_data_dict = {
            "_id": channel_id,
            "name": client.get_channel(channel_id).name,
            "br-details": br_details,
        }
        try:
            collection.insert_one(br_data_dict)
        except:
            search_query = {"_id": channel_id}
            update_query = {
                "$set": {
                    f"br-details.{author_id_str}.BRprogress": progress_msg,
                    f"br-details.{author_id_str}.username": author_name,
                }
            }
            collection.update_one(filter=search_query, update=update_query)

        await message.channel.send(
            f"{author_name}'s progress for this buddy-read is set to {progress_msg}%"
        )
        await change_status_to_default()

    mess = message.content
    username = message.author

    if message.content.startswith("!br status"):
        await client.change_presence(activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{message.author.name}'s command",
        ))

        search_query = {"_id": channel_id}
        try:
            brtable_dict = collection.find(search_query)[0]
        except:
            await message.channel.send(
                "Buddy Read Data for this channel doesn't exist")
            await change_status_to_default()
            return

        brtable = []
        for user_id in brtable_dict["br-details"]:
            user = await client.fetch_user(int(user_id))
            brprogress_var = brtable_dict["br-details"][user_id]["BRprogress"]
            brtable.append([user.name, brprogress_var])
            time.sleep(0.2)

        output = t2a(
            header=["Username", "% Progress"],
            body=brtable,
            style=PresetStyle.thin_compact,
        )
        await message.channel.send(f"```{output}```")
        await change_status_to_default()

    # Searches for the book on goodreads and sends an embed message
    elif mess.strip(" \n").lower().startswith("!book"):
        mess = mess.strip(" \n").lower()
        try:
            temp = ast.literal_eval(BuddyRead(mess.strip(), username)())
            print(temp)
            embed = discord.Embed.from_dict(temp["embeds"][-1])
        except Exception as exc_:
            await message.channel.send(
                "Sorry, couldn't process Book request. Exception: {}".format(
                    exc_))
        if mess.startswith("!br") and (message.channel.id in [
            900145851844935681, 911854338803109929, 876497506849144892
        ]):
            try:
                msg = await message.channel.send(temp["content"], embed=embed)
                await msg.add_reaction("✅")
                await message.delete()
            except Exception as exc_:
                await message.channel.send(
                    "Sorry, couldn't process Buddy read request. Exception: {}"
                    .format(exc_))
        else:
            embed.remove_field(1)  # end date
            embed.remove_field(0)  # start date
            msg = await message.channel.send(
                "Is this the book you searched for?", embed=embed)

    if message.content.startswith('$announce_br'):

        required_role_one = discord.utils.get(message.guild.roles, name="BR Leader")
        required_role_two = discord.utils.get(message.guild.roles, name="Staff")

        # Check if the user has the role
        if required_role_one not in message.author.roles and required_role_two not in message.author.roles and message.author.id != 821036244305707028:
        # Now you can handle the command... send an ephermal message
            await message.channel.send("You don't have the required role to use this command.", delete_after=30)
            return
        # await message.channel.send("You can use the command.")
        # Parse the command and get the message link
        message_link = message.content.split(' ')[1]
        # channel_id = message.content.split(' ')[2]
        # I need the rest of the string not just the string till next space

        announcement_message = " ".join(message.content.split(' ')[2:])

        if announcement_message in ["None", "none", "NONE", "n", "N"]:
            announcement_message = ""

        # Parse the message link
        pattern = r'https?://(www\.)?discord(app)?\.com/channels/(\d+)/(\d+)/(\d+)'
        match = re.match(pattern, message_link)
        if not match:
            await message.channel.send("Invalid message link.")
            return

        # Extract server ID, channel ID, and message ID
        guild_id, channel_id, message_id = int(match.group(3)), int(match.group(4)), int(match.group(5))

        # Fetch the message object
        channel = client.get_channel(channel_id)
        target_message = await channel.fetch_message(message_id)

        # Iterate through reactions and fetch users
        users_who_reacted = []
        for reaction in target_message.reactions:
            async for user in reaction.users():
                users_who_reacted.append("<@" + str(user.id) + ">")

        # Send the list of users who reacted
        if users_who_reacted:
            await message.channel.send((', '.join(users_who_reacted)) + " " + announcement_message)
        else:
            await message.channel.send("No users reacted to this message.")


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    change_status.start()
    await client.get_channel(931066517360115753).send(
        "Beep. Boop. Beep. I am online. :owl:  *hoots*")
    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="BR progress on Book Servers")
    )
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


@client.tree.command(name="hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hey,{interaction.user.mention}!",
                                            ephemeral=True)

my_secret = os.environ["token"]
client.run(my_secret)
