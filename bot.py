import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

STAFF_ROLES = {
    1524505452526833815,
    1524505551596290078,
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="-",
            intents=intents
        )

    async def setup_hook(self):
        print("🔄 Loading commands...")

        if not os.path.exists("./commands"):
            print("❌ commands folder not found")
            return

        for filename in os.listdir("./commands"):
            if filename.endswith(".py") and filename != "__init__.py":

                if filename == "tickets.py":
                    print("⏭️ Skipped commands.tickets")
                    continue

                extension = f"commands.{filename[:-3]}"

                try:
                    await self.load_extension(extension)
                    print(f"✅ Loaded {extension}")
                except Exception as e:
                    print(f"❌ Failed to load {extension}: {e}")

        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} slash commands.")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")


bot = MyBot()


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"📡 Connected to {len(bot.guilds)} server(s)")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required arguments.")

    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found.")

    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument.")

    elif isinstance(error, commands.CommandNotFound):
        return

    else:
        raise error


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable is not set.")


bot.run(TOKEN)
