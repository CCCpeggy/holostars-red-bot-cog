# discord
import discord

# redbot
from redbot.core.i18n import Translator
from redbot.core.bot import Red
from redbot.core import commands

# other
import logging
from typing import *

# local
from .utils import *

# get logger
_ = Translator("StarsStreams", __file__)
log = logging.getLogger("red.core.cogs.Temprole")
log.setLevel(logging.DEBUG)

class Member(commands.Converter):
    
    def __init__(self, bot, _save_func, **kwargs):
        self._bot: str = bot
        self.channel_id: str = kwargs.pop("channel_id")
        self.names: str = kwargs.pop("names")
        self.membership_type: Dict[str, int] = {} # type_name, role_id
        
        membership_type = kwargs.pop("membership_type", {})
        for type_name, role in membership_type.items():
            self.add_membership_type(type_name, role)
        
        self._save_func = _save_func
        self._bot.loop.create_task(_save_func())
        
    def add_membership_type(self, type_name: str, role: Union[discord.Role, int, str]) -> bool:
        role_id = to_role_id(role)
        if (type_name not in self.membership_type):
            self.membership_type[type_name] = role_id
            return True
        return False
    
    def __repr__(self) -> str:
        return str(ConvertToRawData.export_class(self))