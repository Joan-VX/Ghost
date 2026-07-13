import asyncio
import datetime
import io
import re
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

STAFF_ROLE_IDS = {
    1524505551596290078,
    1524505452526833815,
    1525490281493954701,
}

TICKET_CATEGORY_ID = 1525212405951496395
TICKET_LOG_CHANNEL_ID = 1525212589913669653
MAX_TICKETS_PER_USER = 2

TICKET_CHANNEL_REGEX = re.compile(r"^support-(\d{4})$")


def is_staff(member: discord.Member) -> bool:
    return any(role.id in STAFF_ROLE_IDS for role in member.roles)


class InquiryModal(discord.ui.Modal, title="Support Inquiry"):

    subject = discord.ui.TextInput(
        label="Subject",
        placeholder="Briefly describe your issue...",
        required=True,
        max_length=100,
    )

    description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.long,
        placeholder="Please provide as much detail as possible.",
        required=True,
        max_length=2000,
    )

    def __init__(self, cog: "Tickets"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):

        await self.cog.create_ticket(
            interaction=interaction,
            subject=str(self.subject),
            description=str(self.description),
        )


class OpenTicketView(discord.ui.View):

    def __init__(self, cog: "Tickets"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Open Ticket",
        style=discord.ButtonStyle.green,
        custom_id="tickets:open",
        emoji="🎫",
    )
    async def open_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.send_modal(InquiryModal(self.cog))

