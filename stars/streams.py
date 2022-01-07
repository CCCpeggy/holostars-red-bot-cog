# discord
import discord

# redbot
from redbot.core import Config
from redbot.core.config import Group
from redbot.core import checks, commands, Config

# other
import os
import logging
from typing import *
from datetime import datetime
from enum import Enum

# local
from stars.utils import *

_, log = get_logger()


class StreamStatus(str, Enum):
    NOTSURE = "notsure"
    UPCOMING = "upcoming"
    LIVE = "live"
    MISSING = "missing"

class Stream:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.id: str = kwargs.pop("id", create_id())
        self._status: StreamStatus = StreamStatus(kwargs.pop("status", "notsure"))
        self.time: datetime = Time.to_datetime(kwargs.pop("time"))
        self.channel_id: datetime = kwargs.pop("channel_id")
        self.topic: str = kwargs.pop("topic", None)
        self.title: str = kwargs.pop("title", None)
        self.type: str = kwargs.pop("type", None)
        self._channel: "Channel" = kwargs.pop("channel")
        self.info_update: bool = kwargs.pop("info_update", False)
    
    def __repr__(self):
        data = [
            f"Stream",
            f"> id：{self.id}",
            f"> 狀態：{self._status}",
            f"> 預定時間：{self.time}",
            f"> 所屬頻道：{self._channel.type}: {self._channel.name}",
            f"> 標題：{self.title}",
            f"> 類型：{self.type}",
            f"> 主題：{self.topic}",
        ]
        return "\n".join(data)
    
    def is_valid(self):
        return self._channel

    def update_info(self, **kwargs):
        time = Time.to_datetime(kwargs.pop("time"))
        topic = kwargs.pop("topic", None)
        title = kwargs.pop("title", None)
        status = StreamStatus(kwargs.pop("status", "notsure"))
        if self.time != time:
            self.info_update = True
            self.time = time
        if self.topic != topic:
            self.info_update = True
            self.topic = topic
        if self.title != title:
            self.info_update = True
            self.title = title
        if self._status != status:
            self.info_update = True
            self._status = status

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
        self.notify_msg_id: int = kwargs.pop("notify_msg_id", None)
        self.guild_collab_stream_id: str = None
        self._guild_collab_stream: "GuildCollabStream" = None
        self._saved_func = kwargs.pop("saved_func", None)

        self.notify_text_channel: discord.TextChannel = None
        self._notify_text_channel_id: str = kwargs.pop("notify_text_channel", None)
        self.is_init = False

    async def initial(self):
        self.notify_text_channel: discord.TextChannel = await get_text_channel(self._bot, self._notify_text_channel_id)
        self.is_init = True
    
    def is_valid(self):
        return self._stream

    def set_guild_collab_stream(self, guild_collab_stream: "GuildCollabStream"):
        self.guild_collab_stream_id = guild_collab_stream.id
        self._guild_collab_stream = guild_collab_stream
    
    def __repr__(self):
        data = [
            f"GuildStream",
            f"> id：{self.id}",
            f"> 通知啟用狀態：{self.enable}",
            f"> 是否需要更新通知：{self.need_update_notify}",
            f"> 通知訊息的 ID：{self.notify_msg_id}",
            f"> 所屬待機 ID：{self.guild_collab_stream_id}",
        ]
        return "\n".join(data)
    
class GuildCollabStream:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.id: str = kwargs.pop("id", create_id())
        self.enable: bool = kwargs.pop("enable", True)
        self.guild_stream_ids: List[str] = kwargs.pop("guild_stream_ids", [])
        self._guild_streams: List[str] = kwargs.pop("guild_streams", {})
        self.standby_msg_id: int = kwargs.pop("standby_msg_id", None)
        self.need_update_standby: bool = kwargs.pop("need_update_standby", False)
        self.time: datetime = Time.to_datetime(kwargs.pop("time", None))
        self._saved_func = kwargs.pop("saved_func", None)

        self.standby_text_channel: discord.TextChannel = None
        self.is_init = False
        self._standby_text_channel_id = kwargs.pop("standby_text_channel", None)

    async def initial(self):
        self.standby_text_channel = await get_text_channel(self._bot, self._standby_text_channel_id)
        self.is_init = True
    
    def is_valid(self) -> bool:
        not_valid_guild_stream_ids = []
        for id, guild_stream in self._guild_streams.items():
            if not guild_stream or not guild_stream.is_valid():
                not_valid_guild_stream_ids.append(id)
        if len(not_valid_guild_stream_ids) == len(self._guild_streams) \
            and not Time.is_time_in_future_range(self.time):
            return False
        # for guild_stream_id in not_valid_guild_stream_ids:
        #     self.guild_stream_ids.remove(guild_stream_id)
        #     self._guild_streams.pop(guild_stream_id)
        return True
    
    def __repr__(self):
        data = [
            f"GuildCollabStream",
            f"> id：{self.id}",
            f"> 待機台啟用狀態：{self.enable}",
            f"> 是否需要更新待機台：{self.need_update_standby}",
            f"> 相關直播 ID：{', '.join(self.guild_stream_ids)}",
            f"> 待機台時間：{self.time}",
        ]
        return "\n".join(data)

