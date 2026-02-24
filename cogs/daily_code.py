import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import random

GUILD_ID = 1247900579586642021
DAILY_CHANNEL_ID = 1474476859210076294  # Your daily code channel

class DailyCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_code = random.randint(1000, 9999)
        self.last_sent_date = None
        self.reset_daily_code.start()

    # Check every minute
    @tasks.loop(minutes=1)
    async def reset_daily_code(self):
        now = datetime.datetime.now()

        # If it's midnight and we haven't sent today's code yet
        if now.hour == 0 and now.minute == 0:
            today = now.date()

            if self.last_sent_date != today:
                self.daily_code = random.randint(1000, 9999)
                channel = self.bot.get_channel(DAILY_CHANNEL_ID)

                if channel:
                    await channel.send(
                        f"🎯 **Today's Access Code:** `{self.daily_code}`\n"
                        f"📅 Date: {today}"
                    )

                self.last_sent_date = today

    @reset_daily_code.before_loop
    async def before_reset(self):
        await self.bot.wait_until_ready()

    # Slash command version
    @app_commands.command(name="code", description="Get today's access code")
    async def get_code(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"🎯 Today's Access Code: `{self.daily_code}`",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(DailyCode(bot))
