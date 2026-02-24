import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

conn = sqlite3.connect("player_stats.db")
c = conn.cursor()

def get_player(standoff_id):
    c.execute("SELECT * FROM players WHERE standoff_id = ?", (standoff_id,))
    return c.fetchone()

def update_player(standoff_id, field, value):
    c.execute(f"UPDATE players SET {field} = ? WHERE standoff_id = ?", (value, standoff_id))
    conn.commit()

class UpdateKD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="update_kd", description="Update a player's K/D")
    @app_commands.describe(standoff_id="Standoff 2 ID", kd_value="New K/D value")
    async def update_kd(self, interaction: discord.Interaction, standoff_id: str, kd_value: float):
        if not 0.0 <= kd_value <= 1000.0:
            await interaction.response.send_message("K/D must be between 0.00 and 1000.00", ephemeral=True)
            return
        player = get_player(standoff_id)
        if not player:
            await interaction.response.send_message("Player not found.", ephemeral=True)
            return
        update_player(standoff_id, "kd", kd_value)
        await interaction.response.send_message(f"K/D updated to {kd_value:.2f} for {standoff_id}")

async def setup(bot):
    await bot.add_cog(UpdateKD(bot))
