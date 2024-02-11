# discord
import discord

# redbot
from redbot.core.bot import Red
from redbot.core.i18n import Translator

# other
import logging
from datetime import datetime
from typing import *

# get logger
_ = Translator("StarsRoles", __file__)
log = logging.getLogger("red.core.cogs.Temprole")
log.setLevel(logging.DEBUG)

def to_id(object: Union[discord.Member, discord.User, discord.Role, discord.Guild, int, str]) -> int:
    if isinstance(object, (discord.User, discord.Member, discord.Role, discord.Guild)):
        return object.id
    elif isinstance(object, int):
        return object
    elif isinstance(object, str) and not object.isdigit():
        # 將字串編碼成數字
        return int.from_bytes(object.encode('utf-8'), 'little')
    try:
        return int(object)
    except Exception as e:
        log.error(f"轉換成 int 錯誤，原本型態: {type(object)}，內容: {object}，錯誤: {e}")

async def get_comment_info(video_id, channel_id=None, comment_id=None) -> dict:
    from .get_comment_info import get_comment_info
    return get_comment_info(video_id, channel_id=channel_id, comment_id=comment_id)

def get_text_channel(place: Union[discord.Guild, Red], channel: Union[int, str, discord.TextChannel, None]) -> discord.TextChannel:
    if isinstance(channel, int) or isinstance(channel, str):
        return place.get_channel(channel)
    return channel

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
