import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import asyncio
import random
import datetime
import sqlite3
from flask import Flask
import threading

# =========================================================
# RAILWAY WEB SERVER (OPTIMIZED)
# =========================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!", 200

def run_web():
    # Railway uses PORT 8080 by default
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Start web server in a background thread
threading.Thread(target=run_web, daemon=True).start()

# =========================================================
# DATABASE (Persistent Path for Railway)
# =========================================================
# Use the volume path if it exists, otherwise fallback to local
DB_PATH = os.environ.get("DATABASE_URL", "player_stats.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

# Initialize DB
db_conn = get_db_connection()
c = db_conn.cursor()
c.execute("""
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
db_conn.commit()

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
# DB FUNCTIONS
# =========================================================
def add_player(standoff_id, discord_id, name):
    c.execute("INSERT OR IGNORE INTO players (standoff_id, discord_id, name) VALUES (?, ?, ?)",
              (standoff_id, discord_id, name))
    db_conn.commit()

def get_player(standoff_id):
    c.execute("SELECT * FROM players WHERE standoff_id = ?", (standoff_id,))
    return c.fetchone()

def get_player_by_discord(discord_id):
    c.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
    return c.fetchone()

def remove_player(standoff_id):
    c.execute("DELETE FROM players WHERE standoff_id = ?", (standoff_id,))
    db_conn.commit()

# =========================================================
# DAILY CODE TASK (Using Discord's built-in loop)
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

@reset_daily_code.before_loop
async def before_reset_daily_code():
    # Wait until midnight for the first run
    now = datetime.datetime.now()
    next_midnight = (now + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    seconds_until_midnight = (next_midnight - now).total_seconds()
    await asyncio.sleep(seconds_until_midnight)

# =========================================================
# COMMANDS
# =========================================================
@bot.tree.command(name="code", guild=GUILD_OBJECT)
async def code(interaction: discord.Interaction):
    await interaction.response.send_message(f"Today's Code: `{daily_code}`")

@bot.tree.command(name="register", guild=GUILD_OBJECT)
async def register(interaction: discord.Interaction, standoff_id: str, name: str):
    if get_player(standoff_id):
        return await interaction.response.send_message("Already registered.", ephemeral=True)
    
    add_player(standoff_id, str(interaction.user.id), name)
    await interaction.response.send_message(f"Registered {name} successfully!", ephemeral=True)

@bot.tree.command(name="stats", guild=GUILD_OBJECT)
async def stats(interaction: discord.Interaction, standoff_id: str = None, member: discord.Member = None):
    # Logic same as before...
    target_id = str(member.id) if member else None
    player = get_player_by_discord(target_id) if target_id else get_player(standoff_id)

    if not player:
        return await interaction.response.send_message("Player not found.", ephemeral=True)

    _, _, name, comp, allies, duel, kd = player
    embed = discord.Embed(title=f"{name}'s Stats", color=0x3498DB)
    embed.add_field(name="Competitive", value=comp)
    embed.add_field(name="Allies", value=allies)
    embed.add_field(name="Duel", value=duel)
    embed.set_footer(text=f"K/D: {kd}")
    await interaction.response.send_message(embed=embed)

# =========================================================
# STARTUP
# =========================================================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Syncing commands to the specific guild
    await bot.tree.sync(guild=GUILD_OBJECT)
    if not reset_daily_code.is_running():
        reset_daily_code.start()

# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("CRITICAL: DISCORD_TOKEN is not set in environment variables!")
