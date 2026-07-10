import discord
from discord import app_commands
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# Slash command
@bot.tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


# Prefix command system
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content == "-ping":
        await message.channel.send("Pong!")

    if message.content == "-hello":
        await message.channel.send(
            f"Hello {message.author.mention}!"
        )


bot.run(TOKEN)
