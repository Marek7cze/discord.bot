import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import datetime
import random

GUILD_ID = 1247900579586642021
DAILY_CHANNEL_ID = 1474476859210076294

daily_code = random.randint(1000, 9999)

async def reset_daily_code():
    global daily_code
    await bot.wait_until_ready()
    while True:
        now = datetime.datetime.now()
        next_midnight = (now + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        sleep_seconds = (next_midnight - now).total_seconds()
        await asyncio.sleep(sleep_seconds)
        daily_code = random.randint(1000, 9999)
        channel = bot.get_channel(DAILY_CHANNEL_ID)
        if channel:
            await channel.send(f"🎯 **Today's Access Code:** `{daily_code}`\n📅 Date: {datetime.date.today()}")

class DailyCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(reset_daily_code())

    @commands.command()
    async def code(self, ctx):
        await ctx.send(f"Today's Access Code: `{daily_code}`")

async def setup(bot):
    await bot.add_cog(DailyCode(bot))
