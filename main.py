import discord
from discord.ext import commands, tasks
import random
import datetime
import os
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
    app.run(host="0.0.0.0", port=8080)

# Start Flask in a separate thread
threading.Thread(target=run_flask).start()

# -----------------------------
# Discord Bot Setup
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True  # REQUIRED for reading messages/commands

bot = commands.Bot(command_prefix="/", intents=intents)

# -----------------------------
# Daily Code Generator
# -----------------------------
daily_code = random.randint(1000, 9999)

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    print(f"Today's code: {daily_code}")
    update_daily_code.start()  # start the daily code updater

@bot.command()
async def code(ctx):
    await ctx.send(f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}")

# Automatically update the code every 24 hours
@tasks.loop(hours=24)
async def update_daily_code():
    global daily_code
    daily_code = random.randint(1000, 9999)
    # Replace YOUR_CHANNEL_ID with the numeric ID of your Discord channel
    channel = bot.get_channel(1474476859210076294)
    if channel:
        await channel.send(f"Today's Access Code: `{daily_code}`\nDate: {datetime.date.today()}")

# -----------------------------
# Run the Bot
# -----------------------------
bot.run(os.getenv("DISCORD_TOKEN"))
import discord
from discord.ext import commands, tasks
from discord import app_commands
import sqlite3

# --- Bot setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# --- Database setup ---
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

# --- Helper functions ---
def get_player(discord_id):
    c.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
    return c.fetchone()

def update_player(discord_id, field, value):
    c.execute(f"UPDATE players SET {field} = ? WHERE discord_id = ?", (value, discord_id))
    conn.commit()

def add_player(discord_id, name):
    c.execute("INSERT OR IGNORE INTO players (discord_id, name, competitive, allies, duel, kd) VALUES (?, ?, '', '', '', 0)", (discord_id, name))
    conn.commit()

# --- Slash commands ---
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
        
        # Unpack player data
        _, name, competitive, allies, duel, kd = player

        # Create embed
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

# --- Add Cog ---
bot.tree.add_command(Stats(bot).stats)
bot.tree.add_command(Stats(bot).update)
bot.add_cog(Stats(bot))

# --- Run bot ---
bot.run("YOUR_BOT_TOKEN")
