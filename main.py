import os
import discord
import ffmpeg
from dotenv import load_dotenv
from discord.ext import commands
import youtube_dl

load_dotenv()

token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix='?', intents=intents)

block_words = ["xxx"]

# Role IDs
MODERATOR_ROLE_ID = 1145838642464575581  # Replace with the actual Moderator role ID
MEMBER_ROLE_ID = 1145840712466825296  # Replace with the actual Member role ID

# Custom Role Names
ROLE_NAMES = {
    "Král": MODERATOR_ROLE_ID,
    "Cigoš": MEMBER_ROLE_ID
}
# User data dictionary to store levels
user_data = {}

@bot.event
async def on_message(msg):
    if msg.author != bot.user:
        user_id = str(msg.author.id)
        if user_id not in user_data:
            user_data[user_id] = {"level": 1, "exp": 0}

        user_data[user_id]["exp"] += 1
        exp_needed = user_data[user_id]["level"] * 10  # Example: Level * 10 for required exp
        if user_data[user_id]["exp"] >= exp_needed:
            user_data[user_id]["level"] += 1
            await msg.channel.send(
                f"Congrats {msg.author.mention}! You've leveled up to level {user_data[user_id]['level']}!")


        await bot.process_commands(msg)


@bot.command()
async def profile(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    user_id = str(member.id)
    if user_id in user_data:
        level = user_data[user_id]["level"]
        exp = user_data[user_id]["exp"]
        await ctx.send(f"{member.mention}'s Profile\nLevel: {level}\nExperience: {exp}")
    else:
        await ctx.send(f"{member.mention}'s profile data not found.")

# Role Commands
@bot.command()
async def addrole(ctx, role_name):
    role_id = ROLE_NAMES.get(role_name)
    if role_id:
        role = ctx.guild.get_role(role_id)
        if role:
            await ctx.author.add_roles(role)
            await ctx.send(f"You've been assigned the {role.name} role.")
        else:
            await ctx.send("Role not found.")

    else:
        await ctx.send("Role not found.")

@bot.command()
async def removerole(ctx, role_name):
    role_id = ROLE_NAMES.get(role_name)
    if role_id:
        role = ctx.guild.get_role(role_id)
        if role and role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"You've been removed from the {role.name} role.")
        else:
            await ctx.send("Role not found or you don't have the role.")
    else:
        await ctx.send("Role not found.")

# Spotify Music Playback (to be implemented using a music library)

# Server Statistics
@bot.command()
async def serverstats(ctx):
    guild = ctx.guild
    total_members = len(guild.members)
    online_members = len([member for member in guild.members if member.status != discord.Status.offline])

    embed = discord.Embed(title="Server Statistics", color=discord.Color.blue())
    embed.add_field(name="Total Members", value=total_members, inline=False)
    embed.add_field(name="Online Members", value=online_members, inline=False)

    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"Bot Logged in as {bot.user}")

@bot.event
async def negative_words(msg):
    if msg.author != bot.user:
        for text in block_words:
            if "Moderator" not in str(msg.author.roles) and text in str(msg.content.lower()):
                await msg.delete()
                return
        await bot.process_commands(msg)


@bot.event
async def on_member_join(member):
    guild = member.guild
    channel_id = 1144617055765663887  # Replace with the ID of the channel where you want the message to be sent
    channel = guild.get_channel(channel_id)

    if channel is not None:
        await channel.send(f"Hi {member.mention}, welcome to the server!")

@bot.command()
async def rules(ctx):
    rules_text = "Server Rules:\n1. Be respectful to others.\n2. No spamming.\n3. No NSFW content."
    await ctx.send(rules_text)

@bot.command()
async def help_command(ctx):
    help_text = (
        "Welcome to the bot!\n"
        "Available Commands:\n"
        "?help - Display this help message.\n"
        "?rules - Display the server rules."
    )
    await ctx.send(help_text)

bot.run(token)
