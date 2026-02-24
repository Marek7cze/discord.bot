# Temporary code to delete all guild commands and force a fresh sync
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    
    # Delete all registered commands in guild
    commands_list = await bot.tree.fetch_guild_commands(guild.id)
    for cmd in commands_list:
        await bot.tree.delete_command(cmd.id, guild=guild)
    print("🗑 All guild commands deleted")
    
    # Force sync
    await bot.tree.sync(guild=guild)
    print("✅ Commands re-synced")
