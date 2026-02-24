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

def run_flask():
    app.run(host="0.0.0.0", port=8080, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()

# -----------------------------
# CONFIG
# -----------------------------
GUILD_ID = 1247900579586642021

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# DATABASE
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

# -----------------------------
# RANK EMOJIS (FOR NICKNAME)
# -----------------------------
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
# /setrank
# -----------------------------
@bot.tree.command(
    name="setrank",
    description="Set a rank emoji to a user",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(user="User to edit", rank="Rank name (Gold4 etc)")
async def setrank(interaction: discord.Interaction, user: discord.Member, rank: str):

    # Prevent timeout
    await interaction.response.defer(ephemeral=True)

    rank_key = rank.replace(" ", "")

    if rank_key not in rank_emojis:
        await interaction.followup.send(
            f"❌ Invalid rank. Available: {', '.join(rank_emojis.keys())}",
            ephemeral=True
        )
        return

    emoji = rank_emojis[rank_key]

    base_name = user.display_name.split(" | ")[0]
    new_nick = f"{base_name} | {emoji}"

    try:
        await user.edit(nick=new_nick)
        await interaction.followup.send(
            f"✅ Rank updated for {user.mention}",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Error: {e}",
            ephemeral=True
        )

# -----------------------------
# READY EVENT
# -----------------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print("Sync error:", e)

# -----------------------------
# RUN
# -----------------------------
token = os.getenv("DISCORD_TOKEN")

if token:
    bot.run(token)
else:
    print("DISCORD_TOKEN not set!")
