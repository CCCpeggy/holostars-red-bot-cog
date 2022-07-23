# discord
import discord

# redbot
from redbot.core.bot import Red
from redbot.core import commands

# other
from typing import *

import logging
def get_logger(level: int=logging.DEBUG)->logging.Logger:
    from redbot.core.i18n import Translator
    _ = Translator("StarsStreams", __file__)
    log = logging.getLogger("red.core.cogs.StarStreams")
    log.setLevel(level)
    return _, log
_, log = get_logger()

def get_text_channel(place: Union[discord.Guild, Red], channel: Union[int, str, discord.TextChannel, None]) -> discord.TextChannel:
    if isinstance(channel, int) or isinstance(channel, str):
        return place.get_channel(channel)
    return channel

def create_id():
    import uuid
    return uuid.uuid4().hex[:16]

# def checkInit(method):
#     def _checkInit(self, *args, **kwargs):
#         if not self.isInit:
#             from .errors import NotInitYet
#             raise NotInitYet
#     return _checkInit   

async def getHttpData(url, params={}):
    import aiohttp
    from .errors import MException
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as r:
            data = await r.json()
            try:
                check_api_errors(data)
            except MException as e:
                log.error(e.get_message())
            except Exception as e:
                log.error(e)
            else:
                return data
    return None

# async def getHttpDataText(url, params={}):
#     import aiohttp
#     from .errors import MException
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url, params=params) as r:
#             data = await r.text()
#             if r.status == 404:
#                 log.warning(f"404: {url}")
#                 return None
#             return data
#     return None

def check_api_errors(data: dict):
    from .errors import APIError, InvalidYoutubeCredentials, YoutubeQuotaExceeded
    if "error" in data:
        error_code = data["error"]["code"]
        if error_code == 400 and data["error"]["errors"][0]["reason"] == "keyInvalid":
            raise InvalidYoutubeCredentials()
        elif error_code == 403 and data["error"]["errors"][0]["reason"] in (
            "dailyLimitExceeded",
            "quotaExceeded",
            "rateLimitExceeded",
        ):
            raise YoutubeQuotaExceeded()
        raise APIError(error_code, data)

async def get_message(channel: discord.TextChannel, message_id: int) -> "Message":
    try:
        message = await channel.fetch_message(message_id)
    except:
        return None
    else:
        return message
    
def get_role(guild: discord.Guild, id: int) -> discord.Role:
    from discord.utils import get
    return get(guild.roles, id=id)
    
def get_roles_str(guild: discord.Guild, ids: List[int]) -> str:
    if ids:
        role_mentions = []
        for id in ids:
            role = get_role(guild, id)
            if role:
                role_mentions.append(role.mention)
        if len(role_mentions) > 0:
            return " ".join(role_mentions)
    return ""
        
def get_textchannel_id(textchannel: discord.TextChannel):
    if textchannel == None:
        return None
    elif isinstance(textchannel, int):
        return textchannel
    elif isinstance(textchannel, str):
        return int(textchannel)
    elif isinstance(textchannel, discord.TextChannel):
        return textchannel.id
    else:
        raise Exception

def getEmoji(guild_emojis, ori_emoji):
    # check guild
    for e in guild_emojis:
        if str(e.id) in ori_emoji and e.name in ori_emoji:
            return e
    # check emoji dictionary
    import emoji
    if ori_emoji in emoji.EMOJI_DATA:
        return ori_emoji
    return None

def do_event_in_time(bot, func, time: int, timeout_func=None, async_timeout_func=None):
    import asyncio
    async def event():
        try:
            await asyncio.wait_for(func(), timeout=time)
        except asyncio.TimeoutError:
            log.debug(f'{func} timeout!')
            if timeout_func:
                timeout_func()
            if async_timeout_func:
                await async_timeout_func()
    bot.loop.create_task(event())

async def add_reaction(message: discord.Message, emojis: List[str]):
    import contextlib
    with contextlib.suppress(discord.NotFound):
        for emoji in emojis:
            await message.add_reaction(emoji)

