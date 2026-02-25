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
# RAILWAY WEB SERVER (REQUIRED)
# =========================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

# =========================================================
# DISCORD CONFIG
# =========================================================
GUILD_ID = 1247900579586642021
DAILY_CHANNEL_ID = 1474476859210076294
LEADERBOARD_CHANNEL_ID = 1474813234795249734

GUILD_OBJECT = discord.Object(id=GUILD_ID)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================================================
# DATABASE (Safe for Railway)
# =========================================================
conn = sqlite3.connect("player_stats.db", check_same_thread=False)
c = conn.cursor()

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
conn.commit()

def add_player(standoff_id, discord_id, name):
    c.execute("INSERT OR IGNORE INTO players VALUES (?, ?, ?, '❌ NO RANK', '❌ NO RANK', '❌ NO RANK', 0.0)",
              (standoff_id, discord_id, name))
    conn.commit()

def get_player(standoff_id):
    c.execute("SELECT * FROM players WHERE standoff_id = ?", (standoff_id,))
    return c.fetchone()

def get_player_by_discord(discord_id):
    c.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
    return c.fetchone()

def remove_player(standoff_id):
    c.execute("DELETE FROM players WHERE standoff_id = ?", (standoff_id,))
    conn.commit()

# =========================================================
# DAILY CODE
# =========================================================
daily_code = random.randint(1000, 9999)

async def reset_daily_code():
    await bot.wait_until_ready()
    global daily_code

    while True:
        now = datetime.datetime.now()
        next_midnight = (now + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        await asyncio.sleep((next_midnight - now).total_seconds())

        daily_code = random.randint(1000, 9999)

        channel = bot.get_channel(DAILY_CHANNEL_ID)
        if channel:
            await channel.send(f"🎯 Today's Code: `{daily_code}`")

# =========================================================
# COMMANDS
# =========================================================
@bot.tree.command(name="code", guild=GUILD_OBJECT)
async def code(interaction: discord.Interaction):
    await interaction.response.send_message(f"Today's Code: `{daily_code}`")

@bot.tree.command(name="register", guild=GUILD_OBJECT)
@app_commands.describe(standoff_id="Your ID", name="Your Name")
async def register(interaction: discord.Interaction, standoff_id: str, name: str):

    if get_player(standoff_id):
        await interaction.response.send_message("Already registered.", ephemeral=True)
        return

    add_player(standoff_id, str(interaction.user.id), name)
    await interaction.response.send_message("Registered successfully!", ephemeral=True)

@bot.tree.command(name="stats", guild=GUILD_OBJECT)
async def stats(interaction: discord.Interaction, standoff_id: str = None, member: discord.Member = None):

    if member:
        player = get_player_by_discord(str(member.id))
    elif standoff_id:
        player = get_player(standoff_id)
    else:
        await interaction.response.send_message("Provide ID or member.", ephemeral=True)
        return

    if not player:
        await interaction.response.send_message("Player not found.", ephemeral=True)
        return

    _, _, name, comp, allies, duel, kd = player

    embed = discord.Embed(title=f"{name}'s Stats", color=0x3498DB)
    embed.add_field(name="Competitive", value=comp)
    embed.add_field(name="Allies", value=allies)
    embed.add_field(name="Duel", value=duel)
    embed.set_footer(text=f"K/D: {kd}")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="remove", guild=GUILD_OBJECT)
async def remove(interaction: discord.Interaction, standoff_id: str):

    if not get_player(standoff_id):
        await interaction.response.send_message("Player not found.", ephemeral=True)
        return

    remove_player(standoff_id)
    await interaction.response.send_message("Removed successfully.")

# =========================================================
# STARTUP
# =========================================================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync(guild=GUILD_OBJECT)
    bot.loop.create_task(reset_daily_code())

# =========================================================
# RUN
# =========================================================
token = os.environ.get("DISCORD_TOKEN")

if token:
    bot.run(token)
else:
    print("DISCORD_TOKEN not set!")
