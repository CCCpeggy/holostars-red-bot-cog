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

    # region check
    async def check(self):
        while True:
            log.info("--------role check----------")
            try:
                self.update_all_user_role_is_valid()
                self.update_all_dc_role()
                self.update_all_user_role_data()
                self.save_users()
            except Exception as e:
                log.error(e)
            log.info("--------role check end----------")
            await asyncio.sleep(3600)
    
    async def update_all_user_role_is_valid(self):
        for user in self.users.values():
            for user_role in user.user_roles.values():
                user_role.is_valid = await user_role.check()
                # 降級為初始的身分組
                member = self.get_member_by_role(user_role.member_role_id)
                user_role.member_role_id = member.default_member_role.id
    
    def update_all_dc_role(self):
        for user in self.users.values():
            self.update_dc_role(user)
    
    def update_all_user_role_data(self):
        for user in self.users.copy().values():
            for user_role in user.user_roles.copy().values():
                if self.check_dc_role_right(user, user_role.member_role_id, user_role.is_valid):
                    if not user_role.is_valid:
                        user.user_roles.remove(user_role.id)
                else:
                    if user_role.is_valid:
                       log.warning(f"無正確{'新增' if user_role.is_valid else '刪除'}身分組至DC，user({user.dc_user_id}), member_role({user_role.member_role_id})") 
            if len(user.user_roles):
                self.remove_user(user.id)
    # endregion

    # region dc
    async def update_dc_role(self, user: Union[UserRole, int, str]):
        user_id = to_id(user)
        user = self.users[user_id]
        
        for user_role in user.user_roles.values():
            member_roles = self.get_member_by_role(user_role.member_role_id)
            for member_role in member_roles:
                # user 有的 member role
                if user_role.member_role_id == member_role.id and user_role.is_valid:
                    # 如果 DC 沒有這個身分組，就給他
                    self.add_dc_role(user, member_role)
                # user 沒有的 member role
                else:
                    # 如果 DC 有這個身分組，就移除他
                    self.remove_dc_role(user, member_role)
            
    async def add_dc_role(self, user: Union[UserRole, int, str], member_role: Union[MemberRole, int, str]):
        user = self.users[to_id(user)]
        member_role = self.members[to_id(member_role)]
        
        for dc_role in member_role.dc_roles:
            guild, role = await dc_role.get_dc_role()
        
            dc_user: discord.Member = guild.get_member(user.dc_user_id)
            if role not in dc_user.roles:
                await dc_user.add_roles(role, reason="MembershipRoleManger.add_dc_role")
            
    async def remove_dc_role(self, user: Union[UserRole, int, str], member_role: Union[MemberRole, int, str]):
        user = self.users[to_id(user)]
        member_role = self.members[to_id(member_role)]
        
        for dc_role in member_role.dc_roles:
            guild, role = await dc_role.get_dc_role()
        
            dc_user: discord.Member = guild.get_member(user.dc_user_id)
            if role in dc_user.roles:
                await dc_user.remove_roles(role, reason="MembershipRoleManger.remove_dc_role")
    
    async def check_dc_role_right(self, user: Union[UserRole, int, str], member_role: Union[MemberRole, int, str], is_valid: bool) -> bool:
        user = self.users[to_id(user)]
        member_role = self.members[to_id(member_role)]
        
        for dc_role in member_role.dc_roles:
            guild, role = await dc_role.get_dc_role()
        
            dc_user: discord.Member = guild.get_member(user.dc_user_id)
            return role in dc_user.roles == is_valid
    # endregion

    # region member
    def add_member(self, yt_channel_id: str, **kwargs) -> Optional[Member]:
        if yt_channel_id not in self.members:
            member = Member(
                bot=self.bot,
                yt_channel_id=yt_channel_id, 
                _save_func=self.save_members,
                **kwargs
            )
            self.members[yt_channel_id] = member
        return self.members[yt_channel_id]
    
    def get_member_by_role(self, member_role: Union[MemberRole, int]) -> Optional[Member]:
        member_role_id = to_id(member_role)
        for member in self.members.values():
            if member_role_id in member.member_roles:
                return member
        return None
    
    def get_member_by_name(self, name: str):
        for member in self.members.values():
            if name in self.member.names:
                return member
        return None
    # endregion
    
    # region user
    def add_user(self, dc_user_id: Union[discord.Member, discord.User, int, str], **kwargs) -> Optional[User]:
        dc_user_id = to_id(dc_user_id)
        if dc_user_id not in self.users:
            user = User(
                bot=self.bot,
                dc_user_id=dc_user_id, 
                _save_func=self.save_users,
                **kwargs
            )
            self.users[dc_user_id] = user
        return self.users[dc_user_id]
    
    def remove_user(self, id: Union[discord.Member, discord.User, int, str], **kwargs) -> None:
        id = to_id(id)
        if id not in self.users:
            log.debug(f"remove_user: {id} not exists")
            return
        del self.users[id]
    
    def add_user_role(self, _user: Union[discord.Member, discord.User, int, str], 
                      member: Member, _member_role: Union[str, int, MemberRole], 
                      **kwargs) -> Optional[User]:
        user_id = to_id(_user)
        if user_id not in user:
            log.debug(f"add_user_role: user({_user}) not exists")
            raise NotExists
        user = self.users[user_id]
        member_role = member[to_id(_member_role)]
        if member_role is None:
            log.debug(f"add_user_role: member_role_name({_member_role.name}) not exists")
            raise NotExists
        user_role = user.add_role(member_role, **kwargs)
        return user_role
    
    def set_user_role(self, _user: Union[discord.Member, discord.User, int, str], 
                      member: Member, _member_role: Union[str, int, MemberRole], 
                      **kwargs) -> Optional[User]:
        user_id = to_id(_user)
        if user_id not in user:
            log.debug(f"set_user_role: user({_user}) not exists")
            raise NotExists
        user = self.users[user_id]
        member_role = member[to_id(_member_role)]
        if member_role is None:
            log.debug(f"set_user_role: member_role_name({_member_role.name}) not exists")
            raise NotExists
        member_roles = user.get_member_roles(member)
        for _member_role in member_roles:
            if _member_role.id != member_role.id:
                user[_member_role.id].valid = False
        user_role = user.set_role(member_role, **kwargs)
        return user_role

    def remove_user_role(self, user: Union[discord.Member, discord.User, int, str], member_role: Union[int, str]) -> Optional[User]:
        user_id = to_id(user)
        if user_id not in user:
            log.debug(f"remove_user_role: user({user}) not exists")
            raise NotExists
        user = self.users[user_id]
        user.remove_role(member_role)
        if len(user.user_roles) == 0:
            self.remove_user(user_id)
    
    async def save_users(self):
        await self.config.users.set(ConvertToRawData.dict(self.users))
    # endregion
    
    # region audit
    async def audit_membership(self, message, send_result=True):
        error_name = None
        handler_msg = "此為機器人自動偵測。"
        err_msg="\n".join([
            "請重新檢查**__YT、頻道、日期、截圖__**後重新傳送審核資料。",
            "有任何疑問請至 <#863343338933059594>",
            "處理人：{}"])

        color=0xff0000,
        title=_("❌會員頻道權限審核未通過")
        try:
            info = parse_audit_str(message.content)
            print(info)
            if not Time.is_future(Time.add_time(info["date"], hours=16)):
                raise PassDate
            if not Time.is_time_in_future_range(info["date"], months=1, hours=12):
                raise FutureDate
            
            member: Member = info["member"]
            
            embed=None
            comment_data=None
            if info["video_id"]:
                # valid channel
                if not await check_video_owner(member.channel_id, info["video_id"]):
                    raise VideoOwnChannelNotFit
                
                # valid comment
                comment_data = await get_comment_info(info["video_id"], channel_id=info["channel_id"])
                if not comment_data:
                    raise CommentFailure
                
                # make embed
                embed = discord.Embed(
                    color=0xFF0000,
                    title=f"https://www.youtube.com/watch?v={info['video_id']}&lc={comment_data['comment_id']}",
                    description=comment_data["text"]
                )
                embed.set_author(
                    name=comment_data["author"], 
                    url=f"https://www.youtube.com/channel/{info['channel_id']}", 
                    icon_url=comment_data["photo"]
                )
                

            # mod check
            msg = []
            msg.append(f"ID: {message.author.mention}")
            if info["channel_id"]:
                msg.append(f"頻道連結: <https://www.youtube.com/channel/{info['channel_id']}>")
            if info["video_id"]:
                msg.append(f"影片連結: <https://youtu.be/{info['video_id']}>")
            msg.append(message.content.replace("https", "~~https~~"))
            mod_check_msg = await self.command_channel.send("\n".join(msg), embed=embed,
                allowed_mentions=discord.AllowedMentions(users=False))
            if not mod_check_msg:
                raise ServerError
            
            mod_check_valid, mod_user = await add_bool_reaction(self.bot, mod_check_msg)
            if not mod_check_valid:
                raise ModRefused
            
            # get type name
            member_roles = list(member)
            if len(member_roles) == 0:
                raise ServerError
            elif len(member_roles) == 1:
                member_role = member_roles[0]
            else:
                msg = []
                emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
                for i in range(len(member_roles)):
                    msg.append(f"{emoji[i]}: {member_roles[i].name}")
                msg = "\n".join(msg)
                msg = await mod_check_msg.reply(msg)
                index = await add_waiting_reaction(self.bot, msg, emoji[:len(member_roles)])
                member_role = member_roles[index]
                
            user = self.add_user(message.author)

            # TODO: 檢查是否有同會員成員不同身分組
            user_role: UserRole = UserRole(
                channel_id=info["channel_id"],
                video_id=info["video_id"],
                comment_id=comment_data["comment_id"] if comment_data else None
                end_time=info["date"],
                member_role_id=member_role.id,
                is_valid = True
            )
            
            dc_roles = [dc_role.get_dc_role()[1] for dc_role in member_role.dc_roles]
            description="\n".join([
                f"增加身分組：{", ".join([dc_role.mention for dc_role in dc_roles])}",
                # f"請確認看得見會員頻道：{member._text_channel.mention}",
                f"處理人：{mod_user.mention}"])
            embed=discord.Embed(
                color=0x77b255,
                title="✅會員頻道權限審核通過",
                description=description
            )
            if send_result:
                await self.result_channel.send(
                    content=f"{message.author.mention}",
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions(roles=True)
                )
            user.set_user_role(user, member, member_role, user_role)
            self.update_dc_role(user)
            await self.save_users()
            return
        except VideoOwnChannelNotFit:
            error_name = "影片所屬頻道錯誤" 
        except CommentFailure:
            error_name = "YT 留言驗證錯誤" 
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
            if send_result:
                await self.result_channel.send(
                    content=f"{message.author.mention}",
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions(roles=True)
                )
            return
        
        err_msg = err_msg.format(handler_msg)
        if error_name:
            err_msg = f"**{error_name}**，{err_msg}"
        embed = discord.Embed(
            color=0xff0000,
            title=_("❌會員頻道權限審核未通過"),
            description= err_msg,
        )
        if send_result:
            await self.result_channel.send(
                content=f"{message.author.mention}",
                embed=embed,
                allowed_mentions=discord.AllowedMentions(roles=True)
            )

    # endregion