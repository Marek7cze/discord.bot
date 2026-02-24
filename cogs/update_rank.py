import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

conn = sqlite3.connect("player_stats.db")
c = conn.cursor()

def update_player(standoff_id, field, value):
    c.execute(f"UPDATE players SET {field} = ? WHERE standoff_id = ?", (value, standoff_id))
    conn.commit()

class UpdateRank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="update_rank", description="Update a player's rank")
    @app_commands.describe(standoff_id="Standoff 2 ID", field="competitive, allies, duel", rank_value="Rank to assign")
    async def update_rank(self, interaction: discord.Interaction, standoff_id: str, field: str, rank_value: str):
        if field.lower() not in ["competitive", "allies", "duel"]:
            await interaction.response.send_message("Field must be: competitive, allies, duel", ephemeral=True)
            return
        update_player(standoff_id, field.lower(), rank_value)
        await interaction.response.send_message(f"{field.capitalize()} updated to {rank_value} for {standoff_id}")

async def setup(bot):
    await bot.add_cog(UpdateRank(bot))
