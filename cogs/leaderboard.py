import discord
from discord.ext import commands, tasks
from discord import app_commands
import sqlite3
import asyncio

GUILD_ID = 1247900579586642021
LEADERBOARD_CHANNEL_ID = 1474813234795249734  # Your leaderboard channel
RANKS = [
 "NO RANK", "🟫 Bronze I", "🟫 Bronze II", "🟫 Bronze III", "🟫 Bronze IV",
 "⬜ Silver I", "⬜ Silver II", "⬜ Silver III", "⬜ Silver IV",
 "🟨 Gold I", "🟨 Gold II", "🟨 Gold III", "🟨 Gold IV",
 "🔥 Phoenix", "🏹 Ranger", "🏆 Champion", "👑 Master", "💎 Elite", "🌟 The Legend"
]

conn = sqlite3.connect("player_stats.db")
c = conn.cursor()

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_leaderboard.start()

    @tasks.loop(minutes=10)
    async def update_leaderboard(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(LEADERBOARD_CHANNEL_ID)
        if channel is None:
            print("Leaderboard channel not found!")
            return

        c.execute("SELECT name, standoff_id, competitive, allies, duel, kd FROM players")
        players = c.fetchall()
        if not players:
            return

        rank_values = {rank: i for i, rank in enumerate(RANKS)}
        leaderboard_data = []
        for name, standoff_id, competitive, allies, duel, kd in players:
            comp_score = rank_values.get(competitive, 0)
            allies_score = rank_values.get(allies, 0)
            duel_score = rank_values.get(duel, 0)
            total_score = comp_score + allies_score + duel_score + kd
            leaderboard_data.append((name, standoff_id, competitive, allies, duel, kd, total_score))

        leaderboard_data.sort(key=lambda x: x[6], reverse=True)
        embed = discord.Embed(title="🏆 All-Time Leaderboard", color=0xFFD700)

        for idx, (name, standoff_id, comp, allies_, duel_, kd, score) in enumerate(leaderboard_data[:10], start=1):
            embed.add_field(
                name=f"{idx}. {name} ({standoff_id})",
                value=f"Competitive: {comp} | Allies: {allies_} | Duel: {duel_}\nK/D: {kd:.2f}",
                inline=False
            )

        # Delete previous leaderboard messages sent by bot
        async for msg in channel.history(limit=20):
            if msg.author == self.bot.user and msg.embeds:
                await msg.delete()

        await channel.send(embed=embed)

    @update_leaderboard.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
