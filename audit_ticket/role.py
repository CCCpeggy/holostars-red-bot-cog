# discord
import discord

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
_ = Translator("TicketAuditor", __file__)
log = logging.getLogger("red.core.cogs.TicketAuditor")
log.setLevel(logging.DEBUG)

class Role():

    def __init__(self, bot, **kwargs):
        self._bot: Red = bot
        self.emoji: str = kwargs.pop("emoji", None)
        self.role_ids: str = kwargs.pop("role_ids", [])
        self.tag_channel_id: discord.TextChannel = kwargs.pop("tag_channel_id", None)
        self.can_see_channel_id_list: List[discord.TextChannel, discord.Thread] = kwargs.pop("can_see_channel_id_list", [])

    def __repr__(self) -> str:
        data = [
            f"Role",
            f"> Emoji：{self.emoji}",
            f"> 身分組 ID：{str(self.role_ids)}",
            f"> TAG 頻道 ID：{self.tag_channel_id}",
            f"> 可以看見頻道：{self.can_see_channel_id_list}",
        ]
        return "\n".join(data)
    
    def add_role(self, role_id: int):
        self.role_ids.append(role_id)
    
    def remove_role(self, role_id: int):
        self.role_ids.remove(role_id)