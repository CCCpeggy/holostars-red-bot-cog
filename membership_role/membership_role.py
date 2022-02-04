# discord
import discord

# redbot
from redbot.core.bot import Red
from redbot.core import checks, commands, Config
from redbot.core.i18n import cog_i18n, Translator

# other
import logging
from typing import *

from stars.utils import MemberConverter

# local
from .member import Member
from .user import User
from .role import UserRole
from .utils import *

# get logger
_ = Translator("StarsStreams", __file__)
log = logging.getLogger("red.core.cogs.Temprole")
log.setLevel(logging.DEBUG)

members = {}
users = {}

@cog_i18n(_)
class MembershipRoleManger(commands.Cog):

    global_defaults = {
        "members": {}, # channel_id, member
        "users": {} # user_id, user
    }

    guild_defaults = {
    }

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, 55887792)
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
        
        async def initial():
            async def load_members():
                for key, value in (await self.config.members()).items():
                    self.add_member(**value)
            await load_members()
            log.debug(self.members)
            async def load_users():
                for key, value in (await self.config.users()).items():
                    self.add_user(**value)
            await load_users()
            log.debug(self.users)


        self.bot.loop.create_task(initial())
        
    async def check(self):
        pass
    
    def add_member(self, channel_id: str, **kwargs) -> Optional[Member]:
        try:
            if channel_id in self.members:
                log.info(f"{channel_id} already exists")
                raise Exception
            member = Member(
                bot=self.bot,
                channel_id=channel_id, 
                _save_func=self.save_members,
                **kwargs
            )
            self.members[channel_id] = member
            return member
        except:
            return None
    
    def remove_member(self, channel_id: str, **kwargs) -> None:
        try:
            if channel_id not in self.members:
                log.info(f"{channel_id} is not exists")
                raise Exception
            del self.member[channel_id]
        except:
            return
    
    async def save_members(self):
        await self.config.members.set(ConvertToRawData.dict(self.members))
   
    def add_user(self, id: Union[discord.Member, discord.User, int, str], **kwargs) -> Optional[User]:
    # try:
        id = to_user_id(id)
        log.debug(id)
        if id in self.users:
            log.info(f"{id} already exists")
            # raise Exception
        user = User(
            bot=self.bot,
            id=id, 
            _save_func=self.save_users,
            **kwargs
        )
        self.users[id] = user
        return user
    # except:
    #     return None
    
    def add_user_role(self, id: Union[discord.Member, discord.User, int, str], member: Member, end_time: Union[str, datetime], type_name: str, **kwargs) -> Optional[User]:
        # try:
        id = to_user_id(id)
        log.debug(id)
        user = self.users.get(id, None)
        if not user:
            log.info(f"{id} not exists")
            # raise Exception
        role = member.membership_type.get(type_name, None)
        if not role:
            log.info(f"{id} not exists")
            # raise Exception
        user.add_role(role, end_time=end_time)
        return user
    # except:
    #     return None
    
    
    async def save_users(self):
        await self.config.users.set(ConvertToRawData.dict(self.users))
    
    @commands.group(name="role")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def role_group(self, ctx: commands.Context):
        pass
    
    @role_group.group(name="member")
    async def member_group(self, ctx: commands.Context):
        pass

    @member_group.command(name="add")
    async def _add_member(self, ctx: commands.Context, channel_id: str, names: str):
        names = names.lower().split(",")
        try:
            if len(names) == 0:
                raise Exception
            member = self.add_member(
                channel_id=channel_id,
                names=names
            )
            log.debug(member)
            if member == None:
                raise Exception
            await self.save_members()
            await ctx.send(f"successful: {member}")
        except:
            await ctx.send("failed")
            
    
    @commands.group(name="member_type")
    async def member_type_group(self, ctx: commands.Context):
        pass

    @member_type_group.command(name="add")
    async def add_membership_type(self, ctx: commands.Context, member: MemberConverter, type_name: str, role: discord.Role):
        if member.add_membership_type(type_name, role):
            await self.save_members()
            await ctx.send(f"add member type: {member}")
        else:
            await ctx.send(f"already exist: {type_name}")
        
    @role_group.command(name="test")
    async def test(self, ctx: commands.Context):
        log.debug("----------------start------------------")
        # add member
        await self._add_member(ctx, "UCNVEsYbiZjH5QLmGeSgTSzg", "astel,アステル")
        from discord. utils import get
        member = await MemberConverter.convert(_, ctx, "astel")
        await self.add_membership_type(ctx, member, "test", get(ctx.guild. roles, id=879027799204188190))
        
        # add user
        self.add_user(ctx.author)
        self.add_user_role(ctx.author, member, "20220206T00:00:00", "test")
        await self.save_users()
        
        # add role
        
        # check
        log.debug("----------------end------------------")
        
        