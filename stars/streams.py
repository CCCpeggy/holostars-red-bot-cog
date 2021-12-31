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

class Stream:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.id: name = kwargs.pop("id", create_id())
        self._saved_func = kwargs.pop("_saved_func", None)

class StreamsManager:

    def __init__(self, bot, manager: "Manager"):
        self.bot = bot
        self.config = Config.get_conf(self, 12448734)
        self.manager = manager
        self.streams = {}