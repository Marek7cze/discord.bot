import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = 1247900579586642021

# Map of rank names → emoji IDs
RANK_EMOJIS = {
    "Bronze1": "<:Bronze1:1475882755664384154>",
    "Bronze2": "<:Bronze2:1475883215154712758>",
    "Bronze3": "<:Bronze3:1475882893804044402>",
    "Bronze4": "<:Bronze4:1475882954831167508>",
    "Silver1": "<:Silver1:1475887681454997739>",
    "Silver2": "<:Silver2:1475885246292430901>",
    "Silver3": "<:Silver3:1475885332128993342>",
    "Silver4": "<:Silver4:1475885397157478540>",
    "Gold1": "<:Gold1:1475887285202583605>",
    "Gold2": "<:Gold2:1475887345877389435>",
    "Gold3": "<:Gold3:1475887439456243815>",
    "Gold4": "<:Gold4:1475887516816248852>",
    "Phoenix": "<:Phoenix:1475885669271474328>",
    "Ranger": "<:Ranger:1475885739811278969>",
    "Champion": "<:Champion:1475887737050763326>",
    "Master": "<:Master:1475885935416705284>",
    "Elite": "<:Elite:1475886033878122538>",
    "TheLegend": "<:TheLegend:1475886108775546940>"
}

class SetRank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="setrank",
        description="Set a rank emoji to a user"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(user="The user to change nickname", rank="The rank to assign")
    async def setrank(self, interaction: discord.Interaction, user: discord.Member, rank: str):
        rank = rank.replace(" ", "").capitalize()
        if rank not in RANK_EMOJIS:
            await interaction.response.send_message(
                f"❌ Rank not found. Available ranks: {', '.join(RANK_EMOJIS.keys())}",
                ephemeral=True
            )
            return

        emoji = RANK_EMOJIS[rank]

        # Keep part of nickname before " | " if exists
        name_parts = user.display_name.split(" | ")
        base_name = name_parts[0]
        new_nick = f"{base_name} | {emoji}"

        try:
            await user.edit(nick=new_nick)
            await interaction.response.send_message(
                f"✅ {user.display_name} now has {emoji} for rank {rank}"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Cannot change nickname. Make sure my role is above theirs and I have Manage Nicknames permission.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(SetRank(bot))
