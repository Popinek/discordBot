import os
import discord
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

block_words = ["xxx"]

@client.event
async def on_ready():
    print(f"Bot Logged in as {client.user}")


@client.event
async def on_message(msg):
    if msg.author != client.user:
        for text in block_words:
            if "Moderator" not in str(msg.author.roles) and text in str(msg.content.lower()):
                #await msg.author.ban()
                await msg.delete()
                return
        if msg.content.lower().startswith("hi"):
            await msg.channel.send(f"Vitaj, {msg.author.display_name}")
        if msg.content.lower().startswith("help"):
            await msg.channel.send(f"There is no help, {msg.author.display_name}")


client.run(token)
