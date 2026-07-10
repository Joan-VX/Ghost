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


# Slash /say command
@bot.tree.command(name="say", description="Send a message to a channel")
@app_commands.describe(
    message="The message to send",
    channel="The channel to send the message in",
    embed="Send as an embed?"
)
async def say(
    interaction: discord.Interaction,
    message: str,
    channel: discord.TextChannel,
    embed: bool
):
    if embed:
        embed_message = discord.Embed(
            description=message,
            color=discord.Color.blue()
        )
        await channel.send(embed=embed_message)
    else:
        await channel.send(message)

    await interaction.response.send_message(
        "✅ Message sent!",
        ephemeral=True
    )


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("-say "):
        text = message.content[5:]

        # Delete the command message
        await message.delete()

        # Send the actual message
        await message.channel.send(text)


bot.run(TOKEN)