class TicketControls(discord.ui.View):

    def __init__(self, cog: "Tickets"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.red,
        custom_id="tickets:close",
        emoji="🔒",
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.cog.close_ticket(interaction)


class Tickets(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot = bot
        self.bot.add_view(OpenTicketView(self))
        self.bot.add_view(TicketControls(self))

    async def cog_load(self):
        self.bot.add_view(OpenTicketView(self))
        self.bot.add_view(TicketControls(self))

    @property
    def ticket_category(self) -> Optional[discord.CategoryChannel]:
        return self.bot.get_channel(TICKET_CATEGORY_ID)

    @property
    def log_channel(self) -> Optional[discord.TextChannel]:
        return self.bot.get_channel(TICKET_LOG_CHANNEL_ID)

    async def get_next_ticket_number(self) -> int:
        category = self.ticket_category

        if category is None:
            return 1

        highest = 0

        for channel in category.text_channels:
            match = TICKET_CHANNEL_REGEX.match(channel.name)
            if match:
                highest = max(highest, int(match.group(1)))

        return highest + 1

    async def count_open_tickets(
        self,
        member: discord.Member,
    ) -> int:
        category = self.ticket_category

        if category is None:
            return 0

        total = 0

        for channel in category.text_channels:
            overwrites = channel.overwrites_for(member)

            if (
                overwrites.view_channel is True
                and channel.name.startswith("support-")
            ):
                total += 1

        return total

    async def create_ticket(
        self,
        interaction: discord.Interaction,
        subject: str,
        description: str,
    ):
        if interaction.guild is None:
            return

        member = interaction.user

        if not isinstance(member, discord.Member):
            member = interaction.guild.get_member(member.id)

        if member is None:
            await interaction.response.send_message(
                "Unable to identify you.",
                ephemeral=True,
            )
            return

        current = await self.count_open_tickets(member)

        if current >= MAX_TICKETS_PER_USER:
            await interaction.response.send_message(
                f"You already have {MAX_TICKETS_PER_USER} open tickets.",
                ephemeral=True,
            )
            return

        category = self.ticket_category

        if category is None:
            await interaction.response.send_message(
                "Ticket category not found.",
                ephemeral=True,
            )
            return

        number = await self.get_next_ticket_number()
        channel_name = f"support-{number:04d}"

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
                read_message_history=True,
            ),
        }

        for role_id in STAFF_ROLE_IDS:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_messages=True,
                )

        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket Owner: {member.id}",
        )

        embed = discord.Embed(
            title="Support Ticket",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow(),
        )

        embed.add_field(
            name="Owner",
            value=member.mention,
            inline=False,
        )

        embed.add_field(
            name="Subject",
            value=subject,
            inline=False,
        )

        embed.add_field(
            name="Description",
            value=description,
            inline=False,
        )

        await channel.send(
            content=member.mention,
            embed=embed,
            view=TicketControls(self),
        )

        await interaction.response.send_message(
            f"Your ticket has been created: {channel.mention}",
            ephemeral=True,
        )
    async def build_transcript(
        self,
        channel: discord.TextChannel,
    ) -> discord.File:
        messages = []

        async for message in channel.history(limit=None, oldest_first=True):
            messages.append(message)

        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            "<title>Ticket Transcript</title>",
            "<style>",
            "body{font-family:Arial,Helvetica,sans-serif;background:#202225;color:#eee;padding:20px;}",
            ".msg{border-bottom:1px solid #444;padding:10px 0;}",
            ".author{font-weight:bold;color:#6aa9ff;}",
            ".time{font-size:12px;color:#999;}",
            ".content{white-space:pre-wrap;margin-top:4px;}",
            ".attach{margin-top:6px;}",
            "a{color:#7db7ff;}",
            "</style>",
            "</head>",
            "<body>",
            f"<h2>{channel.name}</h2>",
        ]

        for message in messages:
            created = message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")

            html.append("<div class='msg'>")
            html.append(
                f"<div class='author'>{discord.utils.escape_html(str(message.author))}</div>"
            )
            html.append(f"<div class='time'>{created}</div>")

            if message.content:
                html.append(
                    "<div class='content'>"
                    + discord.utils.escape_html(message.content)
                    + "</div>"
                )

            for embed in message.embeds:
                if embed.title:
                    html.append(
                        "<div class='content'><b>Embed:</b> "
                        + discord.utils.escape_html(embed.title)
                        + "</div>"
                    )

            for attachment in message.attachments:
                html.append(
                    "<div class='attach'>Attachment: "
                    f"<a href='{attachment.url}'>{discord.utils.escape_html(attachment.filename)}</a>"
                    "</div>"
                )

            html.append("</div>")

        html.append("</body></html>")

        data = io.BytesIO("\n".join(html).encode("utf-8"))

        return discord.File(
            data,
            filename=f"{channel.name}.html",
        )

    async def log_ticket_close(
        self,
        channel: discord.TextChannel,
        closer: discord.Member,
    ):
        log_channel = self.log_channel

        if log_channel is None:
            return

        transcript = await self.build_transcript(channel)

        owner_id = None

        if channel.topic:
            match = re.search(r"(\d+)", channel.topic)
            if match:
                owner_id = int(match.group(1))

        embed = discord.Embed(
            title="Ticket Closed",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow(),
        )

        embed.add_field(
            name="Channel",
            value=channel.name,
            inline=False,
        )

        if owner_id:
            embed.add_field(
                name="Owner",
                value=f"<@{owner_id}> (`{owner_id}`)",
                inline=False,
            )

        embed.add_field(
            name="Closed By",
            value=closer.mention,
            inline=False,
        )

        await log_channel.send(
            embed=embed,
            file=transcript,
        )

    async def close_ticket(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild is None:
            return

        channel = interaction.channel

        if not isinstance(channel, discord.TextChannel):
            return

        if not channel.name.startswith("support-"):
            await interaction.response.send_message(
                "This is not a ticket channel.",
                ephemeral=True,
            )
            return

        member = interaction.user

        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
        if not is_staff(member):
            await interaction.response.send_message(
                "Only staff can close tickets.",
                ephemeral=True,
            )
            return

        await self.log_ticket_close(channel, member)

        await asyncio.sleep(2)

        await channel.delete(reason=f"Closed by {member}")
    def get_ticket_owner_id(
        self,
        channel: discord.TextChannel,
    ) -> Optional[int]:
        if not channel.topic:
            return None

        match = re.search(r"(\d+)", channel.topic)
        if match:
            return int(match.group(1))

        return None
            if not isinstance(member, discord.Member) or not is_staff(member):
                await ctx_or_interaction.send(
                    "You do not have permission to use this command."
                )
                return False

            return True

        member = ctx_or_interaction.user

        if not isinstance(member, discord.Member) or not is_staff(member):
            await ctx_or_interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True,
            )
            return False

        return True

    @commands.hybrid_command(
        name="close",
        description="Close the current ticket.",
    )
    async def close_command(
        self,
        ctx: commands.Context,
    ):
        fake = type(
            "HybridInteraction",
            (),
            {
                "guild": ctx.guild,
                "channel": ctx.channel,
                "user": ctx.author,
                "response": type(
                    "Response",
                    (),
                    {
                        "send_message": lambda _, content, ephemeral=False: ctx.send(
                            content
                        )
                    },
                )(),
            },
        )()

        await self.close_ticket(fake)

    @commands.hybrid_command(
        name="claim",
        description="Claim a ticket.",
    )
    async def claim(
        self,
        ctx: commands.Context,
    ):
        if not await self.ensure_staff(ctx):
            return

        if not isinstance(ctx.channel, discord.TextChannel):
            return

        if not ctx.channel.name.startswith("support-"):
            await ctx.send("This is not a ticket channel.")
            return

        embed = discord.Embed(
            title="Ticket Claimed",
            description=f"{ctx.author.mention} is now handling this ticket.",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow(),
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="rename",
        description="Rename the current ticket.",
    )
    @app_commands.describe(name="New ticket name")
    async def rename(
        self,
        ctx: commands.Context,
        *,
        name: str,
    ):
        if not await self.ensure_staff(ctx):
            return

        if not isinstance(ctx.channel, discord.TextChannel):
            return

        await ctx.channel.edit(name=name)

        await ctx.send(f"Ticket renamed to **{name}**.")

    @commands.hybrid_command(
        name="add",
        description="Add a user to the ticket.",
    )
    @app_commands.describe(member="Member to add")
    async def add(
        self,
        ctx: commands.Context,
        member: discord.Member,
    ):
        if not await self.ensure_staff(ctx):
            return

        if not isinstance(ctx.channel, discord.TextChannel):
            return

        await ctx.channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True,
        )

        await ctx.send(f"{member.mention} has been added to the ticket.")

    @commands.hybrid_command(
        name="remove",
        description="Remove a user from the ticket.",
    )
    @app_commands.describe(member="Member to remove")
    async def remove(
        self,
        ctx: commands.Context,
        member: discord.Member,
    ):
        if not await self.ensure_staff(ctx):
            return

        if not isinstance(ctx.channel, discord.TextChannel):
            return

        owner_id = self.get_ticket_owner_id(ctx.channel)

        if owner_id == member.id:
            await ctx.send("You cannot remove the ticket owner.")
            return

        await ctx.channel.set_permissions(
            member,
            overwrite=None,
        )

        await ctx.send(f"{member.mention} has been removed from the ticket.")
          @commands.hybrid_command(
        name="support",
        description="Send the support ticket panel.",
    )
    async def support(
        self,
        ctx: commands.Context,
    ):
        if not await self.ensure_staff(ctx):
            return

        embed = discord.Embed(
            title="Support Center",
            description=(
                "Need help?\n\n"
                "Press **Open Ticket** below and complete the inquiry form.\n"
                f"Maximum **{MAX_TICKETS_PER_USER}** open tickets per user."
            ),
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow(),
        )

        embed.set_footer(text="Support System")

        await ctx.send(
            embed=embed,
            view=OpenTicketView(self),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
