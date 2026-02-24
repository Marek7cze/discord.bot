import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import asyncio
import sqlite3
import random
import datetime
from flask import Flask
import threading

# -----------------------------
# Flask Keep-Alive
# -----------------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080, use_reloader=False)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# -----------------------------
# Bot setup
# -----------------------------
GUILD_ID = 1247900579586642021
DAILY_CHANNEL_ID = 1474476859210076294
LEADERBOARD_CHANNEL_ID = 1474813234795249734

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# Database setup (persistent)
# -----------------------------
DB_PATH = os.getenv("DB_PATH", "player_stats.db")
conn = sqlite3.connect(DB_PATH)
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

def remove_player(standoff_id):
    c.execute("DELETE FROM players WHERE standoff_id = ?", (standoff_id,))
    conn.commit()

# -----------------------------
# Daily code
# -----------------------------
daily_code = random.randint(1000, 9999)

async def reset_daily_code():
    global daily_code
    await bot.wait_until_ready()
    while True:
        now = datetime.datetime.now()
        next_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        sleep_seconds = (next_midnight - now).total_seconds()
        await asyncio.sleep(sleep_seconds)
        daily_code = random.randint(1000, 9999)
        channel = bot.get_channel(DAILY_CHANNEL_ID)
        if channel:
            await channel.send(f"🎯 **Today's Access Code:** `{daily_code}`\n📅 Date: {datetime.date.today()}")

# -----------------------------
# Slash commands
# -----------------------------
@bot.tree.command(name="remove", description="Remove a player completely")
@app_commands.describe(standoff_id="Standoff 2 ID", member="Discord member")
async def remove(interaction: discord.Interaction, standoff_id: str = None, member: discord.Member = None):
    if member:
        player = get_player_by_discord(str(member.id))
    elif standoff_id:
        player = get_player(standoff_id)
    else:
        await interaction.response.send_message("Provide a Discord user or a Standoff ID.", ephemeral=True)
        return

    if not player:
        await interaction.response.send_message("Player not found.", ephemeral=True)
        return

    remove_player(player[0])
    await interaction.response.send_message(f"✅ Removed player {player[2]} ({player[0]}) from database.")

# -----------------------------
# Leaderboard task
# -----------------------------
@tasks.loop(minutes=5)
async def auto_leaderboard():
    await bot.wait_until_ready()
    channel = bot.get_channel(LEADERBOARD_CHANNEL_ID)
    if not channel:
        return

    c.execute("SELECT name, standoff_id, competitive, allies, duel, kd FROM players")
    players = c.fetchall()
    if not players:
        return

    # Simple leaderboard score: sum of ranks (you can adjust)
    leaderboard_data = []
    for name, standoff_id, competitive, allies, duel, kd in players:
        leaderboard_data.append((name, standoff_id, competitive, allies, duel, kd))

    embed = discord.Embed(title="🏆 All-Time Leaderboard", color=0xFFD700)
    for idx, (name, standoff_id, comp, allies_, duel_, kd) in enumerate(leaderboard_data[:10], start=1):
        embed.add_field(
            name=f"{idx}. {name} ({standoff_id})",
            value=f"Competitive: {comp} | Allies: {allies_} | Duel: {duel_}\nK/D: {kd:.2f}",
            inline=False
        )

    # Delete old leaderboard messages
    async for msg in channel.history(limit=20):
        if msg.author == bot.user and msg.embeds:
            await msg.delete()

    await channel.send(embed=embed)

# -----------------------------
# Bot ready
# -----------------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("✅ Slash commands synced")
    except Exception as e:
        print("Sync error:", e)
    if not auto_leaderboard.is_running():
        auto_leaderboard.start()
    bot.loop.create_task(reset_daily_code())

# -----------------------------
# Run bot
# -----------------------------
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("DISCORD_TOKEN not set!")
