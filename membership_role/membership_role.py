# discord
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

# local
from .member import Member
from .user import User
from .role import UserRole
from .utils import *
from .errors import *

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
        "users": {}, # user_id, user
        
        "membership_input_channel_id": 864755730677497876,
        "membership_result_channel_id": 864755730677497876,
        "membership_command_channel_id": 864755730677497876,
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
        
        # channel
        self.input_channel: discord.TextChannel = None
        self.command_channel: discord.TextChannel = None
        self.result_channel: discord.TextChannel = None
        
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
        
            # channel
            input_channel_id = await self.config.membership_input_channel_id()
            command_channel_id = await self.config.membership_command_channel_id()
            result_channel_id = await self.config.membership_result_channel_id()
            self.input_channel = get_text_channel(self.bot, input_channel_id)
            self.command_channel = get_text_channel(self.bot, command_channel_id)
            self.result_channel = get_text_channel(self.bot, result_channel_id)
            

        self.bot.loop.create_task(initial())
        
    async def check(self):
        pass
    
    def add_member(self, channel_id: str, **kwargs) -> Optional[Member]:
        # try:
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
        # except:
        #     return None
    
    def remove_member(self, channel_id: str, **kwargs) -> None:
        # try:
        if channel_id not in self.members:
            log.info(f"{channel_id} is not exists")
            raise Exception
        del self.members[channel_id]
        # except:
        #     return
    
    async def save_members(self):
        await self.config.members.set(ConvertToRawData.dict(self.members))
   
    def add_user(self, id: Union[discord.Member, discord.User, int, str], **kwargs) -> Optional[User]:
    # try:
        id = to_user_id(id)
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
    
    def remove_user(self, id: Union[discord.Member, discord.User, int, str], **kwargs) -> Optional[User]:
        id = to_user_id(id)
        if id not in self.users:
            log.info(f"{id} not exists")
            return
        del self.users[id]
    
    def add_user_role(self, id: Union[discord.Member, discord.User, int, str], member: Member, end_time: Union[str, datetime], type_name: str, **kwargs) -> Optional[User]:
        id = to_user_id(id)
        user = self.users.get(id, None)
        if not user:
            log.info(f"{id} not exists")
            return
        role = member.membership_type.get(type_name, None)
        if not role:
            log.info(f"{type_name} not exists")
            return
        return user.add_role(role, end_time=end_time, **kwargs)
    
    async def save_users(self):
        await self.config.users.set(ConvertToRawData.dict(self.users))
    
    def remove_user_role(self, user_id: Union[discord.Member, discord.User, int, str], role_id: Union[discord.Role, int, str]) -> Optional[User]:
        user_id = to_user_id(user_id)
        user = self.users.get(user_id, None)
        if not user:
            log.info(f"{user_id} not exists")
            return
        user.remove_role(role_id)
        if len(user.roles) == 0:
            self.remove_user(user_id)
    
    @commands.group(name="role")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def role_group(self, ctx: commands.Context):
        pass
    
    @role_group.group(name="member")
    async def member_group(self, ctx: commands.Context):
        pass

    @member_group.command(name="add")
    async def _add_member(self, ctx: commands.Context, channel_id: str, names: str, text_channel: discord.TextChannel):
        names = names.lower().split(",")
        try:
            if len(names) == 0:
                raise Exception
            member = self.add_member(
                channel_id=channel_id,
                names=names,
                text_channel_id=text_channel.id
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
        from discord.utils import get
        dc_role = get(ctx.guild.roles, id=879027799204188190)
        # add member
        self.remove_member("UCNVEsYbiZjH5QLmGeSgTSzg")
        await self._add_member(ctx, "UCNVEsYbiZjH5QLmGeSgTSzg", "astel,アステル", self.input_channel)
        member: Member = await MemberConverter.convert(_, ctx, "astel")
        await self.add_membership_type(ctx, member, "test", dc_role)
        
        # add user
        user = self.add_user(ctx.author)
        user_role: UserRole = self.add_user_role(
            ctx.author, 
            member, 
            "20220206T00:00:00", 
            "test",
            video_id="RzIWjDoBH1E",
            channel_id="UC6wTWzIJiKoKvtoPdbGE07w"
        )
        
        data = await user_role.first_check()
        if not data:
            self.remove_user_role(ctx.author, dc_role)
            await self.save_users()
            await ctx.send("invalid")
            return
        else:
            log.debug(data)
            await self.save_users()
            # add role
            if await add_bool_reaction(self.bot, ctx.message):
                await ctx.send("valid")
            else:
                self.remove_user_role(ctx.author, dc_role)
                await ctx.send("invalid")
            await self.save_users()
            
            # check
            log.debug("----------------end------------------")
            
    
    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, message: discord.Message):
        ctx = await self.bot.get_context(message)
        if not is_specify_text_channel(ctx, text_channel_id=self.input_channel.id):
            return
        if is_bot(ctx):
            return
        await self.audit_membership(message)

    async def audit_membership(self, message):
        error_name = None
        handler_msg = "此為機器人自動偵測。"
        err_msg = \
