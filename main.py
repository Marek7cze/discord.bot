import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import datetime
import sqlite3
import os
from flask import Flask
import threading
import asyncio

# -----------------------------
# Flask Keep-Alive
# -----------------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

# -----------------------------
# Bot Setup
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# -----------------------------
# Database setup
# -----------------------------
conn = sqlite3.connect("player_stats.db")
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS players (
    discord_id TEXT PRIMARY KEY,
    name TEXT,
    competitive TEXT,
    allies TEXT,
    duel TEXT,
    kd REAL
)
''')
conn.commit()

def get_player(discord_id):
    c.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
    return c.fetchone()

def update_player(discord_id, field, value):
    c.execute(f"UPDATE players SET {field} = ? WHERE discord_id = ?", (value, discord_id))
    conn.commit()

def add_player(discord_id, name):
    c.execute("INSERT OR IGNORE INTO players (discord_id, name, competitive, allies, duel, kd) VALUES (?, ?, '', '', '', 0)", (discord_id, name))
    conn.commit()

# -----------------------------
# Daily Code
# -----------------------------
daily_code = random.randint(1000, 9999)
DAILY_CHANNEL_ID = 1474476859210076294  # Your channel ID

async def reset_daily_code_at_midnight():
    global daily_code
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.datetime.now()
        next_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_midnight = (next_midnight - now).total_seconds()
        await asyncio.sleep(seconds_until_midnight)
        daily_code = random.randint(1000, 9999)
        channel = bot.get_channel(DAILY_CHANNEL_ID)
        if channel:
            await channel.send(f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}")

@bot.command()
async def code(ctx):
    await ctx.send(f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}")

# -----------------------------
# Stats Cog
# -----------------------------
class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="stats", description="View a player's stats")
    async def stats(self, interaction: discord.Interaction, member: discord.Member):
        add_player(str(member.id), member.name)
        player = get_player(str(member.id))
        if not player:
            await interaction.response.send_message("Player not found.", ephemeral=True)
            return
        
        _, name, competitive, allies, duel, kd = player
        embed = discord.Embed(title=f"{name}'s Stats", color=0x3498DB)
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Rank", value=f"Competitive – {competitive}\nAllies – {allies}\nDuel – {duel}", inline=False)
        embed.add_field(name="K/D", value=kd, inline=False)
        embed.set_footer(text="Last updated • Server Stats")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="update", description="Update a player's stats (Staff only)")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def update(self, interaction: discord.Interaction, member: discord.Member, field: str, value: str):
        if field.lower() not in ["competitive", "allies", "duel", "kd"]:
            await interaction.response.send_message("Invalid field. Use: competitive, allies, duel, kd", ephemeral=True)
            return
        if field.lower() == "kd":
            try:
                value = float(value)
            except:
                await interaction.response.send_message("K/D must be a number.", ephemeral=True)
                return
        add_player(str(member.id), member.name)
        update_player(str(member.id), field.lower(), value)
        await interaction.response.send_message(f"{member.name}'s {field} updated to {value}.")

bot.add_cog(Stats(bot))

# -----------------------------
# Bot Ready
# -----------------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    print(f"Today's code: {daily_code}")
    try:
        await bot.tree.sync()
        print("Slash commands synced.")
    except Exception as e:
        print("Error syncing commands:", e)
    bot.loop.create_task(reset_daily_code_at_midnight())

# -----------------------------
# Run bot
# -----------------------------
bot.run(os.getenv("DISCORD_TOKEN"))
