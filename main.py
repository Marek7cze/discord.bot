import discord
from discord.ext import commands
import os
import asyncio
import datetime
import random
from flask import Flask
import threading

# -----------------------------
# Flask Keep-Alive (SAFE)
# -----------------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080, use_reloader=False)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# -----------------------------
# Bot Setup
# -----------------------------
GUILD_ID = 1247900579586642021  # Your server ID

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Load all cogs from cogs/ folder
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"✅ Loaded cog {filename}")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")

        # Start daily code background task
        self.loop.create_task(reset_daily_code())

bot = MyBot()

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("✅ Slash commands synced")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# -----------------------------
# Database Setup
# -----------------------------
import sqlite3

conn = sqlite3.connect("player_stats.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS players (
    standoff_id TEXT PRIMARY KEY,
    discord_id TEXT,
    name TEXT,
    competitive TEXT DEFAULT 'RANK EMPTY',
    allies TEXT DEFAULT 'RANK EMPTY',
    duel TEXT DEFAULT 'RANK EMPTY',
    kd REAL DEFAULT 0.00
)
""")
conn.commit()

def add_player(standoff_id, discord_id, name):
    c.execute("INSERT OR IGNORE INTO players (standoff_id, discord_id, name) VALUES (?, ?, ?)",
              (standoff_id, discord_id, name))
    conn.commit()

def get_player(standoff_id):
    c.execute("SELECT * FROM players WHERE standoff_id = ?", (standoff_id,))
    return c.fetchone()

def get_player_by_discord(discord_id):
    c.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
    return c.fetchone()

def update_player(standoff_id, field, value):
    c.execute(f"UPDATE players SET {field} = ? WHERE standoff_id = ?", (value, standoff_id))
    conn.commit()

# -----------------------------
# Daily Code Task
# -----------------------------
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
        channel = bot.get_channel(1474476859210076294)  # Your daily code channel ID
        if channel:
            await channel.send(f"🎯 **Today's Access Code:** `{daily_code}`\n📅 Date: {datetime.date.today()}")


# -----------------------------
# Run the bot
# -----------------------------
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("DISCORD_TOKEN not set!")
