import discord
from discord.ext import commands, tasks
from discord import app_commands
import sqlite3
import os
import asyncio

# -----------------------------
# Bot setup
# -----------------------------
GUILD_ID = 1247900579586642021  # Replace with your server ID
LEADERBOARD_CHANNEL_ID = 1474813234795249734  # Replace with your leaderboard channel

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# Database setup
# -----------------------------
conn = sqlite3.connect("player_stats.db")
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

def get_player(standoff_id):
    c.execute("SELECT * FROM players WHERE standoff_id = ?", (standoff_id,))
    return c.fetchone()

def get_player_by_discord(discord_id):
    c.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
    return c.fetchone()

def remove_player(standoff_id):
    c.execute("DELETE FROM players WHERE standoff_id = ?", (standoff_id,))
    conn.commit()

# -----------------------------
# Leaderboard update
# -----------------------------
RANKS = [
 "❌ NO RANK", "🟫 Bronze I", "🟫 Bronze II", "🟫 Bronze III", "🟫 Bronze IV",
 "⬜ Silver I", "⬜ Silver II", "⬜ Silver III", "⬜ Silver IV",
 "🟨 Gold I", "🟨 Gold II", "🟨 Gold III", "🟨 Gold IV",
 "🔥 Phoenix", "🏹 Ranger", "🏆 Champion", "👑 Master", "💎 Elite", "🌟 The Legend"
]

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

    rank_values = {rank: i for i, rank in enumerate(RANKS)}
    leaderboard_data = []
    for name, standoff_id, competitive, allies, duel, kd in players:
        comp_score = rank_values.get(competitive, 0)
        allies_score = rank_values.get(allies, 0)
        duel_score = rank_values.get(duel, 0)
        total_score = comp_score + allies_score + duel_score + kd
        leaderboard_data.append((name, standoff_id, competitive, allies, duel, kd, total_score))

    leaderboard_data.sort(key=lambda x: x[6], reverse=True)
    embed = discord.Embed(title="🏆 All-Time Leaderboard", color=0xFFD700)
    for idx, (name, standoff_id, comp, allies_, duel_, kd, score) in enumerate(leaderboard_data[:10], start=1):
        embed.add_field(name=f"{idx}. {name} ({standoff_id})",
                        value=f"Competitive: {comp} | Allies: {allies_} | Duel: {duel_}\nK/D: {kd:.2f}",
                        inline=False)
    # Delete previous leaderboard messages sent by bot
    async for msg in channel.history(limit=20):
        if msg.author == bot.user and msg.embeds:
            await msg.delete()
    await channel.send(embed=embed)

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

    # Update leaderboard immediately after removal
    await auto_leaderboard()

# -----------------------------
# Bot ready
# -----------------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    try:
        guild_obj = discord.Object(id=GUILD_ID)
        await bot.tree.sync(guild=guild_obj)
        print("✅ Slash commands synced")
    except Exception as e:
        print("Sync error:", e)

    if not auto_leaderboard.is_running():
        auto_leaderboard.start()

# -----------------------------
# Run bot
# -----------------------------
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("DISCORD_TOKEN not set!")
