import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

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
    competitive TEXT DEFAULT 'RANK EMPTY',
    allies TEXT DEFAULT 'RANK EMPTY',
    duel TEXT DEFAULT 'RANK EMPTY',
    kd REAL DEFAULT 0.00
)
""")
conn.commit()

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

# -----------------------------
# Cog
# -----------------------------
GUILD_ID = 1247900579586642021  # Replace with your server ID

class Register(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Register Cog loaded")

    # -----------------------------
    # /register command
    # -----------------------------
    @app_commands.command(
        name="register",
        description="Register your Standoff 2 account",
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(standoff_id="Your Standoff 2 ID", name="Your in-game name")
    async def register(self, interaction: discord.Interaction, standoff_id: str, name: str):
        if get_player(standoff_id):
            await interaction.response.send_message(
                f"Player {standoff_id} is already registered.", ephemeral=True
            )
            return
        add_player(standoff_id, str(interaction.user.id), name)
        await interaction.response.send_message(
            f"✅ Registered {name} with Standoff ID {standoff_id}!", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Register(bot))
