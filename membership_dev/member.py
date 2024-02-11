# discord
import discord

# redbot
from redbot.core.bot import Red

# other
import logging
import operator
from typing import *

# local
from .utils import *
from .errors import *

class DCRole:
    
    def __init__(self, bot: Red, _save_func, **kwargs):
        self._bot: Red = bot
        self.role_id: int = kwargs.pop("role_id")
        self.guild_id: int = kwargs.pop("guild_id")
    
    async def get_dc_role(self) -> discord.Role:
        try:
            guild: discord.Guild = self._bot.get_guild(self.guild_id)
            role: discord.Role = guild.get_role(self.role_id)
            return guild, role
        except Exception as e:
            log.error(f"MemberRole: {e}")
        return None

class MemberRole:
    
    def __init__(self, bot: Red, _save_func, **kwargs):
        self._bot: Red = bot
        self.name: int = kwargs.pop("name")
        self.id: int = kwargs.pop("id", to_id(self.name)) # key
        self.dc_roles: List[DCRole] = []
        for dc_role in kwargs.pop("dc_roles"):
            if isinstance(dc_role, dict):
                self.add_dc_role(**dc_role)
            else:
                self.add_dc_role(dc_role)
        self.text_channel_ids: List[Tuple[int, int]] = kwargs.pop("text_channel_ids", []) # (guild_id, channel_id)
        self.dollar: int = kwargs.pop("dollar", 0)
    
    def add_dc_role(self, dc_role: DCRole=None, **kwargs) -> DCRole:
        if dc_role is None:
            dc_role = DCRole(
                bot=self._bot,
                **kwargs
            )
        self.dc_roles.append(dc_role)
        return dc_role

class Member:
    
    def __init__(self, bot: Red, _save_func, **kwargs):
        self._bot: Red = bot
        self.names: List[str] = kwargs.pop("names")
        self.yt_channel_id: str = kwargs.pop("yt_channel_id")
        self.member_roles: Dict[int, MemberRole] = {} # id, MemberRole
        for member_role in kwargs.pop("member_roles"):
            if isinstance(member_role, dict):
                self.add_role(**member_role)
            else:
                self.add_role(member_role)
        
    @property
    def default_member_role(self):
        return self[0]
    
    def is_default_member_role(self, member_role: Union[int, str]) -> bool:
        return self.default_member_role.id == to_id(member_role)
    
    def __iter__(self):
        return iter(sorted(list(self.member_roles.values()), key=operator.attrgetter('dollar')))
    
    def __getitem__(self, member_role: Union[int, str]):
        if isinstance(member_role, int):
            member_role_id = int
        elif isinstance(member_role, str):
            member_role_id = to_id(member_role_id)
        else:
            raise TypeError("member_role must be int or str")
        found_member_role = [member_role for member_role in self.member_roles if member_role.id == member_role_id]
        if found_member_role:
            return found_member_role[0]
        return None
    
    def add_role(self, member_role: MemberRole=None, **kwargs) -> MemberRole:
        if member_role is None:
            member_role = MemberRole(
                bot=self._bot,
                **kwargs
            )
        if self[member_role.id] is not None:
            raise AlreadyExists("Member role already has this member")
        self.member_roles[member_role.id] = member_role
        return member_role
    
    def __repr__(self) -> str:
        info = {
            "YouTube 頻道": self.channel_id,
            "成員名稱": ", ".join(self.names),
            "身分組": "\n- ".join([""]+[f"{k}：{v}" for k, v in self.membership_type.items()]),
            "文字頻道": self._text_channel.mention,
        }
        return "\n".join([f"{k}：{v}" for k, v in info.items()])
