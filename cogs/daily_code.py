import discord
from discord.ext import commands, tasks
from discord.utils import sleep_until
import random
import datetime

# Replace with your channel ID where the daily code should be posted
DAILY_CHANNEL_ID = 1474476859210076294  

class DailyCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_code = random.randint(1000, 9999)
        self.reset_daily_code.start()  # Start the daily code loop

    @tasks.loop(hours=24)
    async def reset_daily_code(self):
        await self.bot.wait_until_ready()

        # Calculate next midnight
        now = datetime.datetime.now()
        next_midnight = (now + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Wait until midnight
        await sleep_until(next_midnight)

        # Generate new code
        self.daily_code = random.randint(1000, 9999)

        # Send the code to the channel
        channel = self.bot.get_channel(DAILY_CHANNEL_ID)
        if channel:
            await channel.send(
                f"🎯 **Today's Access Code:** `{self.daily_code}`\n📅 Date: {datetime.date.today()}"
            )

    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ DailyCode Cog loaded")

    # Command for users to check the current daily code
    @commands.command()
    async def code(self, ctx):
        await ctx.send(f"🎯 Today's Access Code: `{self.daily_code}`")

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(DailyCode(bot))
