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
GUILD_ID = 1247900579586642021
DAILY_CHANNEL_ID = 1474476859210076294

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
    kd REAL DEFAULT 0.00,
    competitive_image TEXT DEFAULT 'https://i.imgur.com/mlH9Gt8.png',
    allies_image TEXT DEFAULT 'https://i.imgur.com/LPvuDk7.png',
    duel_image TEXT DEFAULT 'https://i.imgur.com/Om1vlem.png'
)
""")
conn.commit()

def add_player(standoff_id, discord_id, name):
    c.execute("""
    INSERT OR IGNORE INTO players 
    (standoff_id, discord_id, name) VALUES (?, ?, ?)
    """, (standoff_id, discord_id, name))
    conn.commit()

def get_player(standoff_id):
    c.execute("SELECT * FROM players WHERE standoff_id = ?", (standoff_id,))
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
        next_midnight = (now + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        await asyncio.sleep((next_midnight - now).total_seconds())
        daily_code = random.randint(1000, 9999)
        channel = bot.get_channel(DAILY_CHANNEL_ID)
        if channel:
            await channel.send(f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}")

@bot.command()
async def code(ctx):
    await ctx.send(f"Today's Access Code: `{daily_code}`")

# -----------------------------
# Stats Slash Commands
# -----------------------------
@bot.tree.command(name="stats", description="View a player's Standoff 2 stats", guild=discord.Object(id=GUILD_ID))
async def stats(interaction: discord.Interaction, standoff_id: str):
    player = get_player(standoff_id)
    if not player:
        await interaction.response.send_message("Player not found.", ephemeral=True)
        return

    _, discord_id, name, competitive, allies, duel, kd, comp_img, allies_img, duel_img = player

    embed = discord.Embed(title=f"{name}'s Stats", color=0x3498DB)

    embed.add_field(name="ID", value=standoff_id, inline=False)
    embed.add_field(name="Competitive", value=f"{competitive}", inline=True)
    embed.set_thumbnail(url=comp_img)
    embed.add_field(name="Allies", value=f"{allies}", inline=True)
    embed.set_image(url=allies_img)
    embed.add_field(name="Duel", value=f"{duel}", inline=True)
    embed.set_footer(text=f"K/D: {kd:.2f} • Last updated")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="update", description="Update a player's Standoff 2 stats", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(manage_roles=True)
async def update(interaction: discord.Interaction, standoff_id: str, field: str, value: str):
    player = get_player(standoff_id)
    if not player:
        await interaction.response.send_message("Player not found.", ephemeral=True)
        return

    if field.lower() in ["competitive", "allies", "duel"]:
        # Allow editing text or image URL
        if value.startswith("http"):
            # It's an image
            field_name = f"{field.lower()}_image"
        else:
            # It's rank text
            field_name = field.lower()
    elif field.lower() == "kd":
        field_name = "kd"
        try:
            value = float(value)
        except:
            await interaction.response.send_message("K/D must be a number.", ephemeral=True)
            return
    else:
        await interaction.response.send_message("Invalid field. Use: competitive, allies, duel, kd", ephemeral=True)
        return

    update_player(standoff_id, field_name, value)
    await interaction.response.send_message(f"{field} updated for {standoff_id} to {value}")

# -----------------------------
# Ready Event
# -----------------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("Slash commands synced!")
    except Exception as e:
        print("Sync error:", e)

    bot.loop.create_task(reset_daily_code())

# -----------------------------
# Run
# -----------------------------
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("DISCORD_TOKEN not set!")
# -----------------------------
# Register command
# -----------------------------
@bot.tree.command(name="register", description="Register your Standoff 2 account", guild=discord.Object(id=GUILD_ID))
async def register(interaction: discord.Interaction, standoff_id: str, name: str):
    # Check if already registered
    existing = get_player(standoff_id)
    if existing:
        await interaction.response.send_message(f"Player {standoff_id} is already registered.", ephemeral=True)
        return

    # Add player with defaults
    c.execute("""
        INSERT INTO players 
        (standoff_id, discord_id, name, competitive, allies, duel, kd, competitive_image, allies_image, duel_image)
        VALUES (?, ?, ?, 'RANK EMPTY', 'RANK EMPTY', 'RANK EMPTY', 0.00, 
                'https://i.imgur.com/mlH9Gt8.png', 
                'https://i.imgur.com/LPvuDk7.png', 
                'https://i.imgur.com/Om1vlem.png')
    """, (standoff_id, str(interaction.user.id), name))
    conn.commit()

    await interaction.response.send_message(f"✅ Registered {name} with Standoff ID {standoff_id}!", ephemeral=True)
    @bot.tree.command(name="stats", description="View a player's Standoff 2 stats", guild=discord.Object(id=GUILD_ID))
async def stats(interaction: discord.Interaction, member: discord.Member = None, standoff_id: str = None):
    if member:
        # Look up Standoff ID by Discord ID
        c.execute("SELECT * FROM players WHERE discord_id = ?", (str(member.id),))
        player = c.fetchone()
    elif standoff_id:
        player = get_player(standoff_id)
    else:
        await interaction.response.send_message("You must provide a Discord user or a Standoff ID.", ephemeral=True)
        return

    if not player:
        await interaction.response.send_message("Player not found.", ephemeral=True)
        return

    _, discord_id, name, competitive, allies, duel, kd, comp_img, allies_img, duel_img = player

    embed = discord.Embed(title=f"{name}'s Stats", color=0x3498DB)
    embed.add_field(name="ID", value=standoff_id if standoff_id else "Unknown", inline=False)
    embed.add_field(name="Competitive", value=competitive, inline=True)
    embed.set_thumbnail(url=comp_img)
    embed.add_field(name="Allies", value=allies, inline=True)
    embed.set_image(url=allies_img)
    embed.add_field(name="Duel", value=duel, inline=True)
    embed.set_footer(text=f"K/D: {kd:.2f} • Last updated")

    await interaction.response.send_message(embed=embed)
