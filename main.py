import os
import discord
import sqlite3
from dotenv import load_dotenv
from discord.ext import commands


load_dotenv()

token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix='?', intents=intents)

block_words = ["xxx"]

# Initialize the Database
conn = sqlite3.connect("userdata.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, level INTEGER, exp INTEGER)")
conn.commit()

# Role IDs
MODERATOR_ROLE_ID = 1145838642464575581  # Replace with the actual Moderator role ID
MEMBER_ROLE_ID = 1145840712466825296  # Replace with the actual Member role ID

# Custom Role Names
ROLE_NAMES = {
    "Král v zámku": MODERATOR_ROLE_ID,
    "Cigoš": MEMBER_ROLE_ID
}
# User data dictionary to store levels
user_data = {}


@bot.event
async def on_message(msg):
    if msg.author != bot.user:
        user_id = str(msg.author.id)
        cursor.execute("INSERT OR IGNORE INTO users (user_id, level, exp) VALUES (?, ?, ?)", (user_id, 1, 0))
        cursor.execute("UPDATE users SET exp = exp + 1 WHERE user_id = ?", (user_id,))
        conn.commit()  # Move this line to update the database for every message

        cursor.execute("SELECT level, exp FROM users WHERE user_id = ?", (user_id,))
        level, exp = cursor.fetchone()

        exp_needed = level * 10  # Calculate required exp based on the current level

        while exp >= exp_needed:
            cursor.execute("UPDATE users SET level = level + 1, exp = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            await msg.channel.send(
                f"Congrats {msg.author.mention}! You've leveled up to level {level + 1}!")
            level += 1  # Update the local 'level' variable
            exp_needed = level * 10

        await bot.process_commands(msg)




@bot.command()
async def profile(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    user_id = str(member.id)
    cursor.execute("SELECT level, exp FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row:
        level, exp = row
        await ctx.send(f"{member.mention}'s Profile\nLevel: {level}\nExperience: {exp}")
    else:
        await ctx.send(f"{member.mention}'s profile data not found.")


# Role Commands
@bot.command()
async def addrole(ctx, *, role_name):
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
async def removerole(ctx, *, role_name):
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


# Add points
@bot.command()
@commands.has_role("Král v zámku")  # Check if the author has the "Král v zámku" role
async def addpoints(ctx, member: discord.Member, points: int):
    if points <= 0:
        await ctx.send("Points must be a positive number.")
        return

    user_id = str(member.id)
    cursor.execute("INSERT OR IGNORE INTO users (user_id, level, exp) VALUES (?, ?, ?)", (user_id, 1, 0))
    cursor.execute("SELECT level, exp FROM users WHERE user_id = ?", (user_id,))
    level, exp = cursor.fetchone()

    new_exp = exp + points
    if new_exp >= level * 10:
        # Level up and reset exp if exp is greater than or equal to 10 times the level
        cursor.execute("UPDATE users SET level = level + 1, exp = ? WHERE user_id = ?", (new_exp - level * 10, user_id))
        conn.commit()
        await ctx.send(f"Congrats {member.mention}! You've leveled up to level {level + 1}!")
    else:
        cursor.execute("UPDATE users SET exp = ? WHERE user_id = ?", (new_exp, user_id))
        conn.commit()

    # Retrieve the updated exp value from the database
    cursor.execute("SELECT exp FROM users WHERE user_id = ?", (user_id,))
    updated_exp = cursor.fetchone()[0]

    await ctx.send(f"Added {points} points to {member.mention}. New exp: {updated_exp}")


@bot.command()
@commands.has_role("Král v zámku")  # Check if the author has the "Král v zámku" role
async def removepoints(ctx, member: discord.Member, points: int):
    if points <= 0:
        await ctx.send("Points must be a positive number.")
        return

    user_id = str(member.id)
    cursor.execute("INSERT OR IGNORE INTO users (user_id, level, exp) VALUES (?, ?, ?)", (user_id, 1, 0))
    cursor.execute("SELECT level, exp FROM users WHERE user_id = ?", (user_id,))
    level, exp = cursor.fetchone()

    new_exp = max(exp - points, 0)  # Ensure exp does not go negative

    if exp < points:
        # Level down and reset exp if current exp is less than points
        remaining_points = points - exp
        new_level = max(level - 1, 1)
        new_exp = new_level * 10 - remaining_points

        cursor.execute("UPDATE users SET level = ?, exp = ? WHERE user_id = ?", (new_level, new_exp, user_id))
        conn.commit()

        await ctx.send(f"{member.mention} has leveled down to level {new_level}!")

    else:
        cursor.execute("UPDATE users SET exp = ? WHERE user_id = ?", (new_exp, user_id))
        conn.commit()

    await ctx.send(f"Removed {points} points from {member.mention}. New exp: {new_exp}")




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


# Close the Database
@bot.event
async def on_disconnect():
    conn.close()

bot.run(token)
