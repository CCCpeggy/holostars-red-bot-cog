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
        self.channel_id: str = kwargs.pop("channel_id")
        self._channel: "Channel" = kwargs.pop("channel")
        self.topic: str = kwargs.pop("topic", None)
        self.title: str = kwargs.pop("title", None)
        self.url: str = kwargs.pop("url", "")
        self.type: str = kwargs.pop("type", None)
        self._info_update: bool = kwargs.pop("info_update", True)
    
    def __repr__(self):
        if self.is_valid():
            data = [
                f"Stream",
                f"> id：{self.id}",
                f"> 狀態：{self._status}",
                f"> 預定時間：{self.time}",
                f"> 所屬頻道：[{self._channel.type}]{self._channel.name}",
                f"> 標題：{self.title}",
                f"> 類型：{self.type}",
                f"> 主題：{self.topic}",
                f"> 資料更新：{self._info_update}",
            ]
        else:
            data = [
                f"NOT VALID: Stream",
                f"> id：{self.id}",
            ]
        return "\n".join(data)
    
    def is_valid(self):
        return self._channel and self._status != StreamStatus.MISSING

    def update_info(self, **kwargs):
        time = Time.to_datetime(kwargs.pop("time"))
        topic = kwargs.pop("topic", None)
        title = kwargs.pop("title", None)
        status = StreamStatus(kwargs.pop("status", "notsure"))
        if self.time != time:
            self._info_update = True
            self.time = time
        if self.topic != topic:
            self._info_update = True
            self.topic = topic
        if self.title != title:
            self._info_update = True
            self.title = title
        if self._status != status:
            self._info_update = True
            self._status = status
        log.debug("已更新 stream：" + str(self))
        log.info("已更新 stream：" + self.id)
    
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
        self._info_update: bool = kwargs.pop("info_update", True)
        self.notify_msg_enable: bool = kwargs.pop("notify_msg_enable", True)
        self.notify_msg_id: int = kwargs.pop("notify_msg_id", None)
        self.guild_collab_stream_id: str = None
        self._guild_collab_stream: "GuildCollabStream" = None
        self._saved_func = kwargs.pop("saved_func", None)
        self._member: "Member" = kwargs.pop("member", True)
        self.member_name: str = self._member.name if self._member else None

        self.notify_text_channel: discord.TextChannel = None
        self._notify_text_channel_id: int = kwargs.pop("notify_text_channel", None)
        self.is_init = False

    async def initial(self):
        self.notify_text_channel: discord.TextChannel = await get_text_channel(self._bot, self._notify_text_channel_id)
        self.is_init = True
    
    def is_valid(self):
        return self._stream

    def set_guild_collab_stream(self, guild_collab_stream: "GuildCollabStream"):
        self.guild_collab_stream_id = guild_collab_stream.id
        self._guild_collab_stream = guild_collab_stream

    def check(self):
        if self.is_valid():
            if self._stream._info_update:
                self._info_update = True
    
    def __repr__(self):
        if self.is_valid():
            data = [
                f"GuildStream",
                f"> id：{self.id}",
                f"> 通知啟用狀態：{self.notify_msg_enable}",
                f"> 通知訊息的 ID：{self.notify_msg_id}",
                f"> 所屬待機 ID：{self.guild_collab_stream_id}",
                f"> 資料更新：{self._info_update}",
                f"> member name：{self.member_name}",
            ]
        else:
            data = [
                f"NOT VALID: GuildStream",
                f"> id：{self.id}",
            ]
        return "\n".join(data)
    
