import discord
from discord.ext import commands
import random
import datetime

TOKEN = "PUT_YOUR_NEW_TOKEN_HERE"
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
    bot.run(os.getenv("DISCORD_TOKEN"))