async def add_waiting_reaction(bot, user: discord.User, message: discord.Message, emojis: List[str]):
    done_emoji = "\N{WHITE HEAVY CHECK MARK}"
    cancel_emoji = "\N{NEGATIVE SQUARED CROSS MARK}"
    emojis = [done_emoji, cancel_emoji] + emojis
    import asyncio
    emojis = [e for e in emojis if e is not None]
    task = asyncio.create_task(add_reaction(message, emojis))
    emojis = [getEmoji(message.guild.emojis, e) for e in emojis]
    selected = {e: False for e in emojis[2:]}
    try:
        async def reaction_task(event):
            nonlocal selected
            while True:
                from redbot.core.utils.predicates import ReactionPredicate
                r, u = await bot.wait_for(
                    event, check=ReactionPredicate.with_emojis(emojis, message, user))
                if r.emoji == done_emoji:
                    break
                elif r.emoji == cancel_emoji:
                    selected = {}
                    break
                else:
                    selected[r.emoji] = not selected[r.emoji]
        tasks = [
            asyncio.create_task(reaction_task('reaction_remove')),
            asyncio.create_task(reaction_task('reaction_add'))
        ]
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=30)
      
    except asyncio.TimeoutError:
        selected = {}

    for task in tasks:
        if task is not None:
            task.cancel()
    if task is not None:
        task.cancel()
    
    selected = [k for k, v in selected.items() if v]
    await message.clear_reactions()
    return selected

async def add_bool_reaction(bot, message: discord.Message) -> bool:
    done_emoji = "\N{WHITE HEAVY CHECK MARK}"
    cancel_emoji = "\N{NEGATIVE SQUARED CROSS MARK}"
    emojis = [done_emoji, cancel_emoji]
    import asyncio
    task = asyncio.create_task(add_reaction(message, emojis))

    try:
        while True:
            from redbot.core.utils.predicates import ReactionPredicate
            from redbot.core.utils.mod import is_mod_or_superior
            (r, u) = await bot.wait_for(
                "reaction_add",
                check=ReactionPredicate.with_emojis(emojis, message),
                timeout=86400  # 1 天
            )
            if await is_mod_or_superior(bot, u):
                if u != message.author or await bot.is_owner(u):
                    break
    except asyncio.TimeoutError:
        await message.remove_reaction(done_emoji)
        return False

    if task is not None:
        task.cancel()
    if r.emoji == done_emoji:
        await message.remove_reaction(cancel_emoji, bot.user)
        return True
    await message.remove_reaction(done_emoji, bot.user)
    return False

class MemberConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, member_name: str) -> "Member":
        if member_name == None:
            return None
        from .manager import members_manager
        guild_members_manager = await members_manager.get_guild_manager(ctx.guild)
        member = guild_members_manager.members.get(member_name, None)
        if member:
            return member
        else:
            raise commands.BadArgument(member_name + " is not existed!!")

class EmojiConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg_emoji: str) -> str:
        emoji = getEmoji(ctx.guild.emojis, arg_emoji)
        if emoji:
            return emoji
        else:
            raise commands.BadArgument(arg_emoji + " is bad emoji!!")
        

class ColorChannelonverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str) -> int:
        try:
            num = 0
            if arg[:2] == "0x":
                num = int(arg, base=16)
            else:
                num = int(arg)
            if num >= 0 and num <= 255:
                return num
            raise commands.BadArgument(num + " need to between 0 to 255.")
        except:
            raise commands.BadArgument(arg + " is invaild integer.")
        

class FutureDatetimeConverter(commands.Converter):
    from datetime import datetime
    async def convert(self, ctx: commands.Context, arg_time: str) -> datetime:
        try:
            time = Time.to_datetime(arg_time)
        except:
            raise commands.BadArgument(arg_time + " is invalid time!!")
        Time.add_timezone(time, "Asia/Taipei")
        if Time.get_diff_from_now_total_sec(time) <= 0:
            raise commands.BadArgument(arg_time + " is pass time!!")
        return time
    
class GuildCollabStreamConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg_id: str) -> "GuildCollabStream":
        from .manager import streams_manager
        guild_streams_manager = await streams_manager.get_guild_manager(ctx.guild)
        guild_collab_stream = guild_streams_manager.get_guild_collab_stream(arg_id)
        if guild_collab_stream:
            return guild_collab_stream
        else:
            raise commands.BadArgument(arg_id + " is not found")
 
class GuildStreamConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg_id: str) -> "GuildStream":
        from .manager import streams_manager
        guild_streams_manager = await streams_manager.get_guild_manager(ctx.guild)
        guild_stream = guild_streams_manager.get_guild_stream(arg_id)
        if guild_stream:
            return guild_stream
        else:
            raise commands.BadArgument(arg_id + " is not found")
               

def get_url_rnd(url):
    """Appends a random parameter to the url to avoid Discord's caching"""
    from string import ascii_letters
    from random import choice
    return url + "?rnd=" + "".join([choice(ascii_letters) for _ in range(6)])

class Youtube:
    @staticmethod
    def check_channel_id(id: str) -> bool:
        import re
        channel_id_re = re.compile("^UC[-_A-Za-z0-9]{21}[AQgw]$")
        return channel_id_re.fullmatch(id)

class ConvertToRawData:
    @staticmethod
    def export_class(data):
        export_func = getattr(data, "export", None)
        if callable(export_func):
            return data.export()
        else:
            from datetime import datetime
            from enum import Enum
            raw_data = {}
            for k, v in data.__dict__.items():
                if k.startswith("_"):
                    continue
                if not v:
                    raw_data[k] = None
                elif isinstance(v, (int, str, list, dict, Enum)):
                    raw_data[k] = v
                elif isinstance(v, datetime):
                    raw_data[k] = Time.to_standard_time_str(v)
                else:
                    raw_data[k] = v.id
        return raw_data

    @staticmethod
    def dict(data: dict):
        raw_data = {}
        for key, value in data.items():
            raw_data[str(key)] = ConvertToRawData.export_class(value)
        return raw_data

    @staticmethod
    def list(data: list):
        raw_data = []
        for value in data:
            raw_data.append(ConvertToRawData.export_class(value))
        return raw_data

class Send:

    SendPlaceType = Union[commands.Context, discord.TextChannel]
    @staticmethod
    async def set_up_completed(send_place: SendPlaceType, name:str, obj=None):
        if obj == None:
            await send_place.send(f"**{name}**已設定完成")
        elif isinstance(obj, (discord.TextChannel, discord.Role)):
            await send_place.send(f"**{name}**已設定為 {obj.mention}",
                allowed_mentions=discord.AllowedMentions.none())
        else:
            await send_place.send(f"**{name}**已設定為\n{str(obj)}")
    @staticmethod
    async def add_completed(send_place: SendPlaceType, name:str, obj=None):
        if obj == None:
            await send_place.send(f"**{name}**已新增一筆資料")
        elif isinstance(obj, (discord.TextChannel, discord.Role)):
            await send_place.send(f"**{name}**已新增一筆：{obj.mention}",
                allowed_mentions=discord.AllowedMentions.none())
        else:
            await send_place.send(f"**{name}**已新增一筆\n{str(obj)}")
    @staticmethod
    async def update_completed(send_place: SendPlaceType, name:str, obj=None):
        if obj == None:
            await send_place.send(f"**{name}**已更新一筆資料")
        elif isinstance(obj, (discord.TextChannel, discord.Role)):
            await send_place.send(f"**{name}**已更新一筆：{obj.mention}",
                allowed_mentions=discord.AllowedMentions.none())
        else:
            await send_place.send(f"**{name}**已更新一筆\n{str(obj)}")
    @staticmethod
    async def remove_completed(send_place: SendPlaceType, name:str, obj=None):
        if obj == None:
            await send_place.send(f"**{name}**已刪除一筆資料")
        elif isinstance(obj, (discord.TextChannel, discord.Role)):
            await send_place.send(f"**{name}**已刪除一筆：{obj.mention}",
                allowed_mentions=discord.AllowedMentions.none())
        else:
            await send_place.send(f"**{name}**已刪除一筆\n{str(obj)}")
    @staticmethod
    async def already_existed(send_place: SendPlaceType, name:str, obj=None):
        if obj == None:
            await send_place.send(f"**{name}**已經存在")
        elif isinstance(obj, (discord.TextChannel, discord.Role)):
            await send_place.send(f"**{name}**已經存在：{obj.mention}",
                allowed_mentions=discord.AllowedMentions.none())
        else:
            await send_place.send(f"**{name}**已經存在\n{str(obj)}")
    @staticmethod
    async def not_existed(send_place: SendPlaceType, name:str, obj=None):
        if obj == None:
            await send_place.send(f"**{name}**不存在")
        elif isinstance(obj, (discord.TextChannel, discord.Role)):
            await send_place.send(f"**{name}**不存在：{obj.mention}",
                allowed_mentions=discord.AllowedMentions.none())
        else:
            await send_place.send(f"**{name}**不存在\n{str(obj)}")
    @staticmethod
    async def data_error(send_place: SendPlaceType, name:str, obj=None):
        if obj == None:
            await send_place.send(f"**{name}**資料或格式錯誤")
        elif isinstance(obj, (discord.TextChannel, discord.Role)):
            await send_place.send(f"**{name}**資料或格式錯誤：{obj.mention}",
                allowed_mentions=discord.AllowedMentions.none())
        else:
            await send_place.send(f"**{name}**資料或格式錯誤\n{str(obj)}")
    @staticmethod
    async def empty(send_place: SendPlaceType, name:str):
        await send_place.send(f"**{name}**是空的")

    @staticmethod
    async def send(send_place: SendPlaceType, content:str):
        text_len = len(content)
        for start in range(0, text_len, 1900):
            end = start + 1900
            if text_len < end:
                end = text_len
            await send_place.send(content[start:end])
        
