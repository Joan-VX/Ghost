import discord
from discord.ext import commands

# ==========================================
# CONFIGURATION
# Replace this with your actual bot token
# ==========================================
TOKEN = "YOUR_BOT_TOKEN_HERE"

# Set up intents so the bot can see when messages are sent and read their text
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True 

# Initialize the bot with a standard prefix
bot = commands.Bot(command_prefix="-", intents=intents)


@bot.event
async def on_ready():
    print(f"🐭 Bot is online! Logged in as {bot.user.name}")


@bot.event
async def on_message(message: discord.Message):
    # 1. Ignore messages sent by bots (including itself) to avoid infinite loops
    if message.author.bot:
        return

    # 2. Convert the content to lowercase so it catches 'mouse', 'Mouse', 'MOUSE', etc.
    if "mouse" in message.content.lower():
        try:
            # Adds the mouse emoji reaction
            await message.add_reaction("🐭")
            print(f"Reacted to a mouse message from {message.author}")
        except discord.Forbidden:
            print(f"Missing permissions to add reactions in channel: {message.channel.name}")
        except discord.HTTPException as e:
            print(f"Failed to add reaction: {e}")

    # 3. CRITICAL: This allows prefix commands to work alongside on_message listeners
    await bot.process_commands(message)


# Example test command to ensure the bot is responsive
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong! 🏓")


if __name__ == "__main__":
    bot.run(TOKEN)
    async def setup(bot):
    await bot.add_cog(Random(bot))
