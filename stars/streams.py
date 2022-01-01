# discord
import discord

# redbot
from redbot.core import Config
from redbot.core.config import Group

# other
import os
import logging
from typing import *
from datetime import datetime
from enum import Enum

# local
from stars.utils import *

_, log = get_logger()


class StreamStatus(Enum):
    STANDBY = 1
    START = 2
    END = 3

class Stream:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.id: str = kwargs.pop("id", create_id())
        self.status: StreamStatus = kwargs.pop("status", StreamStatus.STANDBY)
        self.time: datetime = Time.to_datetime(kwargs.pop("time"))
        self.channel_id: datetime = kwargs.pop("channel_id")
        self._channel: "Channel" = kwargs.pop("channel")
    
    def __repr__(self):
        data = [
            f"Stream",
            f"> id：{self.id}",
            f"> 通知文字頻道：{self.status}",
            f"> 討論文字頻道：{self.time}",
            f"> 會員文字頻道：{self.channel_id}",
        ]
        return "\n".join(data)

# class GuildStreamStatus(Enum):
#     STANDBY = 1
#     START = 2
#     END = 3

class GuildStream:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.stream_id: str = kwargs.pop("stream_id", {})
        self._stream: "Stream" = kwargs.pop("stream", None)
        self.id: str = self._stream.id
        self.enable: bool = kwargs.pop("enable", True)
        self.need_update_notify: bool = kwargs.pop("need_update_notify", False)
        self.notify_msg: int = kwargs.pop("notify_msg_id", None)
        self.time: datetime = Time.to_datetime(kwargs.pop("time", None))
        self.guild_collab_stream_id: kwargs.pop("guild_collab_stream_id", None)
        self._guild_collab_stream: kwargs.pop("guild_collab_stream_id", None)
        self._saved_func = kwargs.pop("saved_func", None)

        self.notify_text_channel: discord.TextChannel = None
        async def async_load():
            self.notify_text_channel: discord.TextChannel = await get_text_channel(self._bot, kwargs.pop("notify_text_channel", None))
        self._bot.loop.create_task(async_load())

    def set_guild_collab_stream(self, guild_collab_stream: "GuildCollabStream"):
        self.guild_collab_stream_id = guild_collab_stream.id
        self._guild_collab_stream = guild_collab_stream
    
class GuildCollabStream:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.id: str = kwargs.pop("id", create_id())
        self.enable: bool = kwargs.pop("enable", True)
        self.guild_stream_ids: List[str] = kwargs.pop("guild_stream_ids", [])
        self._guild_streams: List[str] = kwargs.pop("guild_streams", {})
        self.standby_msg_id: int = kwargs.pop("standby_msg_id", None)
        self.need_update_standby: bool
        self.time: datetime = Time.to_datetime(kwargs.pop("time", None))
        self._saved_func = kwargs.pop("saved_func", None)

        self.standby_text_channel: discord.TextChannel = None
        async def async_load():
            self.standby_text_channel = await get_text_channel(self._bot, kwargs.pop("standby_text_channel", None))
        self._bot.loop.create_task(async_load())

