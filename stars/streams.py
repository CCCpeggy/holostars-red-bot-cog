# discord
from pickle import TUPLE
import discord

# redbot
from redbot.core import Config
from redbot.core.config import Group
from redbot.core import checks, commands, Config

# other
import os
import logging
import random
from typing import *
from datetime import datetime
from enum import Enum

# local
from stars.utils import *
from stars.channel.channel import Channel

_, log = get_logger()


class StreamStatus(str, Enum):
    NOTSURE = "notsure"
    UPCOMING = "upcoming"
    LIVE = "live"
    MISSING = "missing"
    PAST = "past"
    NEW = "new"

class Stream:

    def __init__(self, **kwargs):
        print(kwargs)
        self._bot: Red = kwargs.pop("bot")
        self.id: str = kwargs.pop("id", create_id())
        self._status: StreamStatus = StreamStatus(kwargs.pop("status", "notsure"))
        self.time: datetime = Time.to_datetime(kwargs.pop("time"))
        self._start_actual: datetime = Time.to_datetime(kwargs.pop("start_actual", None))   
        self.channel_id: str = kwargs.pop("channel_id")
        self._channel: "Channel" = kwargs.pop("channel")
        self.topic: str = kwargs.pop("topic", None)
        self.title: str = kwargs.pop("title", None)
        self.url: str = kwargs.pop("url", "")
        self.type: str = kwargs.pop("type", None)
        self.thumbnail: str = kwargs.pop("thumbnail", None)
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
        if not self._channel:
            return False
        if self._status in [StreamStatus.MISSING, StreamStatus.PAST]:
            return False
        return True

    def update_info(self, **kwargs):
        time = Time.to_datetime(kwargs.pop("time"))
        topic = kwargs.pop("topic", None)
        title = kwargs.pop("title", None)
        status = StreamStatus(kwargs.pop("status", "notsure"))
        start_actual = Time.to_datetime(kwargs.pop("start_actual"))
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
        if self._start_actual != start_actual:
            self._info_update = True
            self._start_actual = start_actual
        log.debug("已更新 stream：" + str(self))
        log.info("已更新 stream：" + self.id)
    
# class GuildStreamStatus(Enum):
#     STANDBY = 1
#     START = 2
#     END = 3

