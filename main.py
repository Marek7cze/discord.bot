import discord
from discord.ext import commands, tasks
import random
import datetime
import asyncio

TOKEN = "YOUR_NEW_BOT_TOKEN_HERE"  # <-- put your NEW token here
CHANNEL_ID = 1474476859210076294  # your channel ID

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

daily_code = random.randint(1000, 9999)

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    print(f"Today's code: {daily_code}")
    bot.loop.create_task(wait_until_midnight())

@bot.command()
async def code(ctx):
    await ctx.send(f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}")

@tasks.loop(hours=24)
async def update_daily_code():
    global daily_code
    daily_code = random.randint(1000, 9999)

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(
            f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}"
        )
    else:
        print("Channel not found.")

async def wait_until_midnight():
    now = datetime.datetime.now()
    tomorrow = now + datetime.timedelta(days=1)
    midnight = datetime.datetime.combine(tomorrow.date(), datetime.time())
    seconds_until_midnight = (midnight - now).total_seconds()

    await asyncio.sleep(seconds_until_midnight)
    update_daily_code.start()

bot.run(TOKEN)
