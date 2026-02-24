import discord
from discord.ext import commands, tasks
import asyncio
import sqlite3

LEADERBOARD_CHANNEL_ID = 1474813234795249734

conn = sqlite3.connect("player_stats.db")
c = conn.cursor()

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_update_leaderboard.start()

    def get_players(self):
        c.execute("SELECT name, standoff_id, competitive, allies, duel, kd FROM players")
        return c.fetchall()

    @tasks.loop(minutes=10)
    async def auto_update_leaderboard(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(LEADERBOARD_CHANNEL_ID)
        if not channel:
            print("Leaderboard channel not found!")
            return

        players = self.get_players()
        if not players:
            return

        # Example simple scoring system: sum of K/D + ranks (optional custom scoring)
        leaderboard_data = []
        for name, standoff_id, competitive, allies, duel, kd in players:
            score = kd  # Can improve: add rank points
            leaderboard_data.append((name, standoff_id, competitive, allies, duel, kd, score))

        leaderboard_data.sort(key=lambda x: x[6], reverse=True)

        embed = discord.Embed(title="🏆 All-Time Leaderboard", color=0xFFD700)
        for idx, (name, standoff_id, comp, allies_, duel_, kd, _) in enumerate(leaderboard_data[:10], start=1):
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
        print("✅ Leaderboard updated!")

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
