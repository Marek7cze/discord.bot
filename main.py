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

# =============================
# Flask Keep Alive (Railway)
# =============================
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080)).start()

# =============================
# IDs
# =============================
GUILD_ID = 1247900579586642021
DAILY_CHANNEL_ID = 1474476859210076294

# =============================
# Bot Setup
# =============================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =============================
# Database
# =============================
conn = sqlite3.connect("player_stats.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS players (
    discord_id TEXT PRIMARY KEY,
    name TEXT,
    competitive TEXT,
    allies TEXT,
    duel TEXT,
    kd REAL
)
""")
conn.commit()

def add_player(discord_id, name):
    c.execute(
        "INSERT OR IGNORE INTO players VALUES (?, ?, '', '', '', 0)",
        (discord_id, name)
    )
    conn.commit()

def get_player(discord_id):
    c.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
    return c.fetchone()

def update_player(discord_id, field, value):
    c.execute(f"UPDATE players SET {field} = ? WHERE discord_id = ?", (value, discord_id))
    conn.commit()

# =============================
# Daily Code
# =============================
daily_code = random.randint(1000, 9999)

async def reset_daily_code():
    global daily_code
    await bot.wait_until_ready()

    while True:
        now = datetime.datetime.now()
        next_midnight = (now + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        wait_time = (next_midnight - now).total_seconds()
        await asyncio.sleep(wait_time)

        daily_code = random.randint(1000, 9999)
        channel = bot.get_channel(DAILY_CHANNEL_ID)

        if channel:
            await channel.send(
                f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}"
            )

# Prefix command (optional)
@bot.command()
async def code(ctx):
    await ctx.send(f"Today's Access Code: `{daily_code}`")

# =============================
# Slash Commands (Guild Synced)
# =============================

@bot.tree.command(name="stats", description="View a player's stats", guild=discord.Object(id=GUILD_ID))
async def stats(interaction: discord.Interaction, member: discord.Member):

    add_player(str(member.id), member.name)
    player = get_player(str(member.id))

    if not player:
        await interaction.response.send_message("Player not found.", ephemeral=True)
        return

    _, name, competitive, allies, duel, kd = player

    embed = discord.Embed(
        title=f"{name}'s Stats",
        color=0x3498DB
    )

    embed.add_field(name="ID", value=member.id, inline=False)
    embed.add_field(
        name="Rank",
        value=f"Competitive – {competitive}\nAllies – {allies}\nDuel – {duel}",
        inline=False
    )
    embed.add_field(name="K/D", value=kd, inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="update", description="Update a player's stats", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(manage_roles=True)
async def update(
    interaction: discord.Interaction,
    member: discord.Member,
    field: str,
    value: str
):

    if field.lower() not in ["competitive", "allies", "duel", "kd"]:
        await interaction.response.send_message(
            "Field must be: competitive, allies, duel, kd",
            ephemeral=True
        )
        return

    if field.lower() == "kd":
        try:
            value = float(value)
        except:
            await interaction.response.send_message(
                "K/D must be a number.",
                ephemeral=True
            )
            return

    add_player(str(member.id), member.name)
    update_player(str(member.id), field.lower(), value)

    await interaction.response.send_message(
        f"{member.name}'s {field} updated to {value}."
    )

# =============================
# Ready Event
# =============================
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("Slash commands synced instantly.")
    except Exception as e:
        print("Sync error:", e)

    bot.loop.create_task(reset_daily_code())

# =============================
# Run
# =============================
token = os.getenv("DISCORD_TOKEN")

if token:
    bot.run(token)
else:
    print("DISCORD_TOKEN not set!")
