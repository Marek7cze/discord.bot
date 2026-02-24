import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

rank_emojis = {
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

@bot.command()
async def rank(ctx, rank_name: str):
    rank
