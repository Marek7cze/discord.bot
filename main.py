import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import random
import datetime
import sqlite3
from flask import Flask
import threading

# =========================================================
# RAILWAY WEB SERVER
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
# CONFIG
# =========================================================
GUILD_ID = 1247900579586642021
DAILY_CHANNEL_ID = 1474476859210076294

GUILD_OBJECT = discord.Object(id=GUILD_ID)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================================================
# DATABASE
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
    kd REAL DEFAULT 0.0
)
""")
conn.commit()

def add_player(standoff_id, discord_id, name):
    c.execute(
        "INSERT OR IGNORE INTO players VALUES (?, ?, ?, '❌ NO RANK', '❌ NO RANK', '❌ NO RANK', 0.0)",
        (standoff_id, discord_id, name)
    )
    conn.commit()

def get_player(standoff_id):
    c.execute("SELECT * FROM players WHERE standoff_id = ?", (standoff_id,))
    return c.fetchone()

def get_all_players():
    c.execute("SELECT * FROM players")
    return c.fetchall()

def update_kd(standoff_id, kd):
    c.execute("UPDATE players SET kd = ? WHERE standoff_id = ?", (kd, standoff_id))
    conn.commit()

def update_rank(standoff_id, mode, value):
    if mode not in ["competitive", "allies", "duel"]:
        return False
    c.execute(f"UPDATE players SET {mode} = ? WHERE standoff_id = ?", (value, standoff_id))
    conn.commit()
    return True

def remove_player(standoff_id):
    c.execute("DELETE FROM players WHERE standoff_id = ?", (standoff_id,))
    conn.commit()

# =========================================================
# RANKS
# =========================================================
RANKS = [
    "❌ NO RANK",
    "Bronze",
    "Silver",
    "Gold",
    "Phoenix",
    "Ranger",
    "Champion",
    "Master",
    "Elite",
    "TheLegend"
]

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
@bot.tree.command(name="register", guild=GUILD_OBJECT)
@app_commands.describe(standoff_id="Your ID", name="Your Name")
async def register(interaction: discord.Interaction, standoff_id: str, name: str):

    if get_player(standoff_id):
        await interaction.response.send_message("Already registered.", ephemeral=True)
        return

    add_player(standoff_id, str(interaction.user.id), name)
    await interaction.response.send_message("Registered!", ephemeral=True)


@bot.tree.command(name="remove", guild=GUILD_OBJECT)
@app_commands.describe(standoff_id="Player ID")
async def remove(interaction: discord.Interaction, standoff_id: str):

    if not get_player(standoff_id):
        await interaction.response.send_message("Player not found.", ephemeral=True)
        return

    remove_player(standoff_id)
    await interaction.response.send_message("✅ Player removed.")


@bot.tree.command(name="update_kd", guild=GUILD_OBJECT)
@app_commands.describe(standoff_id="Player ID", kd="New KD")
async def update_kd_command(interaction: discord.Interaction, standoff_id: str, kd: float):

    if not get_player(standoff_id):
        await interaction.response.send_message("Player not found.", ephemeral=True)
        return

    update_kd(standoff_id, kd)
    await interaction.response.send_message("KD Updated.")


@bot.tree.command(name="update_rank", guild=GUILD_OBJECT)
@app_commands.describe(standoff_id="Player ID", mode="competitive/allies/duel", rank="Rank name")
async def update_rank_command(interaction: discord.Interaction, standoff_id: str, mode: str, rank: str):

    if rank not in RANKS:
        await interaction.response.send_message("Invalid rank.", ephemeral=True)
        return

    if not update_rank(standoff_id, mode.lower(), rank):
        await interaction.response.send_message("Invalid mode. Use competitive/allies/duel.", ephemeral=True)
        return

    await interaction.response.send_message("Rank updated.")


@bot.tree.command(name="stats", guild=GUILD_OBJECT)
@app_commands.describe(standoff_id="Player ID")
async def stats(interaction: discord.Interaction, standoff_id: str):

    player = get_player(standoff_id)
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


@bot.tree.command(name="leaderboard", guild=GUILD_OBJECT)
async def leaderboard(interaction: discord.Interaction):

    players = get_all_players()
    if not players:
        await interaction.response.send_message("No players registered.")
        return

    sorted_players = sorted(players, key=lambda x: x[6], reverse=True)

    embed = discord.Embed(title="🏆 Leaderboard", color=0xFFD700)

    for i, player in enumerate(sorted_players[:10], start=1):
        embed.add_field(
            name=f"{i}. {player[2]} ({player[0]})",
            value=f"K/D: {player[6]}",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

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
