import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

ALLOWED_ROLES = {
    1524505452526833815,
    1524505522815111238,
}


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def allowed(self, member: discord.Member):
        return any(role.id in ALLOWED_ROLES for role in member.roles)

    # =======================
    # KICK
    # =======================

    @app_commands.command(name="kick", description="Kick a member")
    async def slash_kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided"
    ):
        if not self.allowed(interaction.user):
            return await interaction.response.send_message(
                "❌ You don't have permission.",
                ephemeral=True
            )

        if not interaction.guild.me.guild_permissions.kick_members:
            return await interaction.response.send_message(
                "❌ I don't have permission to kick members.",
                ephemeral=True
            )

        await member.kick(reason=reason)
        await interaction.response.send_message(
            f"✅ {member.mention} was kicked.\nReason: {reason}"
        )

    @commands.command(name="kick")
    async def kick(
        self,
        ctx,
        member: discord.Member,
        *,
        reason="No reason provided"
    ):
        if not self.allowed(ctx.author):
            return await ctx.send("❌ You don't have permission.")

        await member.kick(reason=reason)
        await ctx.send(f"✅ {member.mention} was kicked.")

    # =======================
    # BAN
    # =======================

    @app_commands.command(name="ban", description="Ban a member")
    async def slash_ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided"
    ):
        if not self.allowed(interaction.user):
            return await interaction.response.send_message(
                "❌ You don't have permission.",
                ephemeral=True
            )

        await member.ban(reason=reason)
        await interaction.response.send_message(
            f"🔨 {member.mention} was banned."
        )

    @commands.command(name="ban")
    async def ban(
        self,
        ctx,
        member: discord.Member,
        *,
        reason="No reason provided"
    ):
        if not self.allowed(ctx.author):
            return await ctx.send("❌ You don't have permission.")

        await member.ban(reason=reason)
        await ctx.send(f"🔨 {member.mention} was banned.")

    # =======================
    # TIMEOUT
    # =======================

    @app_commands.command(name="timeout", description="Timeout a member")
    async def slash_timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        minutes: int,
        reason: str = "No reason provided"
    ):
        if not self.allowed(interaction.user):
            return await interaction.response.send_message(
                "❌ You don't have permission.",
                ephemeral=True
            )

        await member.timeout(
            timedelta(minutes=minutes),
            reason=reason
        )

        await interaction.response.send_message(
            f"🔇 {member.mention} has been timed out for **{minutes}** minute(s).\nReason: **{reason}**"
        )

    @commands.command(name="timeout")
    async def timeout(
        self,
        ctx,
        member: discord.Member,
        minutes: int,
        *,
        reason="No reason provided"
    ):
        if not self.allowed(ctx.author):
            return await ctx.send("❌ You don't have permission.")

        await member.timeout(
            timedelta(minutes=minutes),
            reason=reason
        )

        await ctx.send(
            f"🔇 {member.mention} has been timed out for **{minutes}** minute(s)."
        )

    # =======================
    # UNTIMEOUT
    # =======================

    @app_commands.command(name="untimeout", description="Remove a timeout")
    async def slash_untimeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):
        if not self.allowed(interaction.user):
            return await interaction.response.send_message(
                "❌ You don't have permission.",
                ephemeral=True
            )

        await member.timeout(None)

        await interaction.response.send_message(
            f"✅ Removed timeout from {member.mention}."
        )

    @commands.command(name="untimeout")
    async def untimeout(
        self,
        ctx,
        member: discord.Member
    ):
        if not self.allowed(ctx.author):
            return await ctx.send("❌ You don't have permission.")

        await member.timeout(None)
        await ctx.send(f"✅ Removed timeout from {member.mention}.")

    # =======================
    # CLEAR
    # =======================

    @app_commands.command(name="clear", description="Delete messages")
    async def slash_clear(
        self,
        interaction: discord.Interaction,
        amount: int
    ):
        if not self.allowed(interaction.user):
            return await interaction.response.send_message(
                "❌ You don't have permission.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        deleted = await interaction.channel.purge(limit=amount)

        await interaction.followup.send(
            f"🗑️ Deleted **{len(deleted)}** messages.",
            ephemeral=True
        )

    @commands.command(name="clear")
    async def clear(
        self,
        ctx,
        amount: int
    ):
        if not self.allowed(ctx.author):
            return await ctx.send("❌ You don't have permission.")

        deleted = await ctx.channel.purge(limit=amount)

        msg = await ctx.send(f"🗑️ Deleted **{len(deleted)}** messages.")
        await msg.delete(delay=5)

    # =======================
    # SAY
    # =======================

    @app_commands.command(name="say", description="Send a message")
    async def slash_say(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str,
        embed: bool = False
    ):
        if not self.allowed(interaction.user):
            return await interaction.response.send_message(
                "❌ You don't have permission.",
                ephemeral=True
            )

        if embed:
            em = discord.Embed(
                description=message,
                color=discord.Color.blue()
            )
            await channel.send(embed=em)
        else:
            await channel.send(message)

        await interaction.response.send_message(
            "✅ Message sent!",
            ephemeral=True
        )

    @commands.command(name="say")
    async def say(
        self,
        ctx,
        channel: discord.TextChannel,
        *,
        message
    ):
        if not self.allowed(ctx.author):
            return await ctx.send("❌ You don't have permission.")

        await channel.send(message)

        try:
            await ctx.message.delete()
        except Exception:
            pass

    # =======================
    # PURGE
    # =======================

    @app_commands.command(name="purge", description="Purge a specified number of messages")
    @app_commands.describe(amount="The number of messages to delete")
    async def slash_purge(
        self,
        interaction: discord.Interaction,
        amount: int
    ):
        if not self.allowed(interaction.user):
            return await interaction.response.send_message(
                "❌ You don't have permission.",
                ephemeral=True
            )

        if amount <= 0:
            return await interaction.response.send_message(
                "❌ Please specify a number greater than 0.",
                ephemeral=True
            )

        if amount > 100:
            amount = 100

        await interaction.response.defer(ephemeral=True)
        
        deleted = await interaction.channel.purge(limit=amount)
        
        await interaction.followup.send(
            f"🧹 Successfully purged **{len(deleted)}** messages.",
            ephemeral=True
        )

    @commands.command(name="purge")
    async def purge(
        self,
        ctx,
        amount: int
    ):
        if not self.allowed(ctx.author):
            return await ctx.send("❌ You don't have permission.")

        if amount <= 0:
            return await ctx.send("❌ Please specify a number greater than 0.")

        if amount > 100:
            amount = 100

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        deleted = await ctx.channel.purge(limit=amount)

        status_msg = await ctx.send(f"🧹 Successfully purged **{len(deleted)}** messages.")
        try:
            await status_msg.delete(delay=5)
        except discord.HTTPException:
            pass


async def setup(bot):
    await bot.add_cog(Moderation(bot))
