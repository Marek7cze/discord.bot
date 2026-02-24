import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

GUILD_ID = 1247900579586642021

conn = sqlite3.connect("player_stats.db")
c = conn.cursor()

def add_player(standoff_id, discord_id, name):
    c.execute("INSERT OR IGNORE INTO players (standoff_id, discord_id, name) VALUES (?, ?, ?)",
              (standoff_id, discord_id, name))
    conn.commit()

def get_player(standoff_id):
    c.execute("SELECT * FROM players WHERE standoff_id = ?", (standoff_id,))
    return c.fetchone()

class Register(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="register", description="Register your Standoff 2 account")
    @app_commands.describe(standoff_id="Your Standoff 2 ID", name="Your in-game name")
    async def register(self, interaction: discord.Interaction, standoff_id: str, name: str):
        if get_player(standoff_id):
            await interaction.response.send_message(f"Player {standoff_id} already registered.", ephemeral=True)
            return
        add_player(standoff_id, str(interaction.user.id), name)
        await interaction.response.send_message(f"✅ Registered {name} with Standoff ID {standoff_id}!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Register(bot))
