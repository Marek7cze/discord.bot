import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

GUILD_ID = 1247900579586642021

# Database setup
conn = sqlite3.connect("player_stats.db")
c = conn.cursor()

def update_player(standoff_id, field, value):
    c.execute(f"UPDATE players SET {field} = ? WHERE standoff_id = ?", (value, standoff_id))
    conn.commit()

class UpdateRank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    RANKS = [
        "NO RANK", "🟫 Bronze I", "🟫 Bronze II", "🟫 Bronze III", "🟫 Bronze IV",
        "⬜ Silver I", "⬜ Silver II", "⬜ Silver III", "⬜ Silver IV",
        "🟨 Gold I", "🟨 Gold II", "🟨 Gold III", "🟨 Gold IV",
        "🔥 Phoenix", "🏹 Ranger", "🏆 Champion", "👑 Master", "💎 Elite", "🌟 The Legend"
    ]

    @app_commands.command(
        name="update_rank",
        description="Update a player's rank"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(
        standoff_id="Standoff 2 ID",
        field="Which field to update: competitive, allies, duel",
        rank_value="The rank to assign"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def update_rank(self, interaction: discord.Interaction, standoff_id: str, field: str, rank_value: str):
        if field.lower() not in ["competitive", "allies", "duel"]:
            await interaction.response.send_message("Field must be: competitive, allies, duel", ephemeral=True)
            return
        if rank_value not in self.RANKS:
            await interaction.response.send_message(f"Invalid rank. Choose from: {', '.join(self.RANKS)}", ephemeral=True)
            return
        update_player(standoff_id, field.lower(), rank_value)
        await interaction.response.send_message(f"{field.capitalize()} updated to {rank_value} for {standoff_id}")

async def setup(bot):
    await bot.add_cog(UpdateRank(bot))
