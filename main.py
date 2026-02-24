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
# Bot setup
# -----------------------------
GUILD_ID = 1247900579586642021
DAILY_CHANNEL_ID = 1474476859210076294
LEADERBOARD_CHANNEL_ID = 1474813234795249734

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
# Ranks
# -----------------------------
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

# -----------------------------
