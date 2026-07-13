import discord
from discord.ext import commands


class Random(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bots
        if message.author.bot:
            return

        # React with 🐭 whenever someone says "mouse"
        if "mouse" in message.content.lower():
            try:
                await message.add_reaction("🐭")
            except (discord.Forbidden, discord.HTTPException):
                pass

        # Allow other prefix commands to work
        await self.bot.process_commands(message)

    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.send("Pong! 🏓")


async def setup(bot):
    await bot.add_cog(Random(bot))
