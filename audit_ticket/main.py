
# discord
import discord
import logging

# redbot
from redbot.core.bot import Red
from redbot.core import commands, checks, Config
from redbot.core.i18n import cog_i18n, Translator

# other
from typing import *

# local
from .role import Role
from .errors import *
from .utils import *

_ = Translator("TicketAuditor", __file__)
log = logging.getLogger("red.core.cogs.TicketAuditor")

class AuditTicket(commands.Cog):

    global_defaults = {
        "detect_channel": None,
        "result_channel": None,
        "roles": {} # emoji, Role
    }

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, 22091855)
        self.config.register_global(**self.global_defaults)
        self.bot.loop.create_task(self.load_var())
        self.roles: List[Role] = {}
        self.detect_channel: discord.TextChannel = None
        self.result_channel: discord.TextChannel = None

    async def load_var(self):
        for role_config in (await self.config.roles()).values():
            try:
                self.add_role(**role_config)
            except Exception as e:
                log.error(f"[load_var][role]: {e}")
        
        self.detect_channel = await self.config.detect_channel()
        if self.detect_channel:
            self.detect_channel = self.bot.get_channel(self.detect_channel)

        self.result_channel = await self.config.result_channel()
        if self.result_channel:
            self.result_channel = self.bot.get_channel(self.result_channel)

    async def save_roles(self):
        await self.config.roles.set(ConvertToRawData.dict(self.roles))

    def add_role(self, emoji: str, role_ids: List[id], **kwargs):
        emoji = str(emoji)
        if emoji in self.roles:
            raise AlreadyExisted
        role = Role(
            self.bot,
            emoji=emoji,
            role_ids=role_ids,
            **kwargs
        )
        self.roles[emoji] = role
        return role

    @commands.group(name="event_role")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def role_group(self, ctx: commands.Context):
        """身分審核"""
        pass

    @role_group.command(name="detect_channel")
    async def set_detect_channel(self, ctx: commands.Context, text_channel: discord.TextChannel):
        """設定偵測的頻道"""
        self.detect_channel = text_channel
        await self.config.detect_channel.set(text_channel.id)
        await ctx.send(f"偵測的頻道已設定為 {text_channel.mention}")

    @role_group.command(name="result_channel")
    async def set_result_channel(self, ctx: commands.Context, text_channel: discord.TextChannel):
        """設定結果檢視的頻道"""
        self.result_channel = text_channel
        await self.config.result_channel.set(text_channel.id)
        await ctx.send(f"結果檢視的頻道已設定為 {text_channel.mention}")

    @role_group.command(name="add")
    async def _add_role(self, ctx: commands.Context, emoji: EmojiConverter, role: discord.Role):
        """新增身分"""
        emoji = str(emoji)
        if emoji in self.roles:
            if role.id in self.roles[emoji].role_ids:
                await ctx.send("已經存在")
                return
            else:
                self.roles[emoji].add_role(role.id)
        else:
            self.roles[emoji] = self.add_role(emoji=emoji, role_ids=[role.id])
        await self.save_roles()
        await ctx.send(f"已新增完成 {self.roles[emoji]}")
        
    @role_group.command(name="remove")
    async def _remove_role(self, ctx: commands.Context, emoji: EmojiConverter):
        """刪除身分"""
        emoji = str(emoji)
        if emoji in self.roles:
            self.roles.pop(emoji)
            await self.save_roles()
            await ctx.send(f"已刪除完成")
        else:
            await ctx.send(f"{emoji} 不存在於清單中")
        

    @role_group.command(name="list")
    async def _list_role(self, ctx: commands.Context):
        """列出身分清單"""
        await ctx.send("\n ".join([str(role) for role in self.roles.values()]))

    @role_group.group(name="passed_event")
    @commands.guild_only()
    async def passed_event_group(self, ctx: commands.Context):
        """身分審核"""
        pass

    @passed_event_group.command(name="tag_channel")
    async def _on_pass_tag_member(self, ctx: commands.Context, emoji: EmojiConverter, channel: Union[discord.TextChannel, discord.Thread]=None):
        """在通過審核時 TAG 成員在指定的頻道"""
        emoji = str(emoji)
        if emoji in self.roles:
            self.roles[emoji].tag_channel_id = channel.id if channel else None
            await self.save_roles()
            await ctx.send(f"已設定完成 {self.roles[emoji]}")
        else:
            await ctx.send(f"{emoji} 不存在於清單中")
    
    @role_group.command(name="can_see_channel")
    async def add_can_see_channel(self, ctx: commands.Context, emoji: EmojiConverter, channel: Union[discord.TextChannel, discord.Thread]=None):
        """設定身分組可以看見的頻道"""
        emoji = str(emoji)
        if emoji in self.roles:
            if channel.id in self.roles[emoji].can_see_channel_id_list:
                self.roles[emoji].can_see_channel_id_list.remove(channel.id)
            else:
                self.roles[emoji].can_see_channel_id_list.append(channel.id)
            await self.save_roles()
            await ctx.send(f"已設定完成 {self.roles[emoji]}")
        else:
            await ctx.send(f"{emoji} 不存在於清單中")


    @commands.Cog.listener()
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id != self.detect_channel.id:
            return
        message = await self.detect_channel.fetch_message(payload.message_id)
    
        if message.author.bot or payload.member.bot:
            return

        if message.author.id == payload.member.id and message.author.id != 405327571903971333:
            return
            
        emoji = getEmoji(self.detect_channel.guild.emojis, str(payload.emoji))
        if emoji != "❌"  and str(emoji) not in self.roles:
            return
        await self.audit_data(message, emoji, payload.member)

    async def audit_data(self, message: discord.Message, emoji, mod):
        error_name = None
        handler_msg = "此為機器人自動偵測。"
        err_msg = """請重新檢查資料後重新傳送審核資料。
 有任何疑問請至 <#863343338933059594>。
 {}"""

        color=0xff0000,
        title="❌權限審核未通過"
        try:
            if emoji == "❌":
                raise ModRefused
            await self.pass_audit(message, emoji, mod)
        except ModRefused:
            error_name = "資料不正確"
            handler_msg = f"處理人：{mod.mention}"
            pass
        except Exception as e:
            log.error(f"[audit_data]: {e}")
            return
        else:
            return

        err_msg = err_msg.format(handler_msg)
        if error_name and self.result_channel:
            err_msg = f"**{error_name}**，{err_msg}"
            await self.result_channel.send(
                f"{message.author.mention}",
            embed=discord.Embed(
                color=0xff0000,
                title=_("❌審核未通過"),
                description= err_msg,
            )
        )

    async def pass_audit(self, message, emoji, mod):
        dc_roles = []
        for role_id in self.roles[emoji].role_ids:
            dc_role = discord.utils.get(message.guild.roles, id=role_id)
            if dc_role:
                dc_roles.append(dc_role)
                await message.author.add_roles(dc_role, reason=f"權限審核通過")

        if self.result_channel:
            output_data = []
            output_data.append(f"增加身分組：{', '.join([role.mention for role in dc_roles])}")
            if len(self.roles[emoji].can_see_channel_id_list) > 0:
                channels = [self.bot.get_channel(channel_id) for channel_id in self.roles[emoji].can_see_channel_id_list]
                output_data.append(f"請確認看得見會員頻道：{', '.join([channel.mention for channel in channels if channel is not None])}")
            output_data.append(f"處理人：{mod.mention}")
            await self.result_channel.send(
                f"{message.author.mention}",
                embed=discord.Embed(
                    color=0x77b255,
                    title=_("✅審核通過"),
                    description="\n".join(output_data)
                )
            )

        if self.roles[emoji].tag_channel_id:
            tag_channel = self.bot.get_channel(self.roles[emoji].tag_channel_id)
            if tag_channel:
                await tag_channel.send(f"{message.author.mention}")