class GuildCollabStream:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.id: str = kwargs.pop("id", create_id())
        self.guild_stream_ids: List[str] = kwargs.pop("guild_stream_ids", [])
        self._guild_streams: List[str] = kwargs.pop("guild_streams", {})
        self.standby_msg_enable: bool = kwargs.pop("standby_msg_enable", True)
        self.standby_msg_id: int = kwargs.pop("standby_msg_id", None)
        self._info_update: bool = kwargs.pop("info_update", True)
        self.description: str = kwargs.pop("description", None)
        self.time: datetime = Time.to_datetime(kwargs.pop("time", None))
        self._saved_func = kwargs.pop("saved_func", None)
        self._status: StreamStatus = StreamStatus(kwargs.pop("status", "notsure"))

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

    def check(self):
        self._status = StreamStatus.NOTSURE
        if self.is_valid():
            for id, guild_stream in self._guild_streams.items():
                if guild_stream._info_update:
                    self._info_update = True
                if guild_stream._stream and self._status != StreamStatus.LIVE:
                    if guild_stream._stream._status in [StreamStatus.LIVE, StreamStatus.UPCOMING]:
                        self._status = guild_stream._stream._status

    def get_standby_msg(self, message_format):
        def get_url(self):
            data = []
            for guild_stream in self._guild_streams.values():
                data.append(f"{guild_stream._stream._channel.name}:{guild_stream._stream.url}")
            return "\n".join(data)
        def get_title(self):
            return "\n".join([guild_stream._stream.title for guild_stream in self._guild_streams.values()])
        def get_description(self):
            if self.description:
                return self.description
            topics = [guild_stream._stream.topic for guild_stream in self._guild_streams.values()]
            if len(topics) > 0:
                return "/".join(set(topics))
            return get_title(self)
        def get_channel_name(self):
            return "\n".join([guild_stream._stream._channel.name for guild_stream in self._guild_streams.values()])
                
        message_format = message_format.replace("{time}", Time.to_discord_time_str(Time.get_specified_timezone(self.time)))
        message_format = message_format.replace("{title}", get_title(self))
        message_format = message_format.replace("{channel_name}", get_channel_name(self))
        message_format = message_format.replace("{url}", get_url(self))
        message_format = message_format.replace("{mention}", "")
        message_format = message_format.replace("{description}", get_description(self))
        message_format = message_format.replace("{new_line}", "\n")
        return message_format
    
    def __repr__(self):
        if self.is_valid():
            data = [
                f"GuildCollabStream",
                f"> id：{self.id}",
                f"> 待機台啟用狀態：{self.standby_msg_enable}",
                f"> 相關直播 ID：{', '.join(self.guild_stream_ids)}",
                f"> 待機台時間：{self.time}",
                f"> 資料更新：{self._info_update}",
                f"> 狀態：{self._status}",
            ]
        else:
            data = [
                f"NOT VALID: GuildCollabStream",
                f"> id：{self.id}",
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
    
    async def get_member_by_name(self, member_name: str) -> "Member":
        guild_members_manager = await self.manager.members_manager.get_guild_manager(self.guild)
        return guild_members_manager.members.get(member_name, None)
    
    def get_guild_stream(self, id: str)  -> "GuildStream":
        return self.guild_streams.get(id, None)
    
    def get_guild_collab_stream(self, id: str)  -> "GuildCollabStream":
        return self.guild_collab_streams.get(id, None)

    async def add_guild_stream(self, stream_id, save=True, **kwargs) -> "GuildStream":
        if stream_id not in self.guild_streams:
            # get member
            member_name = kwargs.pop("member_name", None)
            member = None
            if member_name:
                member = await self.get_member_by_name(member_name)
            else:
                member = await self.get_stream_belong_member(stream_id)
            if member == None:
                log.debug("找不到 member，沒有新增 guild_stream 成功：" + stream_id)
                return None
            log.debug("add_guild_stream: " + str(member))
            notify_text_channel = kwargs.pop("notify_text_channel", member.notify_text_channel)
            guild_stream = GuildStream(
                bot=self.bot,
                stream_id=stream_id,
                stream=self.get_stream(stream_id),
                notify_text_channel=notify_text_channel.id if notify_text_channel else None,
                saved_func=self.save_guild_streams,
                member=member,
                **kwargs
            )
            await guild_stream.initial()
            if True or guild_stream.is_valid():
                self.guild_streams[stream_id] = guild_stream
                if save:
                    await self.save_guild_streams()
                log.debug("已新增 guild_stream：" + str(guild_stream))
                log.info("已新增 guild_stream：" + guild_stream.id)
                return guild_stream
        log.debug("已存在，所以沒有新增 guild_stream：" + stream_id)
        return None

    async def add_guild_collab_stream(self, guild_stream_ids: List[str], save=True, **kwargs) -> "GuildCollabStream":
        if len(guild_stream_ids) == 0:
            log.debug("guild_stream_ids 長度為 0，沒有新增 guild_collab_stream 成功")
            return None

        guild_streams = {}
        for guild_stream_id in guild_stream_ids:
            guild_stream = self.get_guild_stream(guild_stream_id)
            if guild_stream:
                guild_streams[guild_stream_id] = guild_stream
                if not guild_stream.guild_collab_stream_id:
                    continue
            log.debug("沒有新增 guild_collab_stream 成功：" + ', '.join(guild_stream_ids))
            return None
        member: "Member" = await self.get_stream_belong_member(guild_stream_id)
        chat_text_channel = kwargs.pop("standby_text_channel", member.chat_text_channel)
        guild_collab_stream = GuildCollabStream(
            bot=self.bot,
            guild_stream_ids=guild_stream_ids,
            guild_streams=guild_streams,
            standby_text_channel=chat_text_channel.id if chat_text_channel else None,
            saved_func=self.save_guild_collab_streams,
            **kwargs
        )
        await guild_collab_stream.initial()
        if False and not guild_collab_stream.is_valid():
            log.debug("沒有新增 guild_collab_stream 成功：" + ', '.join(guild_stream_ids))
            return None
        for guild_stream in guild_streams.values():
            guild_stream.set_guild_collab_stream(guild_collab_stream)
        self.guild_collab_streams[guild_collab_stream.id] = guild_collab_stream
        if save:
            await self.save_guild_collab_streams()
        log.debug("已新增 guild_collab_stream：" + str(guild_collab_stream))
        log.info("已新增 guild_collab_stream：" + ', '.join(guild_stream_ids))
        return guild_collab_stream

    async def save_guild_streams(self) -> None:
        await self.config.guild_streams.set(ConvertToRawData.dict(self.guild_streams))
        
    async def save_guild_collab_streams(self) -> None:
        await self.config.guild_collab_streams.set(ConvertToRawData.dict(self.guild_collab_streams))

    async def check(self):
        for guild_stream in self.guild_streams.values():
            if not guild_stream._guild_collab_stream:
                await self.add_guild_collab_stream([guild_stream.id], time=guild_stream._stream.time)
                guild_stream._info_update = True
            guild_stream.check()

        for guild_collab_stream in self.guild_collab_streams.values():
            guild_collab_stream.check()

        def delete_not_valid_guild_stream(self) -> None:
            remove_guild_stream_ids = []
            for id, guild_stream in self.guild_streams.items():
                if not guild_stream.is_valid():
                    remove_guild_stream_ids.append(id)
            for id in remove_guild_stream_ids:
                self.guild_streams.pop(id)
        delete_not_valid_guild_stream(self)

        def delete_not_valid_guild_collab_stream(self) -> None:
            remove_guild_collab_stream_ids = []
            for id, guild_collab_stream in self.guild_collab_streams.items():
                if not guild_collab_stream.is_valid():
                    remove_guild_collab_stream_ids.append(id)
            for id in remove_guild_collab_stream_ids:
                self.guild_collab_streams.pop(id)
        delete_not_valid_guild_collab_stream(self)

        for guild_stream in self.guild_streams.values():
            guild_stream._info_update = False
        
        await self.save_guild_streams()
        await self.save_guild_collab_streams()

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
        self.guild_managers: Dict[int, "GuildStreamsManager"] = {}

        self.is_init = False

    async def initial(self):
        async def load_streams():
            from .errors import MException
            for id, raw_data in (await self.config.streams()).items():
                await self.add_stream(save=False, **raw_data)
        await load_streams()
        async def load_guild():
            for guild_id, config in (await self.config.all_guilds()).items():
                await self.get_guild_manager(int(guild_id))
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
            if True or stream.is_valid():
                self.streams[id] = stream
                if save:
                    await self.save_streams()
                log.debug("已新增 stream：" + str(stream))
                log.info("已新增 stream：" + id)
                return stream
            log.debug("沒有新增 stream 成功：" + id)
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

    def set_stream_to_notsure(self) -> None:
        for stream in self.streams.values():
            stream._status = StreamStatus.NOTSURE

    async def delete_not_valid_and_notsure_stream(self) -> None:
        remove_stream_ids = []
        for id, stream in self.streams.items():
            if stream._status == StreamStatus.NOTSURE or not stream.is_valid():
                remove_stream_ids.append(id)
        await self.remove_streams(remove_stream_ids)

    async def remove_streams(self, stream_ids: List[str]) -> None:
        for id in stream_ids:
            log.debug("刪除：" + str(self.streams[id]))
            log.info("刪除 stream：" + id)
            self.streams.pop(id)
        await self.save_streams()

    async def check(self) -> None:
        for guild_streams_manager in self.guild_managers.values():
            await guild_streams_manager.check()

        for stream in self.streams.values():
            stream._info_update = False
        await self.save_streams()

    # @commands.command(name="test")
    # @commands.guild_only()
    # @checks.mod_or_permissions(manage_channels=True)
    # async def test(self, ctx: commands.Context, id: str):
    #     stream = await self.add_stream(id)
    #     guild_manager = get_guild_manager(ctx.guild)
    #     await guild_manager.add_guild_stream([stream])

    async def save_streams(self) -> None:
        await self.config.streams.set(ConvertToRawData.dict(self.streams))