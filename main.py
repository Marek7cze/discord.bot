import discord
from discord.ext import commands, tasks
import random
import datetime
import os
from flask import Flask
from threading import Thread

# ---- Tiny web server to keep Railway alive ----
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_web).start()

# ---- Discord Bot ----
CHANNEL_ID = 1474476859210076294

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

daily_code = random.randint(1000, 9999)

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    print(f"Today's code: {daily_code}")

@bot.command()
async def code(ctx):
    await ctx.send(
        f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}"
    

@tasks.loop(hours=24)
async def update_daily_code():
    global daily_code
    daily_code = random.randint(1000, 9999)
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(
            f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}"
        
update_daily_code.start()
bot.run(os.getenv("DISCORD_TOKEN"))
