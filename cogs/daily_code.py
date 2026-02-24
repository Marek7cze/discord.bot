import discord
from discord.ext import commands, tasks
import datetime
import random

DAILY_CHANNEL_ID = 1474476859210076294

class DailyCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_code = random.randint(1000, 9999)
        self.reset_daily_code.start()  # start the background task

    @tasks.loop(seconds=60)  # check every minute
    async def reset_daily_code(self):
        now = datetime.datetime.now()
        if now.hour == 0 and now.minute == 0:  # at midnight
            self.daily_code = random.randint(1000, 9999)
            channel = self.bot.get_channel(DAILY_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"🎯 **Today's Access Code:** `{self.daily_code}`\n📅 Date: {now.date()}"
                )

    @commands.command()
    async def code(self, ctx):
        await ctx.send(f"Today's Access Code: `{self.daily_code}`")

    @reset_daily_code.before_loop
    async def before_reset(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(DailyCode(bot))
