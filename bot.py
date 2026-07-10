import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="-",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    # Load all command files from the commands folder
    for filename in os.listdir("./commands"):
        if filename.endswith(".py"):
            extension = f"commands.{filename[:-3]}"

            try:
                await bot.load_extension(extension)
                print(f"Loaded {extension}")
            except commands.ExtensionAlreadyLoaded:
                pass
            except Exception as e:
                print(f"Failed to load {extension}: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(e)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required arguments.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument.")
    else:
        raise error


bot.run(TOKEN)
