import discord
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True  # REQUIRED for reading message content

bot = commands.Bot(command_prefix="/", intents=intents)
@tasks.loop(hours=24)
async def update_daily_code():
    global daily_code
    daily_code = random.randint(1000, 9999)
    channel = bot.get_channel(YOUR_CHANNEL_ID)  # replace with your Discord channel ID
    if channel:
        await channel.send(f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}")
        @bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    update_daily_code.start()
