import discord
from discord.ext import commands, tasks
import os
import asyncio
import random
import datetime
import sqlite3
from flask import Flask
import threading

# =========================================================
# RAILWAY WEB SERVER (CRITICAL FIX)
# =========================================================
app = Flask(__name__)

@app.route("/")
def health_check():
    # Railway needs a 200 OK response to keep the container running
    return "Bot is running!", 200

def run_web():
    # Railway automatically assigns a PORT variable; we MUST use it
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Start the web server in a background thread BEFORE the bot starts
threading.Thread(target=run_web, daemon=True).start()

# =========================================================
# DATABASE SETUP
# =========================================================
# If you use a Volume in Railway, change this to "/data/player_stats.db"
DB_PATH = "player_stats.db"

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

db = get_db()
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    standoff_id TEXT PRIMARY KEY,
    discord_id TEXT,
    name TEXT,
    competitive TEXT DEFAULT '❌ NO RANK',
    allies TEXT DEFAULT '❌ NO RANK',
    duel TEXT DEFAULT '❌ NO RANK',
    kd REAL DEFAULT 0.00
)
""")
db.commit()

# =========================================================
# DISCORD CONFIG
# =========================================================
GUILD_ID = 1247900579586642021
GUILD_OBJECT = discord.Object(id=GUILD_ID)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================================================
# DAILY CODE TASK
# =========================================================
daily_code = random.randint(1000, 9999)
DAILY_CHANNEL_ID = 1474476859210076294

@tasks.loop(hours=24)
async def reset_daily_code():
    global daily_code
    daily_code = random.randint(1000, 9999)
    channel = bot.get_channel(DAILY_CHANNEL_ID)
    if channel:
        await channel.send(f"🎯 Today's Code: `{daily_code}`")

# =========================================================
# COMMANDS
# =========================================================
@bot.tree.command(name="register", guild=GUILD_OBJECT)
async def register(interaction: discord.Interaction, standoff_id: str, name: str):
    cursor.execute("SELECT * FROM players WHERE standoff_id = ?", (standoff_id,))
    if cursor.fetchone():
        return await interaction.response.send_message("Already registered.", ephemeral=True)
    
    cursor.execute("INSERT INTO players (standoff_id, discord_id, name) VALUES (?, ?, ?)",
                  (standoff_id, str(interaction.user.id), name))
    db.commit()
    await interaction.response.send_message(f"Registered {name}!", ephemeral=True)

@bot.tree.command(name="code", guild=GUILD_OBJECT)
async def code(interaction: discord.Interaction):
    await interaction.response.send_message(f"Today's Code: `{daily_code}`")

# =========================================================
# STARTUP
# =========================================================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.tree.sync(guild=GUILD_OBJECT)
    if not reset_daily_code.is_running():
        reset_daily_code.start()

if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ ERROR: DISCORD_TOKEN environment variable not found.")
