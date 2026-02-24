import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import datetime

DAILY_CHANNEL_ID = 1474476859210076294  # Daily code channel

class DailyCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_code = random.randint(1000, 9999)
        self.reset_daily_code.start()

    @tasks.loop(hours=24)
    async def reset_daily_code(self):
        await self.bot.wait_until_ready()
        now = datetime.datetime.now()
        # Calculate seconds until next midnight
        next_midnight = (now + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        sleep_seconds = (next_midnight - now).total_seconds()
        await discord.utils.sleep_until(next_midnight)

        self.daily_code = random.randint(1000, 9999)
        channel = self.bot.get_channel(DAILY_CHANNEL_ID)
        if channel:
            await channel.send(f"🎯 **Today's Access Code:** `{self.daily_code}`\n📅 Date: {datetime.date.today()}")

    @reset_daily_code.before_loop
    async def before_reset(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="code", description="Get today's access code")
    async def code(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Today's Access Code: `{self.daily_code}`")

async def setup(bot):
    await bot.add_cog(DailyCode(bot))
