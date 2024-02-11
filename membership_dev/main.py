# discord
from dis import dis
from distutils.log import debug
import discord
from discord.utils import get

# redbot
from redbot.core.bot import Red
from redbot.core import checks, commands, Config
from redbot.core.i18n import cog_i18n, Translator

# other
import logging
from typing import *
import asyncio
import json
from io import BytesIO

# local
from .member import Member, MemberRole
from .user import User, UserRole
from .utils import *
from .errors import *

members = {}
users = {}

@cog_i18n(_)
class MembershipRoleManger(commands.Cog):

    global_defaults = {
        "users": {},
        "members": {},
    }

    guild_defaults = {
        "membership_input_channel_id": None,
        "membership_result_channel_id": None,
        "membership_command_channel_id": None,
    }

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, 20240211)
        self.config.register_global(**self.global_defaults)
        self.config.register_guild(**self.guild_defaults)
        
        # member
        self.members: Dict[str, Member] = {}
        global members
        members = self.members
        
        # user role
        self.users: Dict[int, User] = {}
        global users
        users = self.users
        
        # channel
        self.input_channel: discord.TextChannel = None
        self.command_channel: discord.TextChannel = None
        self.result_channel: discord.TextChannel = None
        
        async def initial():
            await self.bot.wait_until_ready()
            async def load_members():
                for key, value in (await self.config.members()).items():
                    # for old version merge
                    if "yt_channel_id" not in value:
                        value["yt_channel_id"] = value.pop("channel_id")
                    self.add_member(**value)
            await load_members()
            async def load_users():
                for key, value in (await self.config.users()).items():
                    # for old version merge
                    if "id" not in value:
                        value["dc_user_id"] = value.pop("id")
                    self.add_user(**value)
            await load_users()
            await self.check()
            
        self.task: asyncio.Task = self.bot.loop.create_task(initial())
        
    def cog_unload(self):
        if self.task:
            self.task.cancel()

    async def check(self):
        pass
        # while True:
        #     log.info("--------role check----------")
        #     try:
        #         remove_user_ids = []
        #         for user in self.users.values():
        #             if not check_user(user):
        #                 remove_user_ids.append(user.id)
        #         for user_id in remove_user_ids:
        #             log.info(f"check: remove user {user_id}")
        #             self.remove_user(user_id)
        #         await self.save_users()
        #     except Exception as e:
        #         log.error(e)
        #     log.info("--------role check end----------")
        #     await asyncio.sleep(3600)
        
    def add_member(self, yt_channel_id: str, **kwargs) -> Optional[Member]:
        if yt_channel_id in self.members:
            log.debug(f"add_member: {yt_channel_id} already exists")
            raise AlreadyExists
        member = Member(
            bot=self.bot,
            yt_channel_id=yt_channel_id, 
            _save_func=self.save_members,
            **kwargs
        )
        self.members[yt_channel_id] = member
        return member
    
    def add_user(self, dc_user_id: Union[discord.Member, discord.User, int, str], **kwargs) -> Optional[User]:
        dc_user_id = to_id(dc_user_id)
        if dc_user_id in self.users:
            log.debug(f"add_user: {dc_user_id} already exists")
            raise AlreadyExists
        user = User(
            bot=self.bot,
            dc_user_id=dc_user_id, 
            _save_func=self.save_users,
            **kwargs
        )
        self.users[dc_user_id] = user
        return user
    
    def remove_user(self, id: Union[discord.Member, discord.User, int, str], **kwargs) -> Optional[User]:
        id = to_user_id(id)
        if id not in self.users:
            log.debug(f"remove_user: {id} not exists")
            return
        del self.users[id]