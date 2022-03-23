# discord
import discord

# redbot
from redbot.core.bot import Red
from redbot.core.i18n import Translator

# other
import logging
from typing import *
from .errors import *

# get logger
_ = Translator("StarsStreams", __file__)
log = logging.getLogger("red.core.cogs.Temprole")
log.setLevel(logging.DEBUG)

def get_text_channel(place: Union[discord.Guild, Red], channel: Union[int, str, discord.TextChannel, None]) -> discord.TextChannel:
    if isinstance(channel, int) or isinstance(channel, str):
        return place.get_channel(channel)
    return channel

def to_user_id(user: Union[discord.Member, discord.User, int, str]) -> int:
    if isinstance(user, (discord.User, discord.Member)):
        return user.id
    elif isinstance(user, str):
        return str(user)
    return user

def to_role_id(role: Union[discord.Role, int, str]) -> int:
    if isinstance(role, discord.Role):
        return role.id
    elif isinstance(role, str):
        return str(role)
    return role

class ConvertToRawData:
    @staticmethod
    def export_class(data):
        export_func = getattr(data, "export", None)
        if callable(export_func):
            return data.export()
        else:
            from datetime import datetime
            raw_data = {}
            for k, v in data.__dict__.items():
                if k.startswith("_"):
                    continue
                if not v:
                    raw_data[k] = None
                elif isinstance(v, (int, str, list, dict)):
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

def replace_redundant_char(ori_str):
    return ori_str.replace(" ", "")

def convert_to_half(ori_str):
    new_str = ""
    for uchar in ori_str:
        inside_code=ord(uchar)
        if inside_code==0x3000:
            new_str += " "
        elif inside_code > 65281 and inside_code < 65374 :
            new_str += chr(inside_code - 0xfee0)
        else:
            new_str += uchar
    return new_str

async def get_comment_info(video_id, channel_id=None, comment_id=None) -> dict:
    from .get_comment_info import get_comment_info
    return get_comment_info(video_id, channel_id=channel_id, comment_id=comment_id)

async def check_video_owner(channel_id: str, video_id: str) -> bool:
    params = {
        "channel_id": channel_id,
        "id": video_id
    }
    log.debug(params)
    data = await get_http_data("https://holodex.net/api/v2/videos", params)
    log.debug(data)
    return data and len(data) > 0

async def get_http_data(url, params={}):
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as r:
            data = await r.json()
            try:
                check_api_errors(data)
            except Exception as e:
                log.error(e)
            else:
                return data
    return None

def check_api_errors(data: dict):
    from .errors import APIError
    if "error" in data:
        error_code = data["error"]["code"]
        raise APIError(error_code, data)

from datetime import datetime
class Time:

    @staticmethod
    def add_timezone(time: datetime, zone: str=None) -> datetime:
        import pytz
        if zone:
            return pytz.timezone(zone).localize(time)
        return pytz.utc.localize(time)
    
    @staticmethod
    def get_now():
        from datetime import timezone
        return datetime.now(timezone.utc)

    @staticmethod
    def to_datetime(time: Union[str, datetime, None]) -> Optional[datetime]:
        if isinstance(time, datetime):
            return time
        elif isinstance(time, str):
            from dateutil.parser import parse as parse_time
            try:
                time = parse_time(time)
                if time.tzinfo == None:
                    time = Time.add_timezone(time)
                return time
            except:
                pass
        return None

    @staticmethod
    def to_standard_time_str(time: datetime) -> str:
        return time.isoformat()

    @staticmethod
    def is_future(time: datetime) -> bool:
        if time.tzinfo == None:
            time = Time.add_timezone(time)
        return time > Time.get_now()

    @staticmethod
    def add_time(time: datetime, months=0, weeks=0, days=0, hours=0, minutes=0, seconds=0) -> datetime:
        if time.tzinfo == None:
            time = Time.add_timezone(time)
        from dateutil.relativedelta import relativedelta
        delta_time = relativedelta(months=months, weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds) 
        return time + delta_time

    @staticmethod
    def is_time_in_future_range(time: datetime, months=0, weeks=0, days=0, hours=0, minutes=0, seconds=0) -> bool:
        if time.tzinfo == None:
            time = Time.add_timezone(time)
        from dateutil.relativedelta import relativedelta
        delta_time = relativedelta(months=months, weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds) 
        return (Time.get_now() + delta_time) > time

