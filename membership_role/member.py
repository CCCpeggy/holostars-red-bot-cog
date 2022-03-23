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

class Member():
    
    def __init__(self, bot: Red, _save_func, **kwargs):
        self._bot: Red = bot
        self.channel_id: str = kwargs.pop("channel_id")
        self.names: List[str] = kwargs.pop("names")
        self.membership_type: Dict[str, int] = {} # type_name, role_id
        self.text_channel_id: int = kwargs.pop("text_channel_id", None)
        self._text_channel: discord.TextChannel = get_text_channel(self._bot, self.text_channel_id)
        
        membership_type = kwargs.pop("membership_type", {})
        for type_name, role in membership_type.items():
            self.add_membership_type(type_name, role)

        self.default_type_name: str = kwargs.pop("default_type_name", list(self.membership_type.keys())[0])
        
        self._save_func = _save_func
        self._bot.loop.create_task(_save_func())
        
    def add_membership_type(self, type_name: str, role: Union[discord.Role, int, str], default: bool=False) -> bool:
        role_id = to_role_id(role)
        if (type_name not in self.membership_type):
            self.membership_type[type_name] = role_id
            if default:
                self.default_type_name = type_name
            return True
        return False
    
    def __repr__(self) -> str:
        info = {
            "YouTube 頻道": self.channel_id,
            "成員名稱": ", ".join(self.names),
            "身分組": "\n- ".join([""]+[f"{k}：{v}" for k, v in self.membership_type.items()]),
            "文字頻道": self._text_channel.mention,
        }
        return "\n".join([f"{k}：{v}" for k, v in info.items()])