import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import random
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
LEADERBOARD_CHANNEL_ID = 1474813234795249734

GUILD_OBJECT = discord.Object(id=GUILD_ID)

intents = discord.Intents.default()
intents.members = True

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

# =========================================================
# RANK SYSTEM WITH EMOJIS
# =========================================================
RANKS = {
    "❌ NO RANK": ("❌ NO RANK", 0),

    "Bronze I": ("<:BronzeI:1475882755664384154>", 1),
    "Bronze II": ("<:BronzeII:1475883215154712758>", 2),
    "Bronze III": ("<:BronzeIII:1475882893804044402>", 3),
    "Bronze IV": ("<:BronzeIV:1475882954831167508>", 4),

    "Silver I": ("<:SilverI:1475887681454997739>", 5),
    "Silver II": ("<:SilverII:1475885246292430901>", 6),
    "Silver III": ("<:SilverIII:1475885332128993342>", 7),
    "Silver IV": ("<:SilverIV:1475885397157478540>", 8),

    "Gold I": ("<:GoldI:1475887285202583605>", 9),
    "Gold II": ("<:GoldII:1475887345877389435>", 10),
    "Gold III": ("<:GoldIII:1475887439456243815>", 11),
    "Gold IV": ("<:GoldIV:1475887516816248852>", 12),

    "Phoenix": ("<:Phoenix:1475885669271474328>", 13),
    "Ranger": ("<:Ranger:1475885739811278969>", 14),
    "Champion": ("<:Champion:1475887737050763326>", 15),
    "Master": ("<:Master:1475885935416705284>", 16),
    "Elite": ("<:Elite:1475886033878122538>", 17),
    "The Legend": ("<:TheLegend:1475886108775546940>", 18),
}

def rank_score(rank):
    return RANKS.get(rank, ("❌ NO RANK", 0))[1]

def rank_emoji(rank):
    return RANKS.get(rank, ("❌ NO RANK", 0))[0]

# =========================================================
# DATABASE FUNCTIONS
# =========================================================
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

def update_rank_db(standoff_id, mode, rank):
    if mode not in ["competitive", "allies", "duel"]:
        return False
    c.execute(f"UPDATE players SET {mode} = ? WHERE standoff_id = ?", (rank, standoff_id))
    conn.commit()
    return True

def update_kd_db(standoff_id, value):
    c.execute("UPDATE players SET kd = ? WHERE standoff_id = ?", (value, standoff_id))
    conn.commit()

def reset_player(standoff_id):
    c.execute("""
        UPDATE players
        SET competitive='❌ NO RANK',
            allies='❌ NO RANK',
            duel='❌ NO RANK',
            kd=0.0
        WHERE standoff_id=?
    """, (standoff_id,))
    conn.commit()

# =========================================================
# DAILY CODE
# =========================================================
daily_code = random.randint(1000, 9999)

@tasks.loop(hours=24)
async def daily_code_task():
    global daily_code
    daily_code = random.randint(1000, 9999)
    channel = bot.get_channel(DAILY_CHANNEL_ID)
    if channel:
        await channel.send(f"🎯 **Daily Code:** `{daily_code}`")

# =========================================================
# LEADERBOARD
# =========================================================
@tasks.loop(minutes=5)
async def leaderboard_task():
    channel = bot.get_channel(LEADERBOARD_CHANNEL_ID)
    if not channel:
        return

    players = get_all_players()
    if not players:
        return

    sorted_players = sorted(
        players,
        key=lambda x: rank_score(x[3]) + rank_score(x[4]) + rank_score(x[5]) + x[6],
        reverse=True
    )

    embed = discord.Embed(title="🏆 Top 10 Leaderboard", color=0xFFD700)

    for i, player in enumerate(sorted_players[:10], start=1):
        embed.add_field(
            name=f"{i}. {player[2]} ({player[0]})",
            value=f"Competitive: {rank_emoji(player[3])}\n"
                  f"Allies: {rank_emoji(player[4])}\n"
                  f"Duel: {rank_emoji(player[5])}\n"
                  f"K/D: {player[6]}",
            inline=False
        )

    async for msg in channel.history(limit=10):
        if msg.author == bot.user:
            await msg.delete()

    await channel.send(embed=embed)

# =========================================================
# COMMANDS
# =========================================================
@bot.tree.command(name="register", guild=GUILD_OBJECT)
async def register(interaction: discord.Interaction, standoff_id: str, name: str):
    if get_player(standoff_id):
        await interaction.response.send_message("Already registered.", ephemeral=True)
        return

    add_player(standoff_id, str(interaction.user.id), name)
    await interaction.response.send_message("Registered successfully.", ephemeral=True)


@bot.tree.command(name="stats", guild=GUILD_OBJECT)
async def stats(interaction: discord.Interaction, standoff_id: str):
    player = get_player(standoff_id)
    if not player:
        await interaction.response.send_message("Player not found.", ephemeral=True)
        return

    embed = discord.Embed(title=f"{player[2]}'s Stats", color=0x3498DB)
    embed.add_field(name="Standoff ID", value=player[0], inline=False)
    embed.add_field(name="Competitive", value=rank_emoji(player[3]), inline=True)
    embed.add_field(name="Allies", value=rank_emoji(player[4]), inline=True)
    embed.add_field(name="Duel", value=rank_emoji(player[5]), inline=True)
    embed.add_field(name="K/D", value=player[6], inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="update_rank", guild=GUILD_OBJECT)
async def update_rank(interaction: discord.Interaction, standoff_id: str, mode: str, rank: str):

    if rank not in RANKS:
        await interaction.response.send_message(
            "Invalid rank.\nAvailable:\n" + "\n".join(RANKS.keys()),
            ephemeral=True
        )
        return

    if not update_rank_db(standoff_id, mode.lower(), rank):
        await interaction.response.send_message(
            "Mode must be: competitive, allies, duel.",
            ephemeral=True
        )
        return

    await interaction.response.send_message("Rank updated successfully.")


@bot.tree.command(name="update_kd", guild=GUILD_OBJECT)
async def update_kd(interaction: discord.Interaction, standoff_id: str, value: float):
    update_kd_db(standoff_id, value)
    await interaction.response.send_message("K/D updated successfully.")


@bot.tree.command(name="remove", guild=GUILD_OBJECT)
async def remove(interaction: discord.Interaction, standoff_id: str):
    reset_player(standoff_id)
    await interaction.response.send_message("Player data reset.")


@bot.tree.command(name="code", guild=GUILD_OBJECT)
async def code(interaction: discord.Interaction):
    await interaction.response.send_message(f"🎯 Current Daily Code: `{daily_code}`")

# =========================================================
# STARTUP
# =========================================================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync(guild=GUILD_OBJECT)

    if not daily_code_task.is_running():
        daily_code_task.start()

    if not leaderboard_task.is_running():
        leaderboard_task.start()

# =========================================================
# RUN
# =========================================================
token = os.environ.get("DISCORD_TOKEN")

if token:
    bot.run(token)
else:
    print("DISCORD_TOKEN not set!")
