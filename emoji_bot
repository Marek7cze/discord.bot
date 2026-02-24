# emoji_bot/emoji_rank_bot.py
import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True  # Needed to edit nicknames

bot = commands.Bot(command_prefix="!", intents=intents)

# Mapping of rank names to your Discord emoji IDs
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

# Dynamically create a command for each rank
for rank_name, emoji in rank_emojis.items():
    @bot.command(name=rank_name.lower())
    async def rank_command(ctx, rank=rank_name, emoji=emoji):
        member = ctx.author
        # Keep the original nickname, remove old rank if present
        name_parts = member.display_name.split(" | ")
        base_name = name_parts[0]  # original nickname
        new_nick = f"{base_name} | {emoji}"
        try:
            await member.edit(nick=new_nick)
            await ctx.send(f"✅ Nickname updated: {new_nick}")
        except discord.Forbidden:
            await ctx.send("❌ Cannot change your nickname. Make sure my role is above yours and I have Manage Nicknames permission.")

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

# Run bot
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("DISCORD_TOKEN not set!")
