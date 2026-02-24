import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Load all cogs
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    try:
        await bot.tree.sync()
        print("✅ Slash commands synced")
    except Exception as e:
        print("Sync error:", e)

async def main():
    await load_cogs()
    token = os.getenv("DISCORD_TOKEN")
    if token:
        await bot.start(token)
    else:
        print("DISCORD_TOKEN not set!")

asyncio.run(main())
