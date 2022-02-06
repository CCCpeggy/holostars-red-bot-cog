
# redbot
from datetime import datetime
from distutils.log import debug
from operator import imod
from redbot.core.i18n import Translator
from redbot.core.bot import Red

# other
import logging
from typing import *
from .utils import *

# get logger
_ = Translator("StarsStreams", __file__)
log = logging.getLogger("red.core.cogs.Temprole")
log.setLevel(logging.DEBUG)

class UserRole():

    def __init__(self, bot, **kwargs):
        self._bot: Red = bot
        self.channel_id: str = kwargs.pop("channel_id", None)
        self.video_id: str = kwargs.pop("video_id", None)
        self.comment_id: str = kwargs.pop("comment_id", None)
        self.end_time: datetime = Time.to_datetime(kwargs.pop("end_time"))
        self.is_valid: bool = kwargs.pop("is_valid", False)
    
    async def check(self) -> bool:
        if not self.is_valid:
            return False
        if Time.is_future(Time.add_time(self.end_time, hours=16)):
            return True
        if self.channel_id == None and self.video_id == None:
            return False
        data = await get_comment_info(self.video_id, channel_id=self.channel_id, comment_id=self.comment_id)
        if data == None:
            data = await get_comment_info(self.video_id, channel_id=self.channel_id)
            if data == None:
                return None
        self.comment_id = data["comment_id"]
        self.end_time = Time.add_time(self.end_time, months=1)
        return True

    def valid(self):
        self.is_valid = True

    def __repr__(self) -> str:
        return str(ConvertToRawData.export_class(self))