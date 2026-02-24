# emoji_sync_test.py
import discord
from discord import app_commands
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# Your Server ID
# -----------------------------
GUILD_ID = 1247900579586642021  # Replace with your server ID if different

# -----------------------------
# Bot Ready
# -----------------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

    guild = discord.Object(id=GUILD_ID)

    # Force sync
    await bot.tree.sync(guild=guild)
    print("✅ Commands synced")

    # Fetch and print all registered guild commands
    commands_list = await bot.tree.fetch_guild_commands(guild.id)
    print("🔹 Registered guild commands:")
    for cmd in commands_list:
        print(f"- {cmd.name} : {cmd.description}")

# -----------------------------
# Run Bot
# -----------------------------
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("DISCORD_TOKEN not set!")
