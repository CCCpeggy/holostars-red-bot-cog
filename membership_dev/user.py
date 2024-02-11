# discord
import discord

# redbot
from redbot.core.bot import Red
from datetime import datetime

# local
from utils import *
from errors import *

class UserRole:
    def __init__(self, bot, **kwargs) -> None:
        self._bot: Red = bot
        self.channel_id: str = kwargs.pop("channel_id", None)
        self.video_id: str = kwargs.pop("video_id", None)
        self.comment_id: str = kwargs.pop("comment_id", None)
        self.end_time: datetime = Time.to_datetime(kwargs.pop("end_time"))
        self.is_valid: bool = kwargs.pop("is_valid", False)
        self.member_role_id: int = kwargs.pop("member_role_id")
        
    @property
    def id(self):
        return self.member_role_id

    def is_expired(self) -> bool:
        return not Time.is_future(Time.add_time(self.end_time, hours=16))
    
    async def check(self) -> bool:
        if not self.is_valid:
            return False
        if not self.is_expired():
            return True
        if self.channel_id == None or self.video_id == None:
            return False
        data = await get_comment_info(self.video_id, channel_id=self.channel_id, comment_id=self.comment_id)
        if data == None:
            data = await get_comment_info(self.video_id, channel_id=self.channel_id)
            if data == None:
                return None
        self.comment_id = data["comment_id"]
        self.end_time = Time.add_time(self.end_time, months=1)
        return True

    def __repr__(self) -> str:
        return str(ConvertToRawData.export_class(self))

class User:
    def __init__(self, bot, **kwargs) -> None:
        self._bot: Red = bot
        self.dc_user_id: int = to_id(kwargs.pop("dc_user_id"))
        self.user_roles: Dict[int, UserRole] = {}
        for user_role in kwargs.pop("user_roles"):
            if isinstance(user_role, dict):
                self.add_role(**user_role)
            else:
                self.add_role(user_role)

    @property
    def id(self):
        return self.dc_user_id
    
    def __getitem__(self, member_role):
        if isinstance(member_role, int):
            member_role_id = int
        elif isinstance(member_role, str):
            member_role_id = to_id(member_role_id)
        else:
            raise TypeError("member_role must be int or str")
        found_user_role = [user_role for user_role in self.user_roles if user_role.member_role_id == member_role_id]
        if found_user_role:
            return found_user_role[0]
        return None
    
    def add_role(self, user_role: UserRole=None, **kwargs) -> UserRole:
        if user_role is None:
            user_role = UserRole(
                bot=self._bot,
                **kwargs
            )
        if self[user_role.member_role_id] is not None:
            raise AlreadyExists("User role already has this user")
        self.user_roles[user_role.member_role_id] = user_role
        return user_role
    
    def set_role(self, user_role: UserRole=None, **kwargs) -> UserRole:
        if user_role is None:
            user_role = UserRole(
                bot=self._bot,
                **kwargs
            )
        if self[user_role.member_role_id] is not None:
            del self[user_role.member_role_id]
        self.user_roles[user_role.member_role_id] = user_role
        return user_role
       
    def remove_role(self, member_role: Union[int, str]) -> Optional[UserRole]:
        member_role_id = to_id(member_role)
        user_role = self.user_roles.pop(member_role_id, None)
        return user_role
        
    def export(self):
        raw_data = {}
        from datetime import datetime
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            if not v:
                raw_data[k] = None
            elif k == "user_roles":
                raw_data[k] = ConvertToRawData.dict(v)
            elif isinstance(v, (int, str, list, dict)):
                raw_data[k] = v
            elif isinstance(v, datetime):
                raw_data[k] = Time.to_standard_time_str(v)
            else:
                raw_data[k] = v.id
        return raw_data
    
    def get_member_roles(self, member: "Member") -> List[UserRole]:
        return [user_role for user_role in self.user_roles if user_role.member_role_id in member.member_roles]
    
    def __repr__(self) -> str:
        info = {
            "ID": self.id,
            "身分組": "\n- ".join([""]+[f"{k}：{v}" for k, v in self.user_roles.items()]),
        }
        return "\n".join([f"{k}：{v}" for k, v in info.items()])
