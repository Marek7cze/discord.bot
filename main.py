import discord
from discord.ext import commands, tasks
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

def run_flask():
    app.run(host="0.0.0.0", port=8080, use_reloader=False)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# -----------------------------
# Bot Setup
# -----------------------------
GUILD_ID = 1247900579586642021       # Your server ID
DAILY_CHANNEL_ID = 1474476859210076294
BUTTON_MESSAGE_CHANNEL_ID = 1369775581469872309
TARGET_CHANNEL_ID = 1247912571802222704
LEADERBOARD_CHANNEL_ID = 1474813234795249734

intents = discord.Intents.all()
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
        sleep_seconds = (next_midnight - now).total_seconds()
        await asyncio.sleep(sleep_seconds)
        daily_code = random.randint(1000, 9999)
        channel = bot.get_channel(DAILY_CHANNEL_ID)
        if channel:
            await channel.send(f"🎯 **Today's Access Code:** `{daily_code}`\n📅 Date: {datetime.date.today()}")

@bot.tree.command(name="code", description="Show today's code", guild=discord.Object(id=GUILD_ID))
async def code(interaction: discord.Interaction):
    await interaction.response.send_message(f"Today's Access Code: `{daily_code}`")

# -----------------------------
# Predefined Ranks
# -----------------------------
RANKS = [
 "NO RANK", "🟫 Bronze I", "🟫 Bronze II", "🟫 Bronze III", "🟫 Bronze IV",
 "⬜ Silver I", "⬜ Silver II", "⬜ Silver III", "⬜ Silver IV",
 "🟨 Gold I", "🟨 Gold II", "🟨 Gold III", "🟨 Gold IV",
 "🔥 Phoenix", "🏹 Ranger", "🏆 Champion", "👑 Master", "💎 Elite", "🌟 The Legend"
]

rank_emojis = {
    "Bronze1": "<:Bronze1:1475882755664384154>",
    "Bronze2": "<:Bronze2:1475883215154712758>",
    "Bronze3": "<:Bronze3:1475882893804044402>",
    "Bronze4": "<:Bronze4:1475882954831167508>",
    "Silver1": "<:Silver1:1475887681454997739>",
    "Silver2": "<:Silver2:1475885246292430901>",
    "Silver3": "<:Silver3:1475885332128993342>",
    "Silver4": "<:Silver4:1475885397157478540>",
    "Gold1": "<:Gold1:1475887285202583605>",
    "Gold2": "<:Gold2:1475887345877389435>",
    "Gold3": "<:Gold3:1475887439456243815>",
    "Gold4": "<:Gold4:1475887516816248852>",
    "Phoenix": "<:Phoenix:1475885669271474328>",
    "Ranger": "<:Ranger:1475885739811278969>",
    "Champion": "<:Champion:1475887737050763326>",
    "Master": "<:Master:1475885935416705284>",
    "Elite": "<:Elite:1475886033878122538>",
    "TheLegend": "<:TheLegend:1475886108775546940>"
}

# -----------------------------
# /register
# -----------------------------
@bot.tree.command(name="register", description="Register your Standoff 2 account", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(standoff_id="Your Standoff 2 ID", name="Your in-game name")
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
@app_commands.describe(standoff_id="Standoff 2 ID", member="Discord member")
async def stats(interaction: discord.Interaction, standoff_id: str = None, member: discord.Member = None):
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

    _, discord_id, name, competitive, allies, duel, kd = player
    embed = discord.Embed(title=f"{name}'s Stats", color=0x3498DB)
    embed.add_field(name="Standoff 2 ID", value=player[0], inline=False)
    embed.add_field(name="Competitive", value=competitive, inline=True)
    embed.add_field(name="Allies", value=allies, inline=True)
    embed.add_field(name="Duel", value=duel, inline=True)
    embed.set_footer(text=f"K/D: {kd:.2f}")
    await interaction.response.send_message(embed=embed)

# -----------------------------
# /update_rank
# -----------------------------
@bot.tree.command(name="update_rank", description="Update a player's rank", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(standoff_id="Standoff 2 ID", field="competitive/allies/duel", rank_value="Rank to assign")
async def update_rank(interaction: discord.Interaction, standoff_id: str, field: str, rank_value: str):
    if field.lower() not in ["competitive", "allies", "duel"] or rank_value not in RANKS:
        await interaction.response.send_message("Invalid field or rank.", ephemeral=True)
        return
    update_player(standoff_id, field.lower(), rank_value)
    await interaction.response.send_message(f"{field.capitalize()} updated to {rank_value} for {standoff_id}")

# -----------------------------
# /update_kd
# -----------------------------
@bot.tree.command(name="update_kd", description="Update a player's K/D", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(standoff_id="Standoff 2 ID", kd_value="New K/D value")
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
# /setrank
# -----------------------------
@bot.tree.command(name="setrank", description="Set a rank emoji to a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="User to change nickname", rank="Rank to assign")
async def setrank(interaction: discord.Interaction, user: discord.Member, rank: str):
    rank_key = rank.replace(" ", "").capitalize()
    if rank_key not in rank_emojis:
        await interaction.response.send_message(f"❌ Rank not found. Available: {', '.join(rank_emojis.keys())}", ephemeral=True)
        return
    emoji = rank_emojis[rank_key]
    base_name = user.display_name.split(" | ")[0]
    new_nick = f"{base_name} | {emoji}"
    try:
        await user.edit(nick=new_nick)
        await interaction.response.send_message(f"✅ {user.display_name} now has {emoji} for rank {rank_key}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Cannot change nickname. Check role position and permissions.", ephemeral=True)

# -----------------------------
# Auto-Updating Leaderboard
# -----------------------------
@tasks.loop(minutes=10)
async def update_leaderboard():
    await bot.wait_until_ready()
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
        comp_score = rank_values.get(competitive, 0)
        allies_score = rank_values.get(allies, 0)
        duel_score = rank_values.get(duel, 0)
        leaderboard_data.append((name, standoff_id, competitive, allies, duel, kd, comp_score+allies_score+duel_score+kd))
    leaderboard_data.sort(key=lambda x: x[6], reverse=True)
    embed = discord.Embed(title="🏆 All-Time Leaderboard", color=0xFFD700)
    for idx, (name, standoff_id, comp, allies_, duel_, kd, _) in enumerate(leaderboard_data[:10], start=1):
        embed.add_field(name=f"{idx}. {name} ({standoff_id})", value=f"Competitive: {comp} | Allies: {allies_} | Duel: {duel_}\nK/D: {kd:.2f}", inline=False)
    async for msg in channel.history(limit=20):
        if msg.author == bot.user and msg.embeds:
            await msg.delete()
    await channel.send(embed=embed)

# -----------------------------
# Bot Ready
# -----------------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    update_leaderboard.start()
    asyncio.create_task(reset_daily_code())
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("✅ Slash commands synced")
    except Exception as e:
        print("Sync error:", e)

# -----------------------------
# Run Bot
# -----------------------------
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("DISCORD_TOKEN not set!")