class GuildStream:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self._guild: discord.Guild = kwargs.pop("guild")
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

        self._notify_text_channel_id: int = kwargs.pop("notify_text_channel", None)
        self.notify_text_channel: discord.TextChannel = get_text_channel(self._bot, self._notify_text_channel_id)
    
    def is_valid(self):
        return self._stream.is_valid()

    def set_guild_collab_stream(self, guild_collab_stream: "GuildCollabStream"):
        self.guild_collab_stream_id = guild_collab_stream.id
        self._guild_collab_stream = guild_collab_stream

    def check(self):
        if self.is_valid():
            if self._stream._info_update:
                self._info_update = True
    
    def get_collab_notify_msg(self, message_format: str, chat_channel: discord.TextChannel) -> str:
        stream = self._stream
        # make message
        message_format = message_format.replace("{mention}", get_roles_str(self._guild, self._member.mention_roles))
        message_format = message_format.replace("{chat_channel}", chat_channel.mention)
        return message_format
                
    def get_notify_msg(self, message_format: str, need_embed: bool, chat_channel: discord.TextChannel) -> Tuple[str, discord.Embed]:
        stream = self._stream
        # make message
        message_format = message_format.replace("{title}", stream.title)
        message_format = message_format.replace("{channel_name}", stream._channel.name)
        message_format = message_format.replace("{url}", f"<{stream.url}>")
        message_format = message_format.replace("{mention}", get_roles_str(self._guild, self._member.mention_roles))
        message_format = message_format.replace("{description}", stream.topic if stream.topic else stream.title)
        message_format = message_format.replace("{new_line}", "\n")
        if chat_channel:
            message_format = message_format.replace("{chat_channel}", chat_channel.mention)
        
        # make embed
        if need_embed:
            embed = discord.Embed(title=stream.title, url=stream.url)
            embed.set_author(name=stream._channel.name, url=stream._channel.url)
            embed.set_footer(text=stream._channel.source_name)
            
            if stream._start_actual:
                embed.timestamp = stream._start_actual
            if stream.thumbnail:
                embed.set_image(url=get_url_rnd(stream.thumbnail))
            embed.colour = self._member.color
            return message_format, embed
        return message_format, None

    def __repr__(self):
        if self.is_valid():
            data = [
                f"GuildStream",
                f"> id：{self.id}",
                f"> 通知啟用狀態：{self.notify_msg_enable}",
                f"> 待機台發送頻道：{self.notify_text_channel.name if self.notify_text_channel else '空'}",
                f"> 通知訊息的 ID：{self.notify_msg_id}",
                f"> 所屬待機 ID：{self.guild_collab_stream_id}",
                f"> 資料更新：{self._info_update}",
                f"> 成員名稱：{self.member_name}",
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
        self._guild: discord.Guild = kwargs.pop("guild")
        self.id: str = kwargs.pop("id", create_id())
        self.guild_stream_ids: List[str] = kwargs.pop("guild_stream_ids", [])
        self._guild_streams: List[str] = kwargs.pop("guild_streams", {})
        self.standby_msg_enable: bool = kwargs.pop("standby_msg_enable", True)
        self.standby_msg_id: int = kwargs.pop("standby_msg_id", None)
        self._info_update: bool = kwargs.pop("info_update", True)
        self.description: str = kwargs.pop("description", None)
        self.time: datetime = Time.to_datetime(kwargs.pop("time", None))
        self._members: List["Member"] = kwargs.pop("members")
        self.member_names: List[str] = [member.name for member in self._members]
        self._saved_func = kwargs.pop("saved_func", None)
        self._status: StreamStatus = StreamStatus(kwargs.pop("status", "notsure"))
        self.standby_text_channel: discord.TextChannel = None
        self._standby_text_channel_id = kwargs.pop("standby_text_channel", None)

        self.notify_sent_member_names = kwargs.pop("notify_sent_member_names", [])
        if self.notify_sent_member_names is None:
            self.notify_sent_member_names = []

        self.standby_text_channel = get_text_channel(self._bot, self._standby_text_channel_id)

    
    def is_valid(self) -> bool:
        not_valid_guild_stream_ids = []
        for id, guild_stream in self._guild_streams.items():
            if not guild_stream:
                log.debug(f"reason 1: {id}")
                pass
            elif not guild_stream.is_valid():
                log.debug(f"reason 2: {id}")
                pass
            elif not guild_stream._guild_collab_stream:
                log.debug(f"reason 3: {id}")
                pass
            elif guild_stream._guild_collab_stream.id != self.id:
                log.debug(f"reason 4: {id}")
                pass
            else:
                continue
            not_valid_guild_stream_ids.append(id)
        if len(self._guild_streams) > 0 and len(not_valid_guild_stream_ids) == len(self._guild_streams):
            log.debug(f"reason 5: {len(not_valid_guild_stream_ids)}")
            return False
        if not Time.is_time_in_future_range(self.time, days=7):
            log.debug(f"reason 6: {self.time}")
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

    def get_standby_msg(self, message_format: str, need_embed: bool=True) -> Tuple[str, discord.Embed]:
        def get_url(self):
            data = []
            for guild_stream in self._guild_streams.values():
                data.append(f"{guild_stream._stream._channel.name}\n{guild_stream._stream.url}&r={random.randint(0,10000)}")
            return "\n".join(data)
        def get_title(self):
            return "\n".join([guild_stream._stream.title for guild_stream in self._guild_streams.values()])
        def get_description(self):
            if self.description:
                return self.description
            topics = [guild_stream._stream.topic for guild_stream in self._guild_streams.values() if guild_stream._stream.topic]
            if len(topics) > 0:
                return "/".join(set(topics))
            return get_title(self)
        def get_channel_name(self):
            return "\n".join([guild_stream._stream._channel.name for guild_stream in self._guild_streams.values()])
        
        # get all mention role in collab stream
        mention_roles = []
        for guild_stream in self._guild_streams.values():
            if guild_stream._member.mention_roles :
                mention_roles += guild_stream._member.mention_roles 
        mention_roles = list(set(mention_roles))

        # 將 TAG 的部分轉換為文字
        messages = []
        for message in message_format.split("{next_msg}"):
            message = message.replace("{time}", Time.to_discord_time_str(Time.get_specified_timezone(self.time)))
            message = message.replace("{title}", get_title(self))
            message = message.replace("{video_id}", list(self._guild_streams.keys())[0])
            message = message.replace("{channel_name}", get_channel_name(self))
            message = message.replace("{url}", get_url(self))
            message = message.replace("{mention}", get_roles_str(self._guild, mention_roles))
            message = message.replace("{description}", get_description(self))
            message = message.replace("{new_line}", "\n")
            messages.append(message)
        return messages
    
    def add_guild_stream(self, guild_stream: "GuildStream"):
        if guild_stream.id not in self.guild_stream_ids:
            if guild_stream._guild_collab_stream:
                self.remove_guild_stream(guild_stream)
            self.guild_stream_ids.append(guild_stream.id)
            self._guild_streams[guild_stream.id] = guild_stream
            guild_stream._guild_collab_stream = self
            guild_stream.guild_collab_stream_id = self.id
            self.add_member(guild_stream._member)
            self._info_update = True
            
    def remove_guild_stream(self, guild_stream: "GuildStream"):
        if guild_stream.id in self.guild_stream_ids:
            self.guild_stream_ids.remove(guild_stream.id)
            self._guild_streams.pop(guild_stream.id, None)
            guild_stream._guild_collab_stream = None
            guild_stream.guild_collab_stream_id = None
            self._info_update = True
    
    def add_member(self, member: "Member"):
        if member.name not in self.member_names:
            self.member_names.append(member.name)
            self._members.append(member)
            self._info_update = True
    
    def remove_member(self, member: "Member"):
        if member.name in self.member_names:
            for guild_stream in list(self._guild_streams.values()):
                if guild_stream.member_name == member.name:
                    self.remove_guild_stream(guild_stream)
            self.member_names.remove(member.name)
            self._members.remove(member)
            self._info_update = True
    
    def check_guild_stream_fit(self, guild_stream: "GuildStream") -> bool:
        if not Time.is_diff_in_range(guild_stream._stream.time, self.time, days=5, minutes=15):
            # time is not in range
            log.debug(f"reason 1: {guild_stream._stream.time}, {self.time}")
            return False
        if guild_stream._member.name not in [m.name for m in self._members]:
            # the member is not belong to the guild_stream
            log.debug(f"reason 2: {guild_stream._member.name}, {[m.name for m in self._members]}")
            return False
        if guild_stream._member.name in [g._member.name for g in self._guild_streams.values()]:
            # the member is already in guild_stream
            log.debug(f"reason 3: {guild_stream._member.name}")
            return False
        return True

    def __repr__(self):
        if self.is_valid():
            data = [
                f"GuildCollabStream",
                f"> id：{self.id}",
                f"> 待機台啟用狀態：{self.standby_msg_enable}",
                f"> 待機台發送頻道：{self.standby_text_channel.name if self.standby_text_channel else '空'}",
                f"> 相關直播 ID：{', '.join(self.guild_stream_ids)}",
                f"> 待機台時間：{self.time}",
                f"> 資料更新：{self._info_update}",
                f"> 狀態：{self._status}",
                f"> 成員名單：{self.member_names}",
                # f"> check: {list(self._guild_streams.values())[0]._guild_collab_stream.id}",
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

    async def initial(self):
        async def load_guild_streams():
            for id, raw_data in (await self.config.guild_streams()).items():
                guild_stream = await self.add_guild_stream(save=False, **raw_data)
        await load_guild_streams()
        
        async def load_collab_guild_streams():
            for id, raw_data in (await self.config.guild_collab_streams()).items():
                await self.add_guild_collab_stream(save=False, **raw_data)
        await load_collab_guild_streams()

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
    
    async def add_guild_stream_to_guild_collab_stream(self, guild_collab_stream: "GuildCollabStream", stream_ids: List[str]):
        for id in stream_ids:
            guild_stream = self.get_guild_stream(id)
            if guild_stream:
                guild_collab_stream.add_guild_stream(guild_stream)
            else:
                log.error(f"not found guild stream by {id}")
        await list(guild_collab_stream._guild_streams.values())[0]._saved_func()
        await guild_collab_stream._saved_func()
    
    async def add_member_to_guild_collab_stream(self, guild_collab_stream: "GuildCollabStream", member_names: List[str]):
        guild_members_manager = await self.manager.members_manager.get_guild_manager(self.guild)
        for name in member_names:
            if name not in guild_members_manager.members:
                log.error(f"{name} not in members")
            if name in guild_collab_stream.member_names:
                continue
            member = guild_members_manager.members[name]
            guild_collab_stream.add_member(member)
        await guild_collab_stream._saved_func()
    
    def get_guild_stream(self, id: str)  -> "GuildStream":
        return self.guild_streams.get(id, None)
    
    def get_guild_collab_stream(self, id: str)  -> "GuildCollabStream":
        return self.guild_collab_streams.get(id, None)

    def get_guild_collab_stream_by_stream_id(self, id: str)  -> "GuildCollabStream":
        if id not in self.guild_streams:
            return None
        return self.guild_streams[id]._guild_collab_stream

    async def add_guild_stream(self, stream_id, save=True, **kwargs) -> "GuildStream":
        if stream_id in self.guild_streams:
            log.debug("已存在，所以沒有新增 guild_stream：" + stream_id)
            return None
            
        stream = self.get_stream(stream_id)
        if stream == None:
            log.debug("stream is none，所以沒有新增 guild_stream：" + stream_id)
            return None
            
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
        notify_text_channel = kwargs.pop("notify_text_channel", member.notify_text_channel)
        guild_stream = GuildStream(
            bot=self.bot,
            guild=self.guild,
            stream_id=stream_id,
            stream=stream,
            notify_text_channel=get_textchannel_id(notify_text_channel),
            saved_func=self.save_guild_streams,
            member=member,
            **kwargs
        )
        if guild_stream.is_valid():
            self.guild_streams[stream_id] = guild_stream
            if save:
                await self.save_guild_streams()
            log.debug("已新增 guild_stream：" + str(guild_stream))
            log.info("已新增 guild_stream：" + guild_stream.id)
            return guild_stream

    async def add_guild_collab_stream(self, guild_stream_ids: List[str]=[], save=True, **kwargs) -> "GuildCollabStream":
        class InvalidException(Exception):
            pass
        try:
            # get guild streams
            is_member_only = False
            guild_streams = {}
            for guild_stream_id in guild_stream_ids:
                guild_stream = self.get_guild_stream(guild_stream_id)
                if guild_stream:
                    guild_streams[guild_stream_id] = guild_stream
                    if guild_stream._stream.topic == "membersonly":
                        is_member_only = True
                #     if not guild_stream.guild_collab_stream_id:
                #         continue
                # log.debug("沒有新增 guild_collab_stream 成功：" + ', '.join(guild_stream_ids))
                # return None
            
            # get members
            member_names = kwargs.pop("member_names", None)
            members = [guild_stream._member for guild_stream in guild_streams.values()]
            if member_names:
                guild_members_manager = await self.manager.members_manager.get_guild_manager(self.guild)
                members += [guild_members_manager.members[name] for name in member_names if name in guild_members_manager.members]
            members = list(set(members))
            
            if "standby_text_channel" in kwargs:
                chat_text_channel = kwargs.pop("standby_text_channel")
            elif len(members) == 0:
                chat_text_channel = None
            elif is_member_only:
                chat_text_channel = members[0].memeber_text_channel
            else:
                chat_text_channel = members[0].chat_text_channel
                
            # create guild_collab_stream
            guild_collab_stream = GuildCollabStream(
                bot=self.bot,
                guild=self.guild,
                members=members,
                guild_stream_ids=list(guild_streams.keys()),
                guild_streams=guild_streams,
                standby_text_channel=get_textchannel_id(chat_text_channel),
                saved_func=self.save_guild_collab_streams,
                **kwargs
            )
            for guild_stream in guild_streams.values():
                guild_stream.set_guild_collab_stream(guild_collab_stream)
            if not guild_collab_stream.is_valid():
                raise InvalidException
            self.guild_collab_streams[guild_collab_stream.id] = guild_collab_stream
            if save:
                await self.save_guild_collab_streams()
            log.debug("已新增 guild_collab_stream：" + str(guild_collab_stream))
            log.info("已新增 guild_collab_stream：" + ', '.join(guild_stream_ids))
            return guild_collab_stream
        except InvalidException:
            log.debug("[InvalidException] 沒有新增 guild_collab_stream 成功：" + ', '.join(guild_stream_ids))
        # except Exception:
        #     log.debug("沒有新增 guild_collab_stream 成功：" + ', '.join(guild_stream_ids))
        return None

    async def save_guild_streams(self) -> None:
        await self.config.guild_streams.set(ConvertToRawData.dict(self.guild_streams))
        
    async def save_guild_collab_streams(self) -> None:
        await self.config.guild_collab_streams.set(ConvertToRawData.dict(self.guild_collab_streams))

    # async def check_old_guild_stream(self):
    #     for guild_stream in self.guild_streams.values():
    #         if guild_stream._guild_collab_stream:
    #             for guild_collab_stream in self.guild_collab_streams.values():
    #                 if guild_collab_stream.check_guild_stream_fit(guild_stream):
    #                     guild_collab_stream.add_guild_stream(guild_stream)
    #                     await guild_collab_stream._saved_func()
    #                     break
    
    async def check(self):
        for guild_stream in self.guild_streams.values():
            # await self.check_old_guild_stream() # TODO
            if not guild_stream._guild_collab_stream:
                for guild_collab_stream in self.guild_collab_streams.values():
                    if guild_collab_stream.check_guild_stream_fit(guild_stream):
                        info_text_channel = await self.manager.send_manager.get_info_channel(self.guild)
                        await choose_whether_add_guild_stream_into_guild_collab_stream(self.bot, info_text_channel, guild_stream, guild_collab_stream, False)
                        break
                else:
                    await self.add_guild_collab_stream([guild_stream.id], time=guild_stream._stream.time)
                guild_stream._info_update = True
            guild_stream.check()

        for guild_collab_stream in self.guild_collab_streams.values():
            guild_collab_stream.check()

        # delete not valid guild stream
        remove_guild_stream_ids = []
        for id, guild_stream in self.guild_streams.items():
            if not guild_stream.is_valid():
                self.guild_streams[id]._guild_collab_stream = None
                remove_guild_stream_ids.append(id)
        for id in remove_guild_stream_ids:
            del self.guild_streams[id]

        # delete not valid guild collab stream
        remove_guild_collab_stream_ids = []
        for id, guild_collab_stream in self.guild_collab_streams.items():
            if not guild_collab_stream.is_valid():
                remove_guild_collab_stream_ids.append(id)
        for id in remove_guild_collab_stream_ids:
            del self.guild_collab_streams[id]

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


    async def initial(self):
        async def load_streams():
            # from .errors import MException
            for id, raw_data in (await self.config.streams()).items():
                await self.add_stream(save=False, **raw_data)
        await load_streams()
        async def load_guild():
            for guild_id, config in (await self.config.all_guilds()).items():
                await self.get_guild_manager(int(guild_id))
        await load_guild()
            
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
            self.streams[id]._status = StreamStatus.MISSING
            del self.streams[id]
        await self.save_streams()

    async def check(self) -> None:
        for guild_streams_manager in self.guild_managers.values():
            await guild_streams_manager.check()

        for stream in self.streams.values():
            stream._info_update = False
        await self.save_streams()

    async def save_streams(self) -> None:
        await self.config.streams.set(ConvertToRawData.dict(self.streams))
    
    
    @commands.group(name="stream")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def stream_group(self, ctx: commands.Context):
        pass

    # set specify channel to textchannel
    @stream_group.command(name="notify_textchannel")
    async def set_notify_textchannel(self, ctx: commands.Context, stream_id: str, text_channel: discord.TextChannel):
        guild_streams_manager = await self.get_guild_manager(ctx.guild)
        guild_stream = guild_streams_manager.get_guild_stream(stream_id)
        guild_stream.notify_text_channel = text_channel
        await self.save_streams()
        await Send.send(ctx, str(guild_stream))
    
    @stream_group.command(name="standby_textchannel")
    async def set_standby_textchannel(self, ctx: commands.Context, stream_id: str, text_channel: discord.TextChannel):
        guild_streams_manager = await self.get_guild_manager(ctx.guild)
        guild_collab_stream = guild_streams_manager.get_guild_collab_stream_by_stream_id(stream_id)
        guild_collab_stream.standby_text_channel = text_channel
        await self.save_streams()
        await Send.send(ctx, str(guild_collab_stream))

    @stream_group.command(name="add")
    async def stream_add_stream(self, ctx: commands.Context, stream_id: str):
        key = (await self.bot.get_shared_api_tokens("youtube"))["api_key"]
        stream_info = await Channel.get_stream_info(stream_id, key)
        log.debug(str(stream_info))
        stream = await self.add_stream(
            save=True,
            **stream_info
        )
        if stream:
            await Send.add_completed(ctx, "直播", stream)
        else:
            await ctx.send("**直播**新增失敗")
    
    # set collab - by channel, video (exist channel or not exist)
    @stream_group.group(name="collab")
    async def collab_group(self, ctx: commands.Context):
        pass
    
    @collab_group.command(name="add")
    async def add_collab(self, ctx: commands.Context, stream_ids: str, chat_channel: discord.TextChannel=None):
        """ 將多個直播間設為聯動
        """
        guild_members_manager = await self.manager.members_manager.get_guild_manager(ctx.guild)
        guild_streams_manager = await self.get_guild_manager(ctx.guild)
        
        # get first guild collab stream
        stream_ids = stream_ids.split(",")
        guild_collab_stream = guild_streams_manager.get_guild_collab_stream_by_stream_id(stream_ids[0])
        
        # get already know collab member name
        member_names = [guild_stream._member.name for guild_stream in guild_streams_manager.guild_streams.values() if guild_stream.id in stream_ids]
        if guild_collab_stream:
            member_names += [m.name for m in guild_collab_stream._members]
        
        # get member by reaction
        emoji_member_name = {}
        for member in guild_members_manager.members.values():
            if member.emoji and member.name not in member_names:
                emoji_member_name[member.emoji] = member.name
        emojis = await add_waiting_reaction(self.bot, ctx.author, ctx.message, list(emoji_member_name.keys()))
        member_names += [v for k, v in emoji_member_name.items() if k in emojis]
        
        if guild_collab_stream:
            await guild_streams_manager.add_guild_stream_to_guild_collab_stream(guild_collab_stream, stream_ids)
            await guild_streams_manager.add_member_to_guild_collab_stream(guild_collab_stream, member_names)
            await Send.update_completed(ctx, "guild_collab_stream", guild_collab_stream)
        else:
            data = {}
            if chat_channel:
                data["standby_text_channel"] = chat_channel
            data["member_names"] = member_names
            data["time"] = guild_streams_manager.get_guild_stream(stream_ids[0])._stream.time
            guild_collab_stream = await guild_streams_manager.add_guild_collab_stream(stream_ids, **data)
            if guild_collab_stream:
                await Send.add_completed(ctx, "guild_collab_stream", guild_collab_stream)
            else:
                await Send.data_error(ctx, "guild_collab_stream")
        
        # search old guild_stream whether belong to this guild_collab_stream
        for guild_stream in guild_streams_manager.guild_streams.values():
            if guild_collab_stream.check_guild_stream_fit(guild_stream):
                await choose_whether_add_guild_stream_into_guild_collab_stream(self.bot, ctx, guild_stream, guild_collab_stream, False)
                
    @collab_group.command(name="create")
    async def create_collab(self, ctx: commands.Context, time: FutureDatetimeConverter, chat_channel: discord.TextChannel):
        guild_members_manager = await self.manager.members_manager.get_guild_manager(ctx.guild)
        guild_streams_manager = await self.get_guild_manager(ctx.guild)
        
        # get member by reaction
        emoji_member_name = {}
        for member in guild_members_manager.members.values():
            emoji_member_name[member.emoji] = member.name
        emojis = await add_waiting_reaction(self.bot, ctx.author, ctx.message, list(emoji_member_name.keys()))
        member_names = [v for k, v in emoji_member_name.items() if k in emojis]
        
        if len(member_names) < 1:
            return
        
        data = {}
        data["member_names"] = member_names
        data["time"] = time
        data["standby_text_channel"] = chat_channel
        guild_collab_stream = await guild_streams_manager.add_guild_collab_stream(**data)
        if guild_collab_stream:
            await Send.add_completed(ctx, "guild_collab_stream", guild_collab_stream)
        else:
            await Send.data_error(ctx, "guild_collab_stream")
        
        # search old guild_stream whether belong to this guild_collab_stream
        for guild_stream in guild_streams_manager.guild_streams.values():
            if guild_collab_stream.check_guild_stream_fit(guild_stream):
                await choose_whether_add_guild_stream_into_guild_collab_stream(self.bot, ctx, guild_stream, guild_collab_stream, False)

    @collab_group.command(name="remove_stream")
    async def remove_stream_from_collab(self, ctx: commands.Context, guild_collab_stream: GuildCollabStreamConverter, guild_stream: GuildStreamConverter):
        if guild_stream.id not in guild_collab_stream._guild_streams:
            await Send.not_existed(ctx, "聯動關聯直播", guild_stream)
        else:
            guild_collab_stream.remove_guild_stream(guild_stream)
            await guild_stream._saved_func()
            await guild_collab_stream._saved_func()
            await Send.remove_completed(ctx, "聯動關聯直播", guild_collab_stream)
    
    @collab_group.command(name="add_stream")
    async def add_stream_from_collab(self, ctx: commands.Context, guild_collab_stream: GuildCollabStreamConverter, guild_stream: GuildStreamConverter):
        if guild_stream.id in guild_collab_stream._guild_streams:
            await Send.already_existed(ctx, "聯動關聯直播", guild_stream.id)
        else:
            guild_collab_stream.add_guild_stream(guild_stream)
            await guild_stream._saved_func()
            await guild_collab_stream._saved_func()
            await Send.add_completed(ctx, "聯動關聯直播", guild_collab_stream)
    
    # TODO: remove member、add member
    @collab_group.command(name="remove_member")
    async def remove_member_from_collab(self, ctx: commands.Context, guild_collab_stream: GuildCollabStreamConverter, member: MemberConverter):
        if member not in guild_collab_stream._members:
            await Send.not_existed(ctx, "聯動成員", member.name)
        else:
            guild_collab_stream.remove_member(member)
            await guild_collab_stream._saved_func()
            await Send.remove_completed(ctx, "聯動成員", guild_collab_stream)
    
    @collab_group.command(name="add_member")
    async def add_member_from_collab(self, ctx: commands.Context, guild_collab_stream: GuildCollabStreamConverter, member: MemberConverter):
        if member in guild_collab_stream._members:
            await Send.already_existed(ctx, "聯動成員", member.name)
        else:
            guild_collab_stream.add_member(member)
            await guild_collab_stream._saved_func()
            await Send.add_completed(ctx, "聯動成員", guild_collab_stream)

    # set no send
    @stream_group.command(name="notify_status")
    async def set_notify_status(self, ctx: commands.Context, stream_id: str, status: bool):
        """ 設定直播的通知是否要啟用
        status: yes、no
        """
        guild_streams_manager = await self.get_guild_manager(ctx.guild)
        guild_stream = guild_streams_manager.get_guild_stream(stream_id)
        guild_stream.notify_msg_enable = status
        await self.save_streams()
        await Send.send(ctx, str(guild_stream))
    
    @stream_group.command(name="standby_status")
    async def set_standby_status(self, ctx: commands.Context, stream_id: str, status: bool):
        """ 設定待機台是否要啟用
        status: yes、no
        """
        guild_streams_manager = await self.get_guild_manager(ctx.guild)
        guild_collab_stream = guild_streams_manager.get_guild_collab_stream_by_stream_id(stream_id)
        guild_collab_stream.standby_msg_enable = status
        await self.save_streams()
        await Send.send(ctx, str(guild_collab_stream ))

    # list
    @stream_group.command(name="list")
    async def standby_list(self, ctx: commands.Context, member: MemberConverter=None):
        guild_streams_manager = await self.get_guild_manager(ctx.guild)
        data = []
        for guild_stream in guild_streams_manager.guild_streams.values():
            if not member or guild_stream._member == member:
                data.append(str(guild_stream))
        await Send.send(ctx, "\n".join(data))
        data = []
        for guild_collab_stream in guild_streams_manager.guild_collab_streams.values():
            if not member or member in [g._member for g in guild_collab_stream._guild_streams.values()]:
                data.append(str(guild_collab_stream))
        await self.save_streams()
        await Send.send(ctx, "\n".join(data))

    # resend
    # update
    @stream_group.command(name="update")
    async def update_message(self, ctx: commands.Context, member: MemberConverter):
        """ 要求重新抓取直播資訊，並在下次定時檢測是更新 (可用於待機台的圖片更新時)
        """
        update_guild_streams_manager = []
        guild_streams_manager = await self.get_guild_manager(ctx.guild)
        for guild_stream in guild_streams_manager.guild_streams.values():
            if guild_stream._member.name == member.name:
                guild_stream._guild_collab_stream._info_update = True
                update_guild_streams_manager.append(str(guild_stream._guild_collab_stream))
        await self.save_streams()
        await Send.send(ctx, "在下次的定時檢測時，會更新以下直播: " + ", ".join(update_guild_streams_manager))

async def choose_whether_add_guild_stream_into_guild_collab_stream(bot, place, guild_stream: GuildStream, guild_collab_stream: GuildCollabStream, default: bool):
    msg = await place.send(f"是否要將直播 {guild_stream.id} 加進聯動 {guild_collab_stream} (預設**{'加入' if default else '不加入'})**")
    async def add():
        guild_collab_stream.add_guild_stream(guild_stream)
        await guild_stream._saved_func()
        await guild_collab_stream._saved_func()
        log.info(f"add {guild_stream.id} into {guild_collab_stream.id}")
        log.debug(f"add {guild_stream.id} into {guild_collab_stream.id}: {guild_collab_stream}")
    async def remove():
        guild_collab_stream.remove_guild_stream(guild_stream)
        await guild_stream._saved_func()
        await guild_collab_stream._saved_func()
        log.info(f"remove {guild_stream.id} {guild_collab_stream.id}")
        log.debug(f"remove {guild_stream.id} {guild_collab_stream.id}: {guild_collab_stream}")
    if default:
        await add()
    def whether_to_add(guild_stream):
        async def event():
            belong_or_not = await add_bool_reaction(bot, msg)
            if not default and belong_or_not:
                await add()
                await place.send(f"已將直播 {guild_stream.id} 加進聯動 {guild_collab_stream}")
            if default and not belong_or_not:
                await remove()
                await place.send(f"直播 {guild_stream.id} 已從聯動中取消 {guild_collab_stream}")
        return event
    do_event_in_time(
        bot,
        whether_to_add(guild_stream), 
        Time.get_diff_from_now_total_sec(guild_collab_stream.time) + 3600,
        async_timeout_func=msg.clear_reactions
    )

# TODO: 產生討論串