class GuildStreamsManager():

    def __init__(self, bot: Red, config: Group, guild: discord.Guild, manager: "Manager", **kwargs):
        self.bot: Red = bot
        self.config: Group = config
        self.guild: discord.Guild = guild
        self.manager: "Manager" = manager
        self.guild_streams: Dict[str, "GuildStream"] = {}
        self.guild_collab_streams: Dict[str, "GuildCollabStream"] = {}

    def get_stream(self, stream_id) -> "Stream":
        return self.manager.streams_manager.streams.get(stream_id, None)

    def get_stream_belong_member(self, stream: "Stream") -> "Member":
        channel_id = stream.channel_id
        guild_members_manager = self.manager.members_manager.get_guild_manager(self.guild)
        for member in guild_members_manager.members:
            if channel_id in member.channel_ids:
                return member

    async def add_guild_stream(self, stream_id, save=True, **kwargs) -> "GuildStream":
        if stream_id not in self.guild_streams:
            # stream=self.get_stream(stream_id)
            member = self.get_stream_belong_member(stream_id)
            guild_stream = GuildStream(
                bot=self.bot,
                stream_id=stream_id,
                stream=self.get_stream(stream_id),
                notify_text_channel=kwargs.pop("notify_text_channel", member.notify_text_channel.id),
                saved_func=save_guild_streams,
                **kwargs
            )
            self.guild_streams[stream_id] = guild_stream
            if save:
                await self.save_guild_streams()
            return guild_stream
        return None

    async def add_guild_collab_stream(self, guild_stream_ids: List["GuildStream"], save=True, **kwargs) -> "GuildCollabStream":
        guild_streams = {}
        for guild_stream_id in guild_stream_ids:
            if not self.get_collab_of_guild_stream(guild_stream_id):
                continue
            guild_streams[guild_stream_id] = self.guild_streams[guild_stream_id]
            return None
        member = self.get_stream_belong_member(guild_stream_id)
        guild_collab_stream = GuildCollabStream(
            bot=self.bot,
            guild_stream_ids=guild_stream_ids,
            guild_streams=guild_streams,
            standby_text_channel=kwargs.pop("standby_text_channel", member.chat_text_channel.id),
            saved_func=save_guild_collab_streams,
            **kwargs
        )
        self.guild_collab_streams[stream_id] = guild_collab_stream
        if save:
            await self.save_guild_collab_streams()
        return None
    
    def get_collab_of_guild_stream(self, guild_stream_id: int):
        if guild_stream_id in self.guild_streams:
            return self.guild_streams[guild_stream_id].guild_collab_stream_id

    async def save_guild_streams(self) -> None:
        await self.config.guild_streams.set(ConvertToRawData.dict(self.guild_streams))
        
    async def save_guild_collab_streams(self) -> None:
        await self.config.guild_collab_streams.set(ConvertToRawData.dict(self.guild_collab_streams))

    async def update(self):
        self.manager.streams_manager.streams


class StreamsManager(commands.Cog):

    global_defaults = {
        "streams": {}
    }

    guild_defaults = {
        "guild_streams": {},
        "guild_collab_streams": {}
    }

    def __init__(self, bot, manager: "Manager"):
        self.bot = bot
        self.manager: "Manager" = manager
        self.config: Config = Config.get_conf(self, 12448734)
        self.config.register_global(**self.global_defaults)
        self.config.register_guild(**self.guild_defaults)
        self.streams: Dict[str, "Stream"] = {}
        self.guild_managers[str, "GuildStreamsManager"] = {}

    def get_guild_manager(self, guild: Union[int, discord.Guild]) -> "GuildStreamsManager":
        guild = guild if isinstance(guild, discord.Guild) else self.bot.get_guild(guild)
        if not guild.id in self.guild_managers:
            self.guild_managers[guild.id] = GuildStreamsManager(self.bot, self.config.guild(guild), guild, self.manager)
        return self.guild_managers[guild.id]
        
    async def add_stream(self, id: str, channel_id: str, save=True, **kwargs) -> "Stream":
        if id not in self.streams:
            stream = Stream(
                bot=self.bot,
                id=id,
                channel_id=channel_id,
                channel=self.manager.channels_manager.channels[channel_id],
                **kwargs
            )
            self.streams[id] = stream
            if save:
                await save_streams()
            return stream
        return None

    @commands.command(name="test")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def test(self, ctx: commands.Context, id: str):
        stream = await self.add_stream(id)
        guild_manager = get_guild_manager(ctx.guild)
        await guild_manager.add_guild_stream([stream])

    async def save_streams(self) -> None:
        await self.config.streams.set(ConvertToRawData.dict(self.streams))