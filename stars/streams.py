# discord
import discord

# redbot
from redbot.core import Config

# other
import os
import logging

# local
from stars.utils import *

_, log = get_logger()

from enum import Enum

class StreamStatus(Enum):
    STANDBY = 1
    START = 2
    END = 3

class Stream:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.id: str = kwargs.pop("id", create_id())
        self._saved_func = kwargs.pop("_saved_func", None)
        self.status: StreamStatus = kwargs.pop("status", None)

class StreamsManager(commands.Cog):

    global_defaults = {
        "streams": {}
    }

    guild_defaults = {
        "custom_streams": {}
    }

    def __init__(self, bot, manager: "Manager"):
        self.bot = bot
        self.manager: "Manager" = manager
        self.config = Config.get_conf(self, 12448734)
        self.config.register_global(**self.global_defaults)
        self.config.register_guild(**self.guild_defaults)
        self.streams = {}
        
    def add_stream(self, **kwargs):
        id = kwargs["id"]
        self.streams[id] = Stream(bot=bot, **kwargs)

    async def save_streams(self) -> None:
        await self.config.channels_.set(ConvertToRawData.dict(self.channels))