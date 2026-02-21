import discord
from discord.ext import commands, tasks
import random
import datetime
import os
from flask import Flask
import threading

# -----------------------------
# Flask Keep-Alive
# -----------------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Start Flask in a separate thread
threading.Thread(target=run_flask).start()

# -----------------------------
# Discord Bot Setup
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True  # REQUIRED for reading messages/commands

bot = commands.Bot(command_prefix="/", intents=intents)

# -----------------------------
# Daily Code Generator
# -----------------------------
daily_code = random.randint(1000, 9999)

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    print(f"Today's code: {daily_code}")
    update_daily_code.start()  # start the daily code updater

@bot.command()
async def code(ctx):
    await ctx.send(f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}")

# Automatically update the code every 24 hours
@tasks.loop(hours=24)
async def update_daily_code():
    global daily_code
    daily_code = random.randint(1000, 9999)
    # Replace YOUR_CHANNEL_ID with the numeric ID of your Discord channel
    channel = bot.get_channel(1474476859210076294)
    if channel:
        await channel.send(f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}")

# -----------------------------
# Run the Bot
# -----------------------------
bot.run(os.getenv("DISCORD_TOKEN"))