class GetSendStr:
    @staticmethod
    def get_channel_mention(channel, default="未設定"):
        return channel.mention if channel else '未設定'
    @staticmethod
    def concat_list(data: list):
        return ", ".join(data) if data else None


from datetime import datetime
class Time:
    @staticmethod
    def add_timezone(time: datetime, zone: str=None) -> datetime:
        import pytz
        if zone:
            return pytz.timezone(zone).localize(time)
        return pytz.utc.localize(time)

    @staticmethod
    def to_datetime(time: Union[str, datetime, None]) -> datetime:
        if isinstance(time, datetime):
            return time
        elif isinstance(time, str):
            from dateutil.parser import parse as parse_time
            time = parse_time(time)
            if time.tzinfo == None:
                time = Time.add_timezone(time)
            return time
        return None

    @staticmethod
    def to_standard_time_str(time: datetime) -> str:
        return time.isoformat()
    
    @staticmethod
    def get_total_seconds(time: datetime) -> int:
        return int(time.timestamp())

    @staticmethod
    def to_discord_time_str(time: datetime) -> str:
        return "<t:{}:f>".format(Time.get_total_seconds(time))

    @staticmethod
    def get_specified_timezone(time: datetime, timezone: str='Asia/Taipei') -> datetime:
        if time.tzinfo == None:
            time = Time.add_timezone(time)
        import pytz
        return time.astimezone(pytz.timezone(timezone))

    @staticmethod
    def get_now():
        from datetime import timezone
        return datetime.now(timezone.utc)

    @staticmethod
    def get_diff_from_now_total_sec(time: datetime) -> int:
        return (time - Time.get_now()).total_seconds()

    @staticmethod
    def is_diff_in_range(time1: datetime, time2: datetime, weeks=0, days=0, hours=0, minutes=0, seconds=0) -> bool:
        if time1.tzinfo == None:
            time1 = Time.add_timezone(time1)
        if time2.tzinfo == None:
            time2 = Time.add_timezone(time2)
        from datetime import timedelta
        delta_time = timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds) 
        diff = time1 - time2 if time1 > time2 else time2 - time1
        return diff < delta_time

    @staticmethod
    def is_time_in_future_range(time: datetime, months=0, weeks=0, days=0, hours=0, minutes=0, seconds=0) -> bool:
        if time.tzinfo == None:
            time = Time.add_timezone(time)
        from dateutil.relativedelta import relativedelta
        delta_time = relativedelta(months=months, weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds) 
        return (Time.get_now() + delta_time) > time
