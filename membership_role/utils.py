# discord
import discord

# redbot
from dis import disco
from xmlrpc.client import DateTime
from redbot.core.i18n import Translator

# other
import logging
from typing import *

# get logger
_ = Translator("StarsStreams", __file__)
log = logging.getLogger("red.core.cogs.Temprole")
log.setLevel(logging.DEBUG)

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
    data = get_http_data("https://holodex.net/api/v2/videos", params)
    return len(data) > 0

async def get_http_data(url, params={}):
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
    def is_future(time: DateTime) -> bool:
        if time.tzinfo == None:
            time = Time.add_timezone(time)
        return time > Time.get_now()

    @staticmethod
    def add_time(time: datetime, months=0, weeks=0, days=0, hours=0, minutes=0, seconds=0) -> datetime:
        if time.tzinfo == None:
            time = Time.add_timezone(time)
        from dateutil.relativedelta import relativedelta
        delta_time = relativedelta(months=months, weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds) 
        return Time.get_now() + delta_time


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
        raise commands.BadArgument(argment + " not found.")