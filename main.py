import discord
from discord.ext import commands, tasks
import random
import datetime
bot = commands.Bot(command_prefix="/")
daily_code = random.randint(1000, 9999)
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    print(f"Today's code: {daily_code}")
    update_daily_code.start(0:00)
@bot.command(Code)
async def code(ctx):
    await ctx.send(f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}")
@tasks.loop(hours=24)
async def update_daily_code():
    global daily_code
    daily_code = random.randint(1000, 9999)
    channel = bot.get_channel(1474476859210076294)
    if channel:await channel.send(f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}")
bot.run("YOUR_BOT_TOKEN_HERE")  # replace with your bot token
