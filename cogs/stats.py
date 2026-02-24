import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

GUILD_ID = 1247900579586642021

conn = sqlite3.connect("player_stats.db")
c = conn.cursor()

def get_player(standoff_id):
    c.execute("SELECT * FROM players WHERE standoff_id = ?", (standoff_id,))
    return c.fetchone()

def get_player_by_discord(discord_id):
    c.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
    return c.fetchone()

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="stats",
        description="View a player's stats"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(standoff_id="Standoff 2 ID", member="Discord user")
    async def stats(self, interaction: discord.Interaction, standoff_id: str = None, member: discord.Member = None):
        if member:
            player = get_player_by_discord(str(member.id))
            if not player:
                await interaction.response.send_message("Player not found for this Discord user.", ephemeral=True)
                return
        elif standoff_id:
            player = get_player(standoff_id)
            if not player:
                await interaction.response.send_message("Player not found for this Standoff ID.", ephemeral=True)
                return
        else:
            await interaction.response.send_message("Provide a Discord user or a Standoff ID.", ephemeral=True)
            return

        _, discord_id, name, competitive, allies, duel, kd = player
        embed = discord.Embed(title=f"{name}'s Stats", color=0x3498DB)
        embed.add_field(name="Standoff 2 ID", value=player[0], inline=False)
        embed.add_field(name="Competitive", value=competitive, inline=True)
        embed.add_field(name="Allies", value=allies, inline=True)
        embed.add_field(name="Duel", value=duel, inline=True)
        embed.set_footer(text=f"K/D: {kd:.2f} • Last updated")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))
