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
GUILD_ID = 1247900579586642021       # Your server ID
DAILY_CHANNEL_ID = 1474476859210076294  # Daily code channel ID
BUTTON_MESSAGE_CHANNEL_ID = 1369775581469872309  # Channel to send the button in
TARGET_CHANNEL_ID = 1247912571802222704         # Channel the button links to
LEADERBOARD_CHANNEL_ID = 1474813234795249734   # Channel for leaderboard

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
 "NO RANK", "🟫 Bronze I", "🟫 Bronze II", "🟫 Bronze III", "🟫 Bronze IV",
 "⬜ Silver I", "⬜ Silver II", "⬜ Silver III", "⬜ Silver IV",
 "🟨 Gold I", "🟨 Gold II", "🟨 Gold III", "🟨 Gold IV",
 "🔥 Phoenix", "🏹 Ranger", "🏆 Champion", "👑 Master", "💎 Elite", "🌟 The Legend"
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
# Auto-Refresh Button Task
# -----------------------------
async def auto_refresh_button():
    await bot.wait_until_ready()
    channel = bot.get_channel(BUTTON_MESSAGE_CHANNEL_ID)
    if channel is None:
        print("Button channel not found!")
        return

    while True:
        button_exists = False
        async for msg in channel.history(limit=50):
            if msg.author == bot.user and msg.embeds:
                button_exists = True
                break

        if not button_exists:
            channel_link = f"https://discord.com/channels/{GUILD_ID}/{TARGET_CHANNEL_ID}"
            button = discord.ui.Button(label="Go to Channel", url=channel_link)
            view = discord.ui.View()
            view.add_item(button)
            await channel.send("Click the button to go to the channel!", view=view)
            print("✅ Button message reposted!")

        # Check every 5 minutes
        await asyncio.sleep(300)

# -----------------------------
# /leaderboard
# -----------------------------
@bot.tree.command(name="leaderboard", description="Show top players leaderboard", guild=discord.Object(id=GUILD_ID))
async def leaderboard(interaction: discord.Interaction):
    c.execute("SELECT name, competitive, allies, duel, kd FROM players")
    players = c.fetchall()
    
    if not players:
        await interaction.response.send_message("No players registered yet.", ephemeral=True)
        return

    # Map ranks to numeric values
    rank_values = {rank: i for i, rank in enumerate(RANKS)}

    leaderboard_data = []
    for name, competitive, allies, duel, kd in players:
        comp_score = rank_values.get(competitive, 0)
        allies_score = rank_values.get(allies, 0)
        duel_score = rank_values.get(duel, 0)
        total_score = comp_score + allies_score + duel_score + kd  # K/D adds to ranking
        leaderboard_data.append((name, competitive, allies, duel, kd, total_score))

    # Sort descending by total_score
    leaderboard_data.sort(key=lambda x: x[5], reverse=True)

    # Prepare embed
    embed = discord.Embed(title="🏆 All-Time Leaderboard", color=0xFFD700)
    for idx, (name, comp, allies_, duel_, kd, score) in enumerate(leaderboard_data[:10], start=1):
        embed.add_field(
            name=f"{idx}. {name}",
            value=f"Competitive: {comp} | Allies: {allies_} | Duel: {duel_} | K/D: {kd:.2f}",
            inline=False
        )

    # Send leaderboard in the dedicated channel
    leaderboard_channel = bot.get_channel(LEADERBOARD_CHANNEL_ID)
    if leaderboard_channel:
        await leaderboard_channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Leaderboard posted in <#{LEADERBOARD_CHANNEL_ID}>", ephemeral=True)
    else:
        await interaction.response.send_message("Leaderboard channel not found!", ephemeral=True)

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

    if not hasattr(bot, "daily_task_started"):
        bot.loop.create_task(reset_daily_code())
        bot.daily_task_started = True

    if not hasattr(bot, "button_task_started"):
        bot.loop.create_task(auto_refresh_button())
        bot.button_task_started = True

# -----------------------------
# Run Bot
# -----------------------------
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("DISCORD_TOKEN not set!")
