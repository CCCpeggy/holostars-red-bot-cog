# discord
import discord

# redbot

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