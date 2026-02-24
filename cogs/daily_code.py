import discord
from discord.ext import commands, tasks
import random
import datetime

DAILY_CHANNEL_ID = 1474476859210076294  # Replace with your daily code channel ID

class DailyCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_code = random.randint(1000, 9999)
        self.reset_daily_code.start()

    @tasks.loop(hours=24)
    async def reset_daily_code(self):
        # Wait until bot is ready
        await self.bot.wait_until_ready()

        now = datetime.datetime.now()
        next_midnight = (now + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        sleep_seconds = (next_midnight - now).total_seconds()
        await discord.utils.sleep_until(next_midnight)  # optional alternative
        self.daily_code = random.randint(1000, 9999)

        channel = self.bot.get_channel(DAILY_CHANNEL_ID)
        if channel:
            await channel.send(
                f"🎯 **Today's Access Code:** `{self.daily_code}`\n📅 Date: {datetime.date.today()}"
            )

    @commands.Cog.listener()
    async def on_ready(self):
        print("DailyCode Cog loaded")

    # Optional command to check today's code
    @commands.command()
    async def code(self, ctx):
        await ctx.send(f"Today's Access Code: `{self.daily_code}`")

async def setup(bot):
    await bot.add_cog(DailyCode(bot))
