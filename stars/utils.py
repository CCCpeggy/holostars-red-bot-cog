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

async def get_text_channel(place: Union[discord.Guild, Red], channel: Union[str, discord.TextChannel, None]) -> discord.TextChannel:
    if isinstance(channel, str):
        return place.get_channel(channel)
    return channel

def create_id():
    import uuid
    return uuid.uuid4().hex[:16]

class Youtube:
    @staticmethod
    def check_id(id: str) -> bool:
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
        elif isinstance(obj, discord.TextChannel):
            await send_place.send(f"**{name}**已設定為 {obj.mention}",
                allowed_mentions=discord.AllowedMentions.none())
        else:
            await send_place.send(f"**{name}**已設定為\n{str(obj)}")
    @staticmethod
    async def add_completed(send_place: SendPlaceType, name:str, obj=None):
        if obj == None:
            await send_place.send(f"**{name}**已新增一筆資料")
        elif isinstance(obj, discord.TextChannel):
            await send_place.send(f"**{name}**已新增一筆：{obj.mention}",
                allowed_mentions=discord.AllowedMentions.none())
        else:
            await send_place.send(f"**{name}**已新增一筆\n{str(obj)}")
    @staticmethod
    async def remove_completed(send_place: SendPlaceType, name:str, obj=None):
        if obj == None:
            await send_place.send(f"**{name}**已刪除一筆資料")
        elif isinstance(obj, discord.TextChannel):
            await send_place.send(f"**{name}**已刪除一筆：{obj.mention}",
                allowed_mentions=discord.AllowedMentions.none())
        else:
            await send_place.send(f"**{name}**已刪除一筆\n{str(obj)}")
    @staticmethod
    async def already_existed(send_place: SendPlaceType, name:str, obj=None):
        if obj == None:
            await send_place.send(f"**{name}**已經存在")
        elif isinstance(obj, discord.TextChannel):
            await send_place.send(f"**{name}**已經存在：{obj.mention}",
                allowed_mentions=discord.AllowedMentions.none())
        else:
            await send_place.send(f"**{name}**已經存在\n{str(obj)}")
    @staticmethod
    async def not_existed(send_place: SendPlaceType, name:str, obj=None):
        if obj == None:
            await send_place.send(f"**{name}**不存在")
        elif isinstance(obj, discord.TextChannel):
            await send_place.send(f"**{name}**不存在：{obj.mention}",
                allowed_mentions=discord.AllowedMentions.none())
        else:
            await send_place.send(f"**{name}**不存在\n{str(obj)}")
    @staticmethod
    async def data_error(send_place: SendPlaceType, name:str, obj=None):
        if obj == None:
            await send_place.send(f"**{name}**資料或格式錯誤")
        elif isinstance(obj, discord.TextChannel):
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
    def getChannelMention(channel, default="未設定"):
        return channel.mention if channel else '未設定'

from datetime import datetime
class Time:
    @staticmethod
    def add_timezone(time: datetime) -> datetime:
        import pytz
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
    def get_specified_timezone_str(time: datetime, timezone: str='Asia/Taipei') -> str:
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
    def is_time_in_future_range(time: datetime, months=0, weeks=0, days=0, hours=0, minutes=0, seconds=0) -> bool:
        if time.tzinfo == None:
            time = Time.add_timezone(time)
        from dateutil.relativedelta import relativedelta
        delta_time = relativedelta(months=months, weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds) 
        return (Time.get_now() + delta_time) > time