from redbot.core import commands
class UserConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argment: str) -> "User":
        from .membership_role import users
        try:
            id = int(argment)
            if id in users:
                return users[id]
        except:
            pass
        raise commands.BadArgument(argment + " not found.")
    
class MemberConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argment: str) -> "Member":
        from .membership_role import members
        for member in members.values():
            if argment in member.names:
                return member
        raise commands.BadArgument(f"不存在會員名稱 {argment}")
    
async def add_reaction(message: discord.Message, emojis: List[str]):
    import contextlib
    with contextlib.suppress(discord.NotFound):
        for emoji in emojis:
            await message.add_reaction(emoji)

async def add_bool_reaction(bot, message: discord.Message) -> Tuple[bool, discord.Member]:
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
                break
    except asyncio.TimeoutError:
        await message.remove_reaction(done_emoji)
        raise ReactionTimeout

    if task is not None:
        task.cancel()
    if r.emoji == done_emoji:
        await message.remove_reaction(cancel_emoji, bot.user)
        return True, u
    await message.remove_reaction(done_emoji, bot.user)
    return False, u

def getEmoji(guild_emojis, ori_emoji):
    # check guild
    for e in guild_emojis:
        if str(e.id) in ori_emoji and e.name in ori_emoji:
            return e
    # check emoji dictionary
    import emoji
    if ori_emoji in emoji.UNICODE_EMOJI['en']:
        return ori_emoji
    return None

async def add_waiting_reaction(bot, message: discord.Message, emojis: List[str]):
    import asyncio
    task = asyncio.create_task(add_reaction(message, emojis))
    emojis = [getEmoji(message.guild.emojis, e) for e in emojis]
    try:
        while True:
            from redbot.core.utils.predicates import ReactionPredicate
            from redbot.core.utils.mod import is_mod_or_superior
            (r, u) = await bot.wait_for(
                "reaction_add",
                check=ReactionPredicate.with_emojis(emojis, message),
                timeout=3600  # 1 hour
            )
            if await is_mod_or_superior(bot, u):
                break
    except asyncio.TimeoutError:
        await message.clear_reactions()
        raise ReactionTimeout

    if task is not None:
        task.cancel()
    
    await message.clear_reactions()
    await add_reaction(message, [r])
    return emojis.index(r.emoji)

def is_specify_text_channel(ctx: commands.Context, text_channel_id: discord.TextChannel):
    return ctx.channel.id == text_channel_id

def is_bot(ctx: commands.Context):
    return ctx.author.bot

def get_member_by_name(name: str):
    from .membership_role import members
    for member in members.values():
        for n in member.names:
            if n in name:
                return member
    return None

def get_youtube_channel_id(text: str):
    import re
    result = re.search(r"UC[-_0-9A-Za-z]{21}[AQgw]", text)
    if result:
        return result.group()
    return None

def get_youtube_video_id(text: str):
    import re
    result = re.search(r"(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)(?P<video_id>[\w\-_]+)\&?", text)
    if result:
        return result.groupdict()["video_id"]
    result = re.search(r"[\w\-_]+", text)
    if result:
        return result.group()
    return None

def parse_audit_str(content: str):
    date = None
    member = None
    channel_id = None
    video_id = None
    content = convert_to_half(content)
    content = replace_redundant_char(content)
    for s in content.split('\n'):
        tmp = s.split(':')
        if len(tmp) != 2:
            continue
        key, value = tmp
        if key == "頻道":
            value = value.lower()
            member = get_member_by_name(value)
            if not member:
                raise WrongChannelName
        elif key == "日期":
            date = Time.to_datetime(value)
            if not date:
                raise WrongDateFormat
        elif key == "YT":
            channel_id = get_youtube_channel_id(value)
        elif key == "影片":
            video_id = get_youtube_video_id(value)
    if not date:
        raise NoDate
    if not member:
        raise NoChannelName
    return {
        "date": date,
        "member": member,
        "channel_id": channel_id,
        "video_id": video_id,
    }
    

