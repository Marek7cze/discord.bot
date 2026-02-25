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
# FLASK KEEP ALIVE (Production Safe)
# =========================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# =========================================================
# DISCORD CONFIG
# =========================================================
GUILD_ID = 1247900579586642021
DAILY_CHANNEL_ID = 1474476859210076294
LEADERBOARD_CHANNEL_ID = 1474813234795249734

GUILD_OBJECT = discord.Object(id=GUILD_ID)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================================================
# DATABASE (Thread Safe)
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

ALLOWED_FIELDS = {"competitive", "allies", "duel", "kd"}

def add_player(standoff_id, discord_id, name):
    c.execute(
        "INSERT OR IGNORE INTO players (standoff_id, discord_id, name) VALUES (?, ?, ?)",
        (standoff_id, discord_id, name)
    )
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
# RANKS
# =========================================================
RANKS = [
    "❌ NO RANK",
    "<:Bronze1:1475882755664384154>",
    "<:Bronze2:1475883215154712758>",
    "<:Bronze3:1475882893804044402>",
    "<:Bronze4:1475882954831167508>",
    "<:Silver1:1475887681454997739>",
    "<:Silver2:1475885246292430901>",
    "<:Silver3:1475885332128993342>",
    "<:Silver4:1475885397157478540>",
    "<:Gold1:1475887285202583605>",
    "<:Gold2:1475887345877389435>",
    "<:Gold3:1475887439456243815>",
    "<:Gold4:1475887516816248852>",
    "<:Phoenix:1475885669271474328>",
    "<:Ranger:1475885739811278969>",
    "<:Champion:1475887737050763326>",
    "<:Master:1475885935416705284>",
    "<:Elite:1475886033878122538>",
    "<:TheLegend:1475886108775546940>"
]

# =========================================================
# DAILY CODE SYSTEM
# =========================================================
daily_code = random.randint(1000, 9999)

async def reset_daily_code():
    await bot.wait_until_ready()
    global daily_code

    while not bot.is_closed():
        now = datetime.datetime.now()
        next_midnight = (now + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        sleep_seconds = (next_midnight - now).total_seconds()
        await asyncio.sleep(sleep_seconds)

        daily_code = random.randint(1000, 9999)

        channel = bot.get_channel(DAILY_CHANNEL_ID)
        if channel:
            await channel.send(
                f"🎯 **Today's Access Code:** `{daily_code}`\n📅 Date: {datetime.date.today()}"
            )

# =========================================================
# SLASH COMMANDS (Guild Only)
# =========================================================
@bot.tree.command(name="code", description="Get today's access code", guild=GUILD_OBJECT)
async def code(interaction: discord.Interaction):
    await interaction.response.send_message(f"Today's Access Code: `{daily_code}`")

@bot.tree.command(name="register", description="Register your Standoff 2 account", guild=GUILD_OBJECT)
@app_commands.describe(standoff_id="Your Standoff 2 ID", name="Your in-game name")
async def register(interaction: discord.Interaction, standoff_id: str, name: str):

    if get_player(standoff_id):
        await interaction.response.send_message(
            f"Player {standoff_id} already registered.",
            ephemeral=True
        )
        return

    add_player(standoff_id, str(interaction.user.id), name)

    await interaction.response.send_message(
        f"✅ Registered {name} with Standoff ID {standoff_id}!",
        ephemeral=True
    )

@bot.tree.command(name="stats", description="View stats", guild=GUILD_OBJECT)
@app_commands.describe(standoff_id="Standoff 2 ID", member="Discord member")
async def stats(interaction: discord.Interaction, standoff_id: str = None, member: discord.Member = None):

    if member:
        player = get_player_by_discord(str(member.id))
    elif standoff_id:
        player = get_player(standoff_id)
    else:
        await interaction.response.send_message("Provide a user or ID.", ephemeral=True)
        return

    if not player:
        await interaction.response.send_message("Player not found.", ephemeral=True)
        return

    _, _, name, competitive, allies, duel, kd = player

    embed = discord.Embed(title=f"{name}'s Stats", color=0x3498DB)
    embed.add_field(name="Competitive", value=competitive)
    embed.add_field(name="Allies", value=allies)
    embed.add_field(name="Duel", value=duel)
    embed.set_footer(text=f"K/D: {kd:.2f}")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="remove", description="Remove a player", guild=GUILD_OBJECT)
@app_commands.describe(standoff_id="Standoff 2 ID", member="Discord member")
async def remove(interaction: discord.Interaction, standoff_id: str = None, member: discord.Member = None):

    if member:
        player = get_player_by_discord(str(member.id))
    elif standoff_id:
        player = get_player(standoff_id)
    else:
        await interaction.response.send_message("Provide a user or ID.", ephemeral=True)
        return

    if not player:
        await interaction.response.send_message("Player not found.", ephemeral=True)
        return

    remove_player(player[0])
    await interaction.response.send_message(
        f"✅ Removed {player[2]} ({player[0]})"
    )

# =========================================================
# LEADERBOARD TASK
# =========================================================
leaderboard_message = None

@tasks.loop(minutes=5)
async def auto_leaderboard():
    global leaderboard_message

    channel = bot.get_channel(LEADERBOARD_CHANNEL_ID)
    if not channel:
        return

    c.execute("SELECT name, standoff_id, competitive, allies, duel, kd FROM players")
    players = c.fetchall()
    if not players:
        return

    rank_values = {rank: i for i, rank in enumerate(RANKS)}

    leaderboard_data = []
    for name, standoff_id, competitive, allies, duel, kd in players:
        score = (
            rank_values.get(competitive, 0)
            + rank_values.get(allies, 0)
            + rank_values.get(duel, 0)
            + kd
        )
        leaderboard_data.append((name, standoff_id, competitive, allies, duel, kd, score))

    leaderboard_data.sort(key=lambda x: x[6], reverse=True)

    embed = discord.Embed(title="🏆 All-Time Leaderboard", color=0xFFD700)

    for idx, (name, sid, comp, al, du, kd, score) in enumerate(leaderboard_data[:10], start=1):
        embed.add_field(
            name=f"{idx}. {name} ({sid})",
            value=f"{comp} | {al} | {du}\nK/D: {kd:.2f}",
            inline=False
        )

    if leaderboard_message:
        await leaderboard_message.edit(embed=embed)
    else:
        leaderboard_message = await channel.send(embed=embed)

# =========================================================
# CLEAN SYNC (REMOVES DUPLICATES PERMANENTLY)
# =========================================================
async def setup_hook():

    # Remove ALL global commands permanently
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()

    # Remove old guild commands
    bot.tree.clear_commands(guild=GUILD_OBJECT)

    # Sync fresh guild-only commands
    await bot.tree.sync(guild=GUILD_OBJECT)

    auto_leaderboard.start()
    bot.loop.create_task(reset_daily_code())

bot.setup_hook = setup_hook

# =========================================================
# RUN
# =========================================================
token = os.getenv("DISCORD_TOKEN")

if not token:
    print("DISCORD_TOKEN not set!")
else:
    bot.run(token)
