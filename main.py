import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
import sqlite3
import os
import asyncio
from flask import Flask
import threading

# -----------------------------
# Flask Keep-Alive
# -----------------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080)).start()

# -----------------------------
# Bot Setup
# -----------------------------
GUILD_ID = 1247900579586642021  # Your server ID
DAILY_CHANNEL_ID = 1474476859210076294  # Daily code channel ID

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# Database Setup
# -----------------------------
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
# Daily Code
# -----------------------------
daily_code = random.randint(1000, 9999)

async def reset_daily_code():
    global daily_code
    await bot.wait_until_ready()
    while True:
        now = datetime.datetime.now()
        next_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await asyncio.sleep((next_midnight - now).total_seconds())
        daily_code = random.randint(1000, 9999)
        channel = bot.get_channel(DAILY_CHANNEL_ID)
        if channel:
            await channel.send(f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}")

@bot.command()
async def code(ctx):
    await ctx.send(f"Today's Access Code: `{daily_code}`")

# -----------------------------
# Predefined Ranks
# -----------------------------
RANKS = [
    "RANK EMPTY", "Bronze I", "Bronze II", "Bronze III",
    "Silver I", "Silver II", "Silver III",
    "Gold I", "Gold II", "Gold III",
    "Platinum I", "Platinum II", "Platinum III",
    "Diamond I", "Diamond II", "Diamond III",
    "Master", "Grandmaster"
]

# -----------------------------
# /register
# -----------------------------
@bot.tree.command(name="register", description="Register your Standoff 2 account", guild=discord.Object(id=GUILD_ID))
async def register(interaction: discord.Interaction, standoff_id: str, name: str):
    if get_player(standoff_id):
        await interaction.response.send_message(f"Player {standoff_id} already registered.", ephemeral=True)
        return
    add_player(standoff_id, str(interaction.user.id), name)
    await interaction.response.send_message(f"✅ Registered {name} with Standoff ID {standoff_id}!", ephemeral=True)

# -----------------------------
# /stats
# -----------------------------
@bot.tree.command(name="stats", description="View a player's stats", guild=discord.Object(id=GUILD_ID))
async def stats(interaction: discord.Interaction, standoff_id: str = None, member: discord.Member = None):
    if member:
        player = get_player_by_discord(str(member.id))
        if not player:
            await interaction.response.send_message("Player not found for this Discord user.", ephemeral=True)
            return
    elif standoff_id:
        player = get_player(standoff_id)
        if not player:
            await interaction.response.send_message("Player not found for this Standoff ID.", ephemeral=True)
            return
    else:
        await interaction.response.send_message("Provide a Discord user or a Standoff ID.", ephemeral=True)
        return

    _, discord_id, name, competitive, allies, duel, kd = player
    embed = discord.Embed(title=f"{name}'s Stats", color=0x3498DB)
    embed.add_field(name="Standoff 2 ID", value=player[0], inline=False)
    embed.add_field(name="Competitive", value=competitive, inline=True)
    embed.add_field(name="Allies", value=allies, inline=True)
    embed.add_field(name="Duel", value=duel, inline=True)
    embed.set_footer(text=f"K/D: {kd:.2f} • Last updated")
    await interaction.response.send_message(embed=embed)

# -----------------------------
# /update_rank
# -----------------------------
@bot.tree.command(name="update_rank", description="Update a player's rank", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(manage_roles=True)
async def update_rank(interaction: discord.Interaction, standoff_id: str, field: str, rank_value: str):
    if field.lower() not in ["competitive", "allies", "duel"]:
        await interaction.response.send_message("Field must be: competitive, allies, duel", ephemeral=True)
        return
    if rank_value not in RANKS:
        await interaction.response.send_message(f"Invalid rank. Choose from: {', '.join(RANKS)}", ephemeral=True)
        return
    update_player(standoff_id, field.lower(), rank_value)
    await interaction.response.send_message(f"{field.capitalize()} updated to {rank_value} for {standoff_id}")

# -----------------------------
# /update_kd
# -----------------------------
@bot.tree.command(name="update_kd", description="Update a player's K/D", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(manage_roles=True)
async def update_kd(interaction: discord.Interaction, standoff_id: str, kd_value: float):
    if not 0.0 <= kd_value <= 1000.0:
        await interaction.response.send_message("K/D must be between 0.00 and 1000.00", ephemeral=True)
        return
    player = get_player(standoff_id)
    if not player:
        await interaction.response.send_message("Player not found.", ephemeral=True)
        return
    update_player(standoff_id, "kd", kd_value)
    await interaction.response.send_message(f"K/D updated to {kd_value:.2f} for {standoff_id}")

# -----------------------------
# Bot Ready
# -----------------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("✅ Slash commands synced")
    except Exception as e:
        print("Sync error:", e)
    bot.loop.create_task(reset_daily_code())

# -----------------------------
# Run Bot
# -----------------------------
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("DISCORD_TOKEN not set!")
