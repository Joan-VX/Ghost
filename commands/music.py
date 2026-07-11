# commands/music.py
# Part 1/3

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Optional, List

import discord
from discord.ext import commands
from discord import app_commands

import wavelink


@dataclass
class MusicQueue:
    tracks: list[wavelink.Playable] = field(default_factory=list)

    def add(self, track: wavelink.Playable):
        self.tracks.append(track)

    def remove(self, index: int):
        if 0 <= index < len(self.tracks):
            return self.tracks.pop(index)
        return None

    def clear(self):
        self.tracks.clear()

    def shuffle(self):
        random.shuffle(self.tracks)

    def get_next(self):
        if self.tracks:
            return self.tracks.pop(0)
        return None


@dataclass
class GuildMusic:
    queue: MusicQueue = field(default_factory=MusicQueue)

    current: Optional[wavelink.Playable] = None

    loop_current: bool = False
    loop_queue: bool = False
    autoplay: bool = False

    volume: int = 100

    last_active: float = field(default_factory=time.time)

    alone_task: Optional[asyncio.Task] = None

    def touch(self):
        self.last_active = time.time()


class MusicControlView(discord.ui.View):
    def __init__(self, cog: "Music", guild_id: int):
        super().__init__(timeout=None)

        self.cog = cog
        self.guild_id = guild_id


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.voice:
            await interaction.response.send_message(
                "You must be in a voice channel.",
                ephemeral=True
            )
            return False

        return True


    async def get_player(self, interaction: discord.Interaction):
        return interaction.guild.voice_client


    @discord.ui.button(
        emoji="⏮️",
        style=discord.ButtonStyle.secondary,
        custom_id="music_previous"
    )
    async def previous(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        player = await self.get_player(interaction)

        if not isinstance(player, wavelink.Player):
            return await interaction.response.send_message(
                "Nothing is playing.",
                ephemeral=True
            )

        await interaction.response.defer()

        await player.seek(0)


    @discord.ui.button(
        emoji="⏯️",
        style=discord.ButtonStyle.primary,
        custom_id="music_pause_resume"
    )
    async def pause_resume(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        player = await self.get_player(interaction)

        if not isinstance(player, wavelink.Player):
            return await interaction.response.send_message(
                "Nothing is playing.",
                ephemeral=True
            )

        await player.pause(not player.paused)

        await interaction.response.send_message(
            "Playback updated.",
            ephemeral=True
        )


    @discord.ui.button(
        emoji="⏭️",
        style=discord.ButtonStyle.success,
        custom_id="music_skip"
    )
    async def skip(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        player = await self.get_player(interaction)

        if not isinstance(player, wavelink.Player):
            return await interaction.response.send_message(
                "Nothing is playing.",
                ephemeral=True
            )

        await interaction.response.defer()

        await player.skip()


    @discord.ui.button(
        emoji="⏹️",
        style=discord.ButtonStyle.danger,
        custom_id="music_stop"
    )
    async def stop(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        player = await self.get_player(interaction)

        if not isinstance(player, wavelink.Player):
            return await interaction.response.send_message(
                "Nothing is playing.",
                ephemeral=True
            )

        await player.stop()

        data = self.cog.get_guild_data(interaction.guild.id)
        data.queue.clear()
        data.current = None

        await interaction.response.send_message(
            "Stopped playback.",
            ephemeral=True
        )


    @discord.ui.button(
        emoji="🔁",
        style=discord.ButtonStyle.secondary,
        custom_id="music_loop"
    )
    async def loop(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        data = self.cog.get_guild_data(interaction.guild.id)

        data.loop_current = not data.loop_current
        data.loop_queue = False

        await interaction.response.send_message(
            f"Loop current: `{data.loop_current}`",
            ephemeral=True
        )


    @discord.ui.button(
        emoji="🔉",
        style=discord.ButtonStyle.secondary,
        custom_id="music_volume_down"
    )
    async def volume_down(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        player = await self.get_player(interaction)

        if not isinstance(player, wavelink.Player):
            return await interaction.response.send_message(
                "Nothing is playing.",
                ephemeral=True
            )

        data = self.cog.get_guild_data(interaction.guild.id)

        data.volume = max(0, data.volume - 10)

        await player.set_volume(data.volume)

        await interaction.response.send_message(
            f"Volume: `{data.volume}%`",
            ephemeral=True
        )


    @discord.ui.button(
        emoji="🔊",
        style=discord.ButtonStyle.secondary,
        custom_id="music_volume_up"
    )
    async def volume_up(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        player = await self.get_player(interaction)

        if not isinstance(player, wavelink.Player):
            return await interaction.response.send_message(
                "Nothing is playing.",
                ephemeral=True
            )

        data = self.cog.get_guild_data(interaction.guild.id)

        data.volume = min(200, data.volume + 10)

        await player.set_volume(data.volume)

        await interaction.response.send_message(
            f"Volume: `{data.volume}%`",
            ephemeral=True
        )


class Music(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.guild_music: dict[int, GuildMusic] = {}

        self.disconnect_tasks: dict[int, asyncio.Task] = {}

    def get_guild_data(self, guild_id: int) -> GuildMusic:
        if guild_id not in self.guild_music:
            self.guild_music[guild_id] = GuildMusic()

        return self.guild_music[guild_id]
  # Part 2/3

    async def ensure_voice(
        self,
        ctx: commands.Context | discord.Interaction
    ) -> Optional[wavelink.Player]:

        if isinstance(ctx, commands.Context):
            member = ctx.author
            guild = ctx.guild
        else:
            member = ctx.user
            guild = ctx.guild

        if not member.voice:
            if isinstance(ctx, commands.Context):
                await ctx.send(
                    "You must be in a voice channel.",
                    delete_after=10
                )
            else:
                await ctx.response.send_message(
                    "You must be in a voice channel.",
                    ephemeral=True
                )
            return None

        channel = member.voice.channel

        player = guild.voice_client

        if not player:
            player = await channel.connect(
                cls=wavelink.Player,
                self_deaf=True
            )

        elif player.channel != channel:
            await player.move_to(channel)

        return player


    async def play_next(
        self,
        guild: discord.Guild
    ):

        data = self.get_guild_data(guild.id)

        player = guild.voice_client

        if not isinstance(player, wavelink.Player):
            return

        next_track = None

        if data.loop_current and data.current:
            next_track = data.current

        elif data.loop_queue and data.current:
            data.queue.add(data.current)
            next_track = data.queue.get_next()

        else:
            next_track = data.queue.get_next()


        if not next_track:

            if data.autoplay and data.current:
                try:
                    results = await wavelink.Playable.search(
                        data.current.title
                    )

                    if results:
                        next_track = random.choice(
                            results[:5]
                        )

                except Exception:
                    next_track = None


        if not next_track:

            data.current = None

            await self.start_disconnect_timer(guild)

            return


        data.current = next_track
        data.touch()

        try:
            await player.play(next_track)

            await player.set_volume(
                data.volume
            )

        except Exception:
            data.current = None


    async def start_disconnect_timer(
        self,
        guild: discord.Guild
    ):

        if guild.id in self.disconnect_tasks:
            return


        async def timer():

            await asyncio.sleep(300)

            player = guild.voice_client

            if not isinstance(player, wavelink.Player):
                return

            if player.channel:

                humans = [
                    member
                    for member in player.channel.members
                    if not member.bot
                ]

                if not humans:

                    await player.disconnect()

                    self.guild_music.pop(
                        guild.id,
                        None
                    )


        task = asyncio.create_task(timer())

        self.disconnect_tasks[guild.id] = task


    async def send_now_playing(
        self,
        ctx,
        track: wavelink.Playable
    ):

        embed = discord.Embed(
            title="🎵 Now Playing",
            description=(
                f"**{track.title}**\n"
                f"Requested by: "
                f"{getattr(track, 'requester', 'Unknown')}"
            ),
            colour=discord.Colour.blurple()
        )

        if track.uri:
            embed.url = track.uri


        view = MusicControlView(
            self,
            ctx.guild.id
        )


        if isinstance(ctx, commands.Context):
            await ctx.send(
                embed=embed,
                view=view
            )

        else:
            await ctx.followup.send(
                embed=embed,
                view=view
            )


    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self,
        payload: wavelink.TrackEndEventPayload
    ):

        player = payload.player

        if not player:
            return

        await self.play_next(
            player.guild
        )


    @commands.command(
        name="connect"
    )
    async def prefix_connect(
        self,
        ctx: commands.Context
    ):

        player = await self.ensure_voice(ctx)

        if player:
            await ctx.send(
                "Connected to voice."
            )


    @app_commands.command(
        name="connect",
        description="Connect the bot to your voice channel."
    )
    async def slash_connect(
        self,
        interaction: discord.Interaction
    ):

        player = await self.ensure_voice(
            interaction
        )

        if player:

            await interaction.response.send_message(
                "Connected to voice."
            )


    @commands.command(
        name="disconnect"
    )
    async def prefix_disconnect(
        self,
        ctx: commands.Context
    ):

        player = ctx.guild.voice_client

        if isinstance(player, wavelink.Player):

            await player.disconnect()

            self.guild_music.pop(
                ctx.guild.id,
                None
            )

            await ctx.send(
                "Disconnected."
            )


    @app_commands.command(
        name="disconnect",
        description="Disconnect from voice."
    )
    async def slash_disconnect(
        self,
        interaction: discord.Interaction
    ):

        player = interaction.guild.voice_client

        if isinstance(player, wavelink.Player):

            await player.disconnect()

            self.guild_music.pop(
                interaction.guild.id,
                None
            )


        await interaction.response.send_message(
            "Disconnected."
        )


    async def search_track(
        self,
        query: str
    ):

        results = await wavelink.Playable.search(
            query
        )

        if not results:
            return None

        if isinstance(results, wavelink.Playlist):

            return results.tracks

        return results[0]


    @commands.command(
        name="play"
    )
    async def prefix_play(
        self,
        ctx: commands.Context,
        *,
        query: str
    ):

        player = await self.ensure_voice(ctx)

        if not player:
            return

        await ctx.message.add_reaction("🔎")

        result = await self.search_track(
            query
        )

        if not result:
            return await ctx.send(
                "No results found."
            )


        data = self.get_guild_data(
            ctx.guild.id
        )

        if isinstance(result, list):

            for track in result:
                data.queue.add(track)

            await ctx.send(
                f"Added `{len(result)}` tracks."
            )

        else:

            result.requester = ctx.author

            if player.playing:

                data.queue.add(
                    result
                )

                await ctx.send(
                    f"Queued: **{result.title}**"
                )

            else:

                data.current = result

                await player.play(
                    result
                )

                await self.send_now_playing(
                    ctx,
                    result
                )


    @app_commands.command(
        name="play",
        description="Play a song."
    )
    async def slash_play(
        self,
        interaction: discord.Interaction,
        query: str
    ):

        player = await self.ensure_voice(
            interaction
        )

        if not player:
            return

        await interaction.response.defer()

        result = await self.search_track(
            query
        )

        if not result:

            return await interaction.followup.send(
                "No results found."
            )


        data = self.get_guild_data(
            interaction.guild.id
        )

        if isinstance(result, list):

            for track in result:
                data.queue.add(track)

            await interaction.followup.send(
                f"Added `{len(result)}` tracks."
            )

        else:

            result.requester = interaction.user

            if player.playing:

                data.queue.add(result)

                await interaction.followup.send(
                    f"Queued: **{result.title}**"
                )

            else:

                data.current = result

                await player.play(result)

                await self.send_now_playing(
                    interaction,
                    result
                )
              # Part 3/3

    @commands.command(
        name="skip"
    )
    async def prefix_skip(
        self,
        ctx: commands.Context
    ):

        player = ctx.guild.voice_client

        if isinstance(player, wavelink.Player):

            await player.skip()

            await ctx.send(
                "Skipped."
            )


    @app_commands.command(
        name="skip",
        description="Skip the current song."
    )
    async def slash_skip(
        self,
        interaction: discord.Interaction
    ):

        player = interaction.guild.voice_client

        if isinstance(player, wavelink.Player):

            await player.skip()

        await interaction.response.send_message(
            "Skipped."
        )


    @commands.command(
        name="previous"
    )
    async def previous(
        self,
        ctx: commands.Context
    ):

        player = ctx.guild.voice_client

        if isinstance(player, wavelink.Player):

            await player.seek(0)

            await ctx.send(
                "Restarted current track."
            )


    @commands.command(
        name="pause"
    )
    async def pause(
        self,
        ctx: commands.Context
    ):

        player = ctx.guild.voice_client

        if isinstance(player, wavelink.Player):

            await player.pause(True)

            await ctx.send(
                "Paused."
            )


    @commands.command(
        name="resume"
    )
    async def resume(
        self,
        ctx: commands.Context
    ):

        player = ctx.guild.voice_client

        if isinstance(player, wavelink.Player):

            await player.pause(False)

            await ctx.send(
                "Resumed."
            )


    @commands.command(
        name="stop"
    )
    async def stop(
        self,
        ctx: commands.Context
    ):

        player = ctx.guild.voice_client

        if isinstance(player, wavelink.Player):

            await player.stop()

            data = self.get_guild_data(
                ctx.guild.id
            )

            data.queue.clear()
            data.current = None

            await ctx.send(
                "Stopped playback."
            )


    @commands.command(
        name="shuffle"
    )
    async def shuffle(
        self,
        ctx: commands.Context
    ):

        data = self.get_guild_data(
            ctx.guild.id
        )

        data.queue.shuffle()

        await ctx.send(
            "Queue shuffled."
        )


    @commands.command(
        name="remove"
    )
    async def remove(
        self,
        ctx: commands.Context,
        index: int
    ):

        data = self.get_guild_data(
            ctx.guild.id
        )

        track = data.queue.remove(
            index - 1
        )

        if track:

            await ctx.send(
                f"Removed **{track.title}**"
            )

        else:

            await ctx.send(
                "Invalid queue position."
            )


    @commands.command(
        name="clear"
    )
    async def clear(
        self,
        ctx: commands.Context
    ):

        data = self.get_guild_data(
            ctx.guild.id
        )

        data.queue.clear()

        await ctx.send(
            "Queue cleared."
        )


    @commands.command(
        name="loop"
    )
    async def loop(
        self,
        ctx: commands.Context,
        mode: str = "song"
    ):

        data = self.get_guild_data(
            ctx.guild.id
        )

        mode = mode.lower()

        if mode == "song":

            data.loop_current = not data.loop_current
            data.loop_queue = False

            state = data.loop_current

        elif mode == "queue":

            data.loop_queue = not data.loop_queue
            data.loop_current = False

            state = data.loop_queue

        else:

            return await ctx.send(
                "Use `song` or `queue`."
            )


        await ctx.send(
            f"Loop {mode}: `{state}`"
        )


    @commands.command(
        name="autoplay"
    )
    async def autoplay(
        self,
        ctx: commands.Context
    ):

        data = self.get_guild_data(
            ctx.guild.id
        )

        data.autoplay = not data.autoplay

        await ctx.send(
            f"Autoplay: `{data.autoplay}`"
        )


    @commands.command(
        name="volume"
    )
    async def volume(
        self,
        ctx: commands.Context,
        amount: int
    ):

        if amount < 0 or amount > 200:

            return await ctx.send(
                "Volume must be between 0 and 200."
            )


        player = ctx.guild.voice_client

        if not isinstance(player, wavelink.Player):
            return


        data = self.get_guild_data(
            ctx.guild.id
        )

        data.volume = amount

        await player.set_volume(
            amount
        )

        await ctx.send(
            f"Volume set to `{amount}%`"
        )


    @commands.command(
        name="seek"
    )
    async def seek(
        self,
        ctx: commands.Context,
        seconds: int
    ):

        player = ctx.guild.voice_client

        if isinstance(player, wavelink.Player):

            await player.seek(
                seconds * 1000
            )

            await ctx.send(
                f"Seeked to `{seconds}s`."
            )


    @commands.command(
        name="nowplaying",
        aliases=["np"]
    )
    async def now_playing(
        self,
        ctx: commands.Context
    ):

        data = self.get_guild_data(
            ctx.guild.id
        )

        track = data.current

        if not track:

            return await ctx.send(
                "Nothing playing."
            )


        embed = discord.Embed(
            title="🎵 Now Playing",
            description=track.title,
            colour=discord.Colour.blurple()
        )

        if track.uri:
            embed.url = track.uri


        await ctx.send(
            embed=embed,
            view=MusicControlView(
                self,
                ctx.guild.id
            )
        )


    @commands.command(
        name="queue",
        aliases=["q"]
    )
    async def queue(
        self,
        ctx: commands.Context
    ):

        data = self.get_guild_data(
            ctx.guild.id
        )


        if not data.queue.tracks:

            return await ctx.send(
                "Queue is empty."
            )


        lines = []

        for index, track in enumerate(
            data.queue.tracks[:10],
            start=1
        ):

            lines.append(
                f"`{index}` {track.title}"
            )


        embed = discord.Embed(
            title="🎶 Music Queue",
            description="\n".join(lines),
            colour=discord.Colour.blurple()
        )


        await ctx.send(
            embed=embed
        )


    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):

        if member.bot:
            return

        guild = member.guild

        player = guild.voice_client

        if not isinstance(player, wavelink.Player):
            return


        if player.channel:

            humans = [
                m
                for m in player.channel.members
                if not m.bot
            ]

            if not humans:

                await self.start_disconnect_timer(
                    guild
                )


    async def cog_unload(self):

        for task in self.disconnect_tasks.values():

            task.cancel()


async def setup(
    bot: commands.Bot
):

    await bot.add_cog(
        Music(bot)
    )