class GuildStreamsManager():

    def __init__(self, bot: Red, config: Group, guild: discord.Guild, manager: "Manager", **kwargs):
        self.bot: Red = bot
        self.config: Group = config
        self.guild: discord.Guild = guild
        self.manager: "Manager" = manager
        self.guild_streams: Dict[str, "GuildStream"] = {}
        self.guild_collab_streams: Dict[str, "GuildCollabStream"] = {}

        self.is_init = False

    async def initial(self):
        async def load_guild_streams():
            for id, raw_data in (await self.config.guild_streams()).items():
                guild_stream = await self.add_guild_stream(save=False, **raw_data)
        await load_guild_streams()
        
        async def load_collab_guild_streams():
            for id, raw_data in (await self.config.guild_collab_streams()).items():
                await self.add_guild_collab_stream(save=False, **raw_data)
        await load_collab_guild_streams()
        self.is_init = True

    def get_stream(self, stream_id) -> "Stream":
        return self.manager.streams_manager.streams.get(stream_id, None)

    async def get_stream_belong_member(self, stream_id: str) -> "Member":
        stream=self.get_stream(stream_id)
        if not stream:
            return None
        channel_id = stream.channel_id
        guild_members_manager = await self.manager.members_manager.get_guild_manager(self.guild)
        for member in guild_members_manager.members.values():
            if channel_id in member.channel_ids:
                return member
        return None
    
    def get_guild_stream(self, id: str)  -> "GuildStream":
        return self.guild_streams.get(id, None)
    
    def get_guild_collab_stream(self, id: str)  -> "GuildCollabStream":
        return self.guild_collab_streams.get(id, None)

    async def add_guild_stream(self, stream_id, save=True, **kwargs) -> "GuildStream":
        if stream_id not in self.guild_streams:
            member = await self.get_stream_belong_member(stream_id)
            if member == None:
                return None
            guild_stream = GuildStream(
                bot=self.bot,
                stream_id=stream_id,
                stream=self.get_stream(stream_id),
                notify_text_channel=kwargs.pop("notify_text_channel", member.notify_text_channel),
                saved_func=self.save_guild_streams,
                **kwargs
            )
            await guild_stream.initial()
            if guild_stream.is_valid():
                self.guild_streams[stream_id] = guild_stream
                if save:
                    await self.save_guild_streams()
                return guild_stream
        return None

    async def add_guild_collab_stream(self, guild_stream_ids: List["GuildStream"], save=True, **kwargs) -> "GuildCollabStream":
        guild_streams = {}
        for guild_stream_id in guild_stream_ids:
            guild_stream = self.guild_streams[guild_stream_id]
            guild_streams[guild_stream_id] = guild_stream
            if not guild_stream.guild_collab_stream_id:
                continue
            return None
        member = await self.get_stream_belong_member(guild_stream_id)
        guild_collab_stream = GuildCollabStream(
            bot=self.bot,
            guild_stream_ids=guild_stream_ids,
            guild_streams=guild_streams,
            standby_text_channel=kwargs.pop("standby_text_channel", member.chat_text_channel),
            saved_func=self.save_guild_collab_streams,
            **kwargs
        )
        await guild_collab_stream.initial()
        if not guild_collab_stream.is_valid():
            return None
        for guild_stream in guild_streams.values():
            guild_stream.set_guild_collab_stream(guild_collab_stream)
        self.guild_collab_streams[guild_collab_stream.id] = guild_collab_stream
        if save:
            await self.save_guild_collab_streams()
        return guild_collab_stream

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
        self.guild_managers: Dict[str, "GuildStreamsManager"] = {}

        self.is_init = False

    async def initial(self):
        async def load_streams():
            from .errors import MException
            for id, raw_data in (await self.config.streams()).items():
                await self.add_stream(save=False, **raw_data)
        await load_streams()
        async def load_guild():
            for guild_id, config in (await self.config.all_guilds()).items():
                await self.get_guild_manager(guild_id)
        await load_guild()
        self.is_init = True
            
    async def get_guild_manager(self, guild: Union[int, discord.Guild]) -> "GuildStreamsManager":
        guild = guild if isinstance(guild, discord.Guild) else self.bot.get_guild(guild)
        if not guild.id in self.guild_managers:
            self.guild_managers[guild.id] = GuildStreamsManager(self.bot, self.config.guild(guild), guild, self.manager)
            await self.guild_managers[guild.id].initial()
        return self.guild_managers[guild.id]
        
    async def add_stream(self, id: str, channel_id: str, save=True, **kwargs) -> "Stream":
        if id not in self.streams:
            stream = Stream(
                bot=self.bot,
                id=id,
                channel_id=channel_id,
                channel=self.manager.channels_manager.channels.get(channel_id, None),
                **kwargs
            )
            if stream.is_valid():
                self.streams[id] = stream
                if save:
                    await self.save_streams()
                return stream
        return None

    async def update_stream(self, id: str, save=True, **kwargs) -> "Stream":
        if id not in self.streams:
            from .errors import DataNotFound
            raise DataNotFound
        self.streams[id].update_info(kwargs)
        if save:
            await self.save_streams()

    def get_stream(self, id: str) -> "Stream":
        return self.streams.get(id, None)

    # @commands.command(name="test")
    # @commands.guild_only()
    # @checks.mod_or_permissions(manage_channels=True)
    # async def test(self, ctx: commands.Context, id: str):
    #     stream = await self.add_stream(id)
    #     guild_manager = get_guild_manager(ctx.guild)
    #     await guild_manager.add_guild_stream([stream])

    async def save_streams(self) -> None:
        await self.config.streams.set(ConvertToRawData.dict(self.streams))