"""請重新檢查**__YT、頻道、日期、截圖__**後重新傳送審核資料。
有任何疑問請至 <#863343338933059594>。
{}"""

        color=0xff0000,
        title=_("❌會員頻道權限審核未通過")
        try:
            info = parse_audit_str(message.content)
            print(info)
            if not Time.is_future(info["date"]):
                raise PassDate
            if not Time.is_time_in_future_range(info["date"], months=1):
                raise FutureDate
            
            member: Member = info["member"]
            user = self.add_user(message.author)
            type_name = "test"
            user_role: UserRole = self.add_user_role(
                message.author, 
                member,
                info["date"], 
                type_name,
                video_id=info["video_id"],
                channel_id=info["channel_id"]
            )
            log.debug(user_role)
            role_id = member.membership_type.get(type_name, None)
            role = get(message.guild.roles, id=role_id)
            
            if not (await user_role.first_check()):
                raise ValidFailure

            mod_check_valid, mod_user = await add_bool_reaction(self.bot, message)
            
            if not mod_check_valid:
                raise ModRefused
            
            if mod_check_valid:
                user_role.valid()
                # role = get(message.guild.roles, id=info["role"])
                description="\n".join([
                    f"增加身分組：{role.mention}",
                    f"請確認看得見會員頻道：{member._text_channel.mention}",
                    f"處理人：{mod_user.mention}"])
                embed=discord.Embed(
                    color=0x77b255,
                    title=_("✅會員頻道權限審核通過"),
                    description=description
                )
                await self.result_channel.send(
                    content=f"{message.author.mention}",
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions(roles=True)
                )
                await self.save_users()
                # TODO: add role
                return
        except ValidFailure:
            error_name = "#### TODO" 
        except WrongDateFormat:
            error_name = "日期格式錯誤"
        except WrongChannelName:
            error_name = "頻道名稱錯誤"
        except NoDate:
            error_name = "沒有提供日期"
        except NoChannelName:
            error_name = "沒有提供頻道名稱"
        except FutureDate:
            error_name = "提供的日期超過一個月，請提供圖片上的下一個帳單日期"
        except PassDate:
            error_name = "此日期為過去日期，請提供圖片上的下一個帳單日期"
        except ModRefused:
            handler_msg = f"處理人：{mod_user.mention}"
            pass
        except ReactionTimeout:
            # error_name = "管理員未在一天內審核"
            log.info(f"未審核：{message.id}, {message.content}")
            return
        except ServerError:
            error_name = "伺服器錯誤"
            embed = discord.Embed(
                color=0x77b255,
                title=_("伺服器錯誤"),
                description="""伺服器錯誤，請稍後一下""",
            )
            await self.result_channel.send(
                content=f"{message.author.mention}",
                embed=embed,
                allowed_mentions=discord.AllowedMentions(roles=True)
            )
            return
        
        self.remove_user_role(message.author, role)
        await self.save_users()
        err_msg = err_msg.format(handler_msg)
        if error_name:
            err_msg = f"**{error_name}**，{err_msg}"
        embed = discord.Embed(
            color=0xff0000,
            title=_("❌會員頻道權限審核未通過"),
            description= err_msg,
        )
        await self.result_channel.send(
            content=f"{message.author.mention}",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True)
        )