# discord
import discord
from lavalink import user_id

# redbot
from redbot.core.i18n import Translator
from redbot.core.bot import Red

# other
import logging
from typing import *

# local
from .utils import *
from .role import UserRole
from .errors import *

# get logger
_ = Translator("StarsStreams", __file__)
log = logging.getLogger("red.core.cogs.Temprole")
log.setLevel(logging.DEBUG)

class User():
    
    def __init__(self, bot, _save_func, **kwargs):
        self._bot: Red = bot
        self.id: str = kwargs.pop("id")
        self.roles: Dict[int, UserRole] = {}

        roles = kwargs.pop("roles", {})
        if roles:
            for role_id, user_role in roles.items():
                self.add_role(role=role_id, **user_role)
                pass
        self._save_func = _save_func
        self._bot.loop.create_task(_save_func())
    
    def add_role(self, role: Union[discord.Role, int, str], tmp: bool=False, **kwargs):
        role_id = to_role_id(role)
        if role_id in self.roles and not tmp:
            raise AlreadyExists
        user_role = UserRole(
            bot=self._bot,
            **kwargs
        )
        if not tmp:
            self.roles[role_id] = user_role
        return user_role
    
    def set_role(self, role: Union[discord.Role, int, str], user_role: UserRole):
        role_id = to_role_id(role)
        self.roles[role_id] = user_role
        
    def remove_role(self, role: Union[discord.Role, int, str]):
        role_id = to_role_id(role)
        user_role = self.roles.pop(role_id, None)
        
    def export(self):
        raw_data = {}
        from datetime import datetime
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            if not v:
                raw_data[k] = None
            elif k == "roles":
                raw_data[k] = ConvertToRawData.dict(v)
            elif isinstance(v, (int, str, list, dict)):
                raw_data[k] = v
            elif isinstance(v, datetime):
                raw_data[k] = Time.to_standard_time_str(v)
            else:
                raw_data[k] = v.id
        return raw_data
    
    def __repr__(self) -> str:
        info = {
            "ID": self.id,
            "身分組": "\n- ".join([""]+[f"{k}：{v}" for k, v in self.roles.items()]),
        }
        return "\n".join([f"{k}：{v}" for k, v in info.items()])