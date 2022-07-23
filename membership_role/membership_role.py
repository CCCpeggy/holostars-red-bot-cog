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
        
        "membership_input_channel_id": None,
        "membership_result_channel_id": None,
        "membership_command_channel_id": None,
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
            await self.bot.wait_until_ready()
            async def load_members():
                for key, value in (await self.config.members()).items():
                    self.add_member(**value)
            await load_members()
            async def load_users():
                for key, value in (await self.config.users()).items():
                    self.add_user(**value)
            await load_users()
        
            # channel
            input_channel_id = await self.config.membership_input_channel_id()
            command_channel_id = await self.config.membership_command_channel_id()
            result_channel_id = await self.config.membership_result_channel_id()
            self.input_channel = get_text_channel(self.bot, input_channel_id)
            self.command_channel = get_text_channel(self.bot, command_channel_id)
            self.result_channel = get_text_channel(self.bot, result_channel_id)
            
            await self.check()
            

        self.task: asyncio.Task = self.bot.loop.create_task(initial())
        

    def cog_unload(self):
        if self.task:
            self.task.cancel()

    async def check(self):
        while True:
            log.info("--------check----------")
            tmp_channel = get_text_channel(self.bot, 875001908350316544)
            try:
                remove_user_ids = []
                for user in self.users.values():
                    guild: discord.Guild = self.input_channel.guild
                    dc_user: discord.Member = guild.get_member(user.id)
                    if not dc_user:
                        remove_user_ids.append(user.id)
                    
                    invalid_role_ids = []
                    for role_id, user_role in user.roles.items():
                        role_id = to_role_id(role_id)
                        deleted = False
                        role: discord.Role = guild.get_role(role_id)
                        try:
                            member = self.get_member_by_role(role_id)
                        except:
                            continue
                        if not user_role.is_expired():
                            continue
                        elif not await user_role.check():
                            await dc_user.remove_roles(role, reason=f"身分組到期: {user_role.end_time}")
                            deleted = True
                            await tmp_channel.send(f"Debug 中：{dc_user.mention} 的 {member.names[0]} 會員身分組已到期，請再次發送驗證資料", 
                                    allowed_mentions=discord.AllowedMentions.none())
                            # await dc_user.send(f"您的 {member.names[0]} 會員身分組已到期，請再次發送驗證資料")
                        elif member.default_type_name:
                            default_role_id = member.membership_type[member.default_type_name]
                            if default_role_id != role_id:
                                default_role = get(guild.roles, id=default_role_id)
                                await tmp_channel.send(f"Debug 中：{dc_user.mention} 的新一個月的 {member.names[0]} 會員身分組驗證成功，但因無法驗證等級，所以自動降為 {member.default_type_name}，如需提高等級請重新發送驗證資料", 
                                    allowed_mentions=discord.AllowedMentions.none())
                                # await dc_user.send(f"您的新一個月的 {member.names[0]} 會員身分組驗證成功，但因無法驗證等級，所以自動降為 {member.default_type_name}，如需提高等級請重新發送驗證資料")
                                await dc_user.remove_roles(role, reason=f"身分組到期 ({user_role.end_time})，更換成預設身分組")
                                deleted = True
                                await dc_user.add_roles(default_role, reason=f"身分組到期 ({user_role.end_time})，更換成預設身分組")
                                user.roles[default_role_id] = user.roles[role_id]
                        if deleted:
                            invalid_role_ids.append(str(role_id))
                            if role in dc_user.roles: # 刪除失敗
                                await self.command_channel.send(f"{dc_user.mention} 的 {role.mention} 身分組刪除失敗，請管理員幫忙確認並刪除", 
                                    allowed_mentions=discord.AllowedMentions.none())
                    
                    for role_id in invalid_role_ids:
                        user.remove_role(role_id)
                    if len(user.roles) == 0:
                        remove_user_ids.append(user.id)
                    await self.save_users()
                for user_id in remove_user_ids:
                    log.info(f"check: remove user {user_id}")
                    self.remove_user(user_id)
                await self.save_users()
            except Exception as e:
                log.error(e)
            log.info("--------check end----------")
            await asyncio.sleep(3600)
    
    def get_member_by_role(self, role_id):
        role_id = to_role_id(role_id)
        member = [member for member in self.members.values() if role_id in member.membership_type.values()]
        if len(member) != 1:
            raise Exception
        return member[0]
    
    def add_member(self, channel_id: str, **kwargs) -> Optional[Member]:
        if channel_id in self.members:
            log.debug(f"add_member: {channel_id} already exists")
            raise AlreadyExists
        member = Member(
            bot=self.bot,
            channel_id=channel_id, 
            _save_func=self.save_members,
            **kwargs
        )
        self.members[channel_id] = member
        return member
    
    def remove_member(self, channel_id: str, **kwargs) -> None:
        if channel_id not in self.members:
            log.debug(f"remove_member: {channel_id} is not exists")
            raise NotExists
        del self.members[channel_id]
    
    async def save_members(self):
        await self.config.members.set(ConvertToRawData.dict(self.members))
   
    def add_user(self, id: Union[discord.Member, discord.User, int, str], **kwargs) -> Optional[User]:
        id = to_user_id(id)
        if id in self.users:
            log.debug(f"add_user: {id} already exists")
            raise AlreadyExists
        user = User(
            bot=self.bot,
            id=id, 
            _save_func=self.save_users,
            **kwargs
        )
        self.users[id] = user
        return user
    
    def remove_user(self, id: Union[discord.Member, discord.User, int, str], **kwargs) -> Optional[User]:
        id = to_user_id(id)
        if id not in self.users:
            log.debug(f"remove_user: {id} not exists")
            return
        del self.users[id]
    
    def add_user_role(self, id: Union[discord.Member, discord.User, int, str], member: Member, end_time: Union[str, datetime], type_name: str, tmp: bool=False, **kwargs) -> Optional[User]:
        id = to_user_id(id)
        user = self.users.get(id, None)
        if not user:
            log.debug(f"add_user_role: {id} not exists")
            raise NotExists
        role = member.membership_type.get(type_name, None)
        if not role:
            log.debug(f"add_user_role: {type_name} not exists")
            raise NotExists
        return user.add_role(role, end_time=end_time, tmp=tmp, **kwargs)
    
    async def save_users(self):
        await self.config.users.set(ConvertToRawData.dict(self.users))
    
    def remove_user_role(self, user_id: Union[discord.Member, discord.User, int, str], role_id: Union[discord.Role, int, str]) -> Optional[User]:
        user_id = to_user_id(user_id)
        user = self.users.get(user_id, None)
        if not user:
            log.debug(f"remove_user_role: {user_id} not exists")
            raise NotExists
        user.remove_role(role_id)
        if len(user.roles) == 0:
            self.remove_user(user_id)
    
    def get_role_by_member(self, member: Member, user: User) -> int:
        role_id = intersection(member.membership_type.values(), user.roles.keys())
        if len(role_id) == 0:
            return None
        if len(role_id) > 1:
            log.error(f"more than one fit: {role_id}")
            # raise Exception
        return role_id[0]
    
    async def change_role_level(self, user_id: Union[discord.Member, discord.User, int, str], new_role_id: Union[discord.Role, int, str], reason: str=None):
        user_id = to_user_id(user_id)
        new_role_id: int = to_user_id(new_role_id)
        guild: discord.Guild = self.input_channel.guild
        if user_id not in self.users:
            raise NotExists
        user = self.users[user_id]
        member: Member = self.get_member_by_role(new_role_id)
        old_role_id = self.get_role_by_member(member, user)
        if not old_role_id:
            raise NotExists
        
        if old_role_id != new_role_id:
            old_role: discord.Role = guild.get_role(old_role_id)
            new_role: discord.Role = guild.get_role(new_role_id)
            if not old_role or not new_role:
                raise Exception
            dc_user: discord.Member = guild.get_member(user_id)
            await dc_user.remove_roles(old_role, reason=reason)
            await dc_user.add_roles(new_role, reason=reason)
            user.roles[new_role_id] = user.roles.pop(old_role_id)
            
    
    async def get_member_by_name(self, name: str) -> Member:
        try:
            return await MemberConverter.convert(_, None, name)
        except commands.BadArgument:
            return None
    
    @commands.group(name="role")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def role_group(self, ctx: commands.Context):
        """管理會員身分組
        """
        pass
    
    @role_group.command(name="add")
    async def _add_role(
        self, ctx: commands.Context, dc_member: discord.Member, member: MemberConverter, date: str
        , channel_id: str = None, video_id: str = None):
        """對使用者加入暫時身分組
        
        dc_member: 要增加身分組的使用者
        member (字串): 成員名稱
        date: 到期日期
        """
        comment_id = None
        if video_id != None:
            comment_data = await get_comment_info(video_id, channel_id=channel_id)
            if comment_data == None:
                await ctx.send("找不到留言")
                return
            comment_id = comment_data["comment_id"]
        try:
            user = self.add_user(dc_member)
        except AlreadyExists:
            user = self.users[dc_member.id]
        except Exception as e:
            await ctx.reply("發生不明錯誤")
            log.error(f"on_message: {e}")
            return
        
        # get type name
        type_names = list(member.membership_type.keys())
        if len(type_names) == 0:
            raise ServerError
        elif len(type_names) == 1:
            type_name = type_names[0]
        else:
            msg = []
            emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
            for i in range(len(type_names)):
                msg.append(f"{emoji[i]}: {type_names[i]}")
            msg = "\n".join(msg)
            msg = await ctx.reply(msg)
            index = await add_waiting_reaction(self.bot, msg, emoji[:len(type_names)])
            type_name = type_names[index]
        
        try:
            user_role: UserRole = self.add_user_role(
                dc_member, member, date, type_name,tmp=True,
                video_id=video_id,
                channel_id=channel_id,
                comment_id=comment_id,
            )
        except Exception as e:
            await self.command_channel.send("發生不明錯誤")
            log.error(f"_add_role: {e}")
            return
        user_role.valid()
        old_role_id = self.get_role_by_member(member, user)
        if old_role_id:
            if not user_role.video_id:
                old_user_role = user.roles[old_role_id]
                user_role.video_id = old_user_role.video_id
                user_role.channel_id = old_user_role.channel_id
                user_role.video_id = old_user_role.video_id
            user.remove_role(old_role_id)
            old_role: discord.Role = ctx.guild.get_role(old_role_id)
            await dc_member.remove_roles(old_role, reason=f"經管理員手動更新身分組等級")
        role_id = member.membership_type.get(type_name, None)
        user.set_role(role_id, user_role)
        
        await self.save_users()
        role = get(ctx.guild.roles, id=role_id)
        await dc_member.add_roles(role, reason=f"mod: {dc_member}, expiration date: {date}")
        
        await ctx.send(f"{dc_member.mention} 已新增身分組 {role.mention}", allowed_mentions=discord.AllowedMentions.none())
        
    @role_group.command(name="check")
    async def _check_role(
        self, ctx: commands.Context, member: MemberConverter):
        """對成員下的身分組做檢查
        """
        non_temp_list = []
        for type_name, role_id in member.membership_type.items():
            role = get(ctx.guild.roles, id=role_id)
            for member in role.members:
                user = self.users.get(member.id, None)
                if not user or role_id not in user.roles or user.roles[role_id].is_expired():
                    if len(non_temp_list) >= 50:
                        await ctx.send(f"{role.mention} 名單：{', '.join(non_temp_list)}",
                        allowed_mentions=discord.AllowedMentions.none())
                        non_temp_list = []
                    non_temp_list.append(f"{member.mention} ({member.id})")
            if len(non_temp_list) > 0:
                await ctx.send(f"{role.mention} 名單：{', '.join(non_temp_list)}",
                allowed_mentions=discord.AllowedMentions.none())
        await ctx.send("檢查結束")
            
    
    @role_group.group(name="member")
    async def member_group(self, ctx: commands.Context):
        """會員成員管理
        """
        pass

    @member_group.command(name="add")
    async def _add_member(self, ctx: commands.Context, channel_id: str, names: str, type_name: str, role: discord.Role, text_channel: discord.TextChannel):
        """加入會員成員

        channel_id (字串): YouTube 頻道 ID。
        names (字串): 成員名稱，無視大小寫，多個可用 `,` 隔開，例如：`name1,name2,name3`。
        type_name (字串): 預設的身分組名稱
        role (身分組): 預設的身分組
        text_channel (文字頻道): 所屬的文字頻道。
        """
        names = names.lower().split(",")
        try:
            if len(names) == 0:
                raise WrongMemberNameStr
            member = self.add_member(
                channel_id=channel_id,
                names=names,
                text_channel_id=text_channel.id
            )
            member.add_membership_type(type_name, role, True)
            await self.save_members()
            await ctx.send(f"成功加入會員成員: `{member.names[0]}`")
        except WrongMemberNameStr:
            await ctx.send("沒有加入會員成員，錯誤的 names 格式")
        except AlreadyExists:
            await ctx.send("沒有加入會員成員，`{channel_id}` 已經存在")
        except Exception as e:
            await ctx.send("沒有加入會員成員，發生未知錯誤")
            log.error(f"_add_member: {e}")
    
    @member_group.command(name="list")
    async def _list_member(self, ctx: commands.Context, member: MemberConverter=None):
        """列出會員成員

        member (字串, 可選): 會員成員名稱。
        """
        if member:
            await ctx.send(f"{member}")
        else:
            for member in self.members.values():
                await ctx.send(f"{member}")

    @member_group.command(name="remove")
    async def _remove_member(self, ctx: commands.Context, member: MemberConverter):
        """刪除會員成員

        member (字串): 成員名稱
        """
        try:
            self.remove_member(member.channel_id)
            await self.save_members()
            await ctx.send(f"成功刪除會員成員: `{member.names[0]}`")
        except:
            await ctx.send("沒有成功刪除會員成員，發生未知錯誤")
    
    @role_group.group(name="member_type")
    async def member_type_group(self, ctx: commands.Context):
        """會員身分組管理
        """
        pass

    @member_type_group.command(name="add")
    async def add_membership_type(self, ctx: commands.Context, member: MemberConverter, type_name: str, role: discord.Role):
        """新增會員成員所屬的身分組

        member (字串): 成員名稱
        type_name (字串): 身分組名稱
        role (身分組): 對應的身分組
        """
        if member.add_membership_type(type_name, role):
            await self.save_members()
            await ctx.send(f"已加入身分組 `{type_name}`")
        else:
            await ctx.send(f"沒有成功加入等級身分組，`{type_name}` 已經存在")

    @role_group.group(name="user")
    async def user_group(self, ctx: commands.Context):
        """管理使用者
        """
        pass

    @user_group.command(name="change_level")
    async def _change_role_level(self, ctx: commands.Context, user: discord.Member, role: discord.Role):
        """變更使用者的會員身分
        """
        try:
            await self.change_role_level(user.id, role.id, "下指令變更")
            await self.save_users()
            await ctx.send(f"已變更身分組 `{role}`")
        except NotExists:
            await self.command_channel.send("此使用者沒有相符的身分組")
        except Exception as e:
            await self.command_channel.send("發生不明錯誤")
            log.error(f"on_message: {e}")

    @user_group.command(name="list")
    async def _user_list(self, ctx: commands.Context):
        """列出使用者
        """
        info = []
        for user in self.users.values():
            guild: discord.Guild = self.input_channel.guild
            dc_user: discord.Member = guild.get_member(user.id)
            role_info = []
            for role_id, user_role in user.roles.items():
                role_info.append(get(guild.roles, id=role_id).mention)
            info.append(f"{dc_user.mention} 有身分組 {', '.join(role_info)}")
        msg = "\n".join(info)
        for i in range(0, len(msg), 2000):
            await ctx.send(msg[i:i + 2000], allowed_mentions=discord.AllowedMentions.none())

    @role_group.command(name="audit")
    async def _audit_membership(self, ctx: commands.Context, send_result: bool=True):
        """補驗證訊息
        """
        async def get_message(channel, message_id):
            try:
                message = await channel.fetch_message(message_id)
            except:
                return False
            else:
                return message

        if ctx.message.reference:
            msg = await get_message(ctx.channel, ctx.message.reference.message_id)
            if msg:
                await self.audit_membership(msg, send_result)
            else:
                await ctx.send(f"找不到原始訊息")
        else:
            await ctx.send(f"請回覆要驗證的訊息")
    
    @role_group.command(name="stars")
    async def test_init(self, ctx: commands.Context):
        """(還不能用) 自動設定 stars 的身分組 (寫死的)
        """
        # TODO
        log.debug("----------------stars setting------------------")
        from discord.utils import get
        roles = {
            "アランファミリー集会": 939752456299118612,
            "アランファミリー幹部会": 939752597886238780,
            "アランファミリー役員会": 939752634607358002
        }
        papa_1 = get(ctx.guild.roles, id=939752456299118612)
        papa_2 = get(ctx.guild.roles, id=939752597886238780)
        papa_3 = get(ctx.guild.roles, id=939752634607358002)
        papa_text_channel  = get_text_channel(self.bot, 864755730677497876)
        log.debug("----------------stars add member------------------")
        member: Member = await self.get_member_by_name("aruran")
        if member:
            await self._remove_member(ctx, member)
        await self._add_member(ctx, "UCKeAhJvy8zgXWbh9duVjIaQ", "aruran,アルランディス", papa_text_channel)
        member: Member = await self.get_member_by_name("aruran")
        log.debug("----------------stars add member type------------------")
        await self.add_membership_type(ctx, member, "アランファミリー集会", papa_1)
        await self.add_membership_type(ctx, member, "アランファミリー幹部会", papa_2)
        await self.add_membership_type(ctx, member, "アランファミリー役員会", papa_3)
        await ctx.send(f"完成加入 aruran: \n{member}")
        log.debug("----------------stars setting end------------------")
        
    @role_group.command(name='input')
    async def set_input(self, ctx: commands.Context, text_channel: discord.TextChannel):
        """設定使用者輸入會員資料的文字頻道"""
        self.input_channel = text_channel
        await self.config.membership_input_channel_id.set(text_channel.id)
        await ctx.send(_(f"已設定"))

    @role_group.command(name='result')
    async def _set_result(self, ctx: commands.Context, text_channel: discord.TextChannel):
        """設定回覆使用者審核結果的文字頻道"""
        self.result_channel = text_channel
        await self.config.membership_result_channel_id.set(text_channel.id)
        await ctx.send(_(f"已設定"))

    @role_group.command(name='command')
    async def set_command(self, ctx: commands.Context, text_channel: discord.TextChannel):
        """設定下會員設定指令的文字頻道"""
        self.command_channel = text_channel
        await self.config.membership_command_channel_id.set(text_channel.id)
        await ctx.send(_(f"已設定"))    
    
    @role_group.command(name="test")
    async def test(self, ctx: commands.Context):
        log.debug("----------------test------------------")
        from discord.utils import get
        dc_role = get(ctx.guild.roles, id=879027799204188190)
        dc_role_2 = get(ctx.guild.roles, id=879027873682436147)
        text_channel  = get_text_channel(self.bot, 864755730677497876)
        # add member
        member: Member = await self.get_member_by_name("astel")
        if member:
            await self._remove_member(ctx, member)
        await self._add_member(ctx, "UCNVEsYbiZjH5QLmGeSgTSzg", "astel,アステル", "test", dc_role, text_channel)
        member: Member = await self.get_member_by_name("astel")
        await self.add_membership_type(ctx, member, "test2", dc_role_2)
        
        message = """
頻道：astel
日期：2022/4/01
影片：RzIWjDoBH1E
YT：UC6wTWzIJiKoKvtoPdbGE07w
        """
        ctx.message.content = message
        await self.audit_membership(ctx.message)
        return
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
            log.debug("----------------test end------------------")
            
    
    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, message: discord.Message):
        ctx = await self.bot.get_context(message)
        if message.content.startswith("-"):
            return
        if not (self.result_channel and self.command_channel and self.result_channel):
            return
        if not is_specify_text_channel(ctx, text_channel_id=self.input_channel.id):
            return
        if is_bot(ctx):
            return
        image_url = [a.url for a in message.attachments]
        if len(image_url):
            await self.command_channel.send("\n".join(image_url))
        if message.content == "":
            return
        await self.audit_membership(message)

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
            if not Time.is_time_in_future_range(info["date"], months=1):
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
            type_names = list(member.membership_type.keys())
            if len(type_names) == 0:
                raise ServerError
            elif len(type_names) == 1:
                type_name = type_names[0]
            else:
                msg = []
                emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
                for i in range(len(type_names)):
                    msg.append(f"{emoji[i]}: {type_names[i]}")
                msg = "\n".join(msg)
                msg = await mod_check_msg.reply(msg)
                index = await add_waiting_reaction(self.bot, msg, emoji[:len(type_names)])
                type_name = type_names[index]
            role_id = member.membership_type.get(type_name, None)
            role = get(message.guild.roles, id=role_id)
            
            try:
                user = self.add_user(message.author)
            except AlreadyExists:
                user = self.users[message.author.id]
            except Exception as e:
                await mod_check_msg.reply("發生不明錯誤")
                log.error(f"on_message: {e}")
                return

            # TODO: 檢查是否有同會員成員不同身分組
            try:
                user_role: UserRole = self.add_user_role(
                    message.author, 
                    member,
                    info["date"], 
                    type_name,
                    video_id=info["video_id"],
                    channel_id=info["channel_id"],
                    comment_id=comment_data["comment_id"] if comment_data else None,
                    tmp=True
                )
            except Exception as e:
                await self.command_channel.send("發生不明錯誤")
                log.error(f"on_message: {e}")
                return
            
            user_role.valid()
            description="\n".join([
                f"增加身分組：{role.mention}",
                f"請確認看得見會員頻道：{member._text_channel.mention}",
                f"處理人：{mod_user.mention}"])
            embed=discord.Embed(
                color=0x77b255,
                title=_("✅會員頻道權限審核通過"),
                description=description
            )
            if send_result:
                await self.result_channel.send(
                    content=f"{message.author.mention}",
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions(roles=True)
                )
            old_role_id = self.get_role_by_member(member, user)
            if old_role_id:
                if not user_role.video_id:
                    old_user_role = user.roles[old_role_id]
                    user_role.video_id = old_user_role.video_id
                    user_role.channel_id = old_user_role.channel_id
                    user_role.video_id = old_user_role.video_id
                user.remove_role(old_role_id)
                old_role: discord.Role = message.guild.get_role(old_role_id)
                await message.author.remove_roles(old_role, reason=f"經審核更新身分組等級")
            user.set_role(role_id, user_role)
            
            await self.save_users()
            await message.author.add_roles(role,
                    reason=f"mod: {message.author}, expiration date: {info['date']}")
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

    @role_group.command(name="download")
    @checks.is_owner()
    async def settings(self, ctx: commands.Context):
        """伺服器設定輸出"""
        data = json.dumps(await self.config.get_raw()).encode('utf-8')
        to_write = BytesIO()
        to_write.write(data)
        to_write.seek(0)
        await ctx.send(file=discord.File(to_write, filename=f"global_settings.json"))
        data = json.dumps(await self.config.guild(ctx.guild).get_raw()).encode('utf-8')
        to_write = BytesIO()
        to_write.write(data)
        to_write.seek(0)
        await ctx.send(file=discord.File(to_write, filename=f"guild_settings.json"))
