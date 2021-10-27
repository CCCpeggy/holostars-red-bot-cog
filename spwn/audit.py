from redbot.core.i18n import cog_i18n, Translator, set_contextual_locales_from_guild
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils.mod import is_mod_or_superior
from redbot.core import checks, commands, Config
from redbot.core.utils import AsyncIter
from redbot.core.bot import Red
import logging
import asyncio
import contextlib
import discord
from discord.utils import get
from typing import MutableMapping

from .errors import (
    AuditException,
    NoSPWNID,
    NoDiscordID,
    WrongSPWNID,
    RepeatSPWNID,
    ModRefused,
    ReactionTimeout,
    ServerError
)

_ = Translator("SPWNAuditor", __file__)
log = logging.getLogger("red.core.cogs.SPWNAuditor")

class Audit(commands.Cog):

    global_defaults = {
        "spwn_id": []
    }

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, 62626262)
        self.config.register_global(**self.global_defaults)
        self.bot.loop.create_task(self.load_var())

    async def load_var(self):
        self.spwn_id = await self.config.spwn_id()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if message.author.bot:
            return
        await self.audit_data(message)

    async def audit_data(self, message):
        input_channel_ids = 902566141786988575
        if message.channel.id != input_channel_ids:
            return
        result_channel_id = 902566271902707732
        new_channel_id = 901845395326525450
        role_id = 901845427865919508
        error_name = None
        handler_msg = "此為機器人自動偵測。"
        err_msg = """請重新檢查資料後重新傳送審核資料。
 有任何疑問請至 <#902566671171092550>。
 {}"""

        color=0xff0000,
        title="❌權限審核未通過"
        try:
            result_channel = self.bot.get_channel(result_channel_id)
            role = get(message.guild.roles, id=role_id)
            if not result_channel or not role:
                raise ServerError
            info = get_info(message.content)

            if info["spwn_id"] in self.spwn_id:
                raise RepeatSPWNID
       
            reaction, mod = await self.send_reaction_check_cross(message)
            new_channel = self.bot.get_channel(new_channel_id)
            if reaction == "Done":
                self.spwn_id.append(info["spwn_id"])
                await self.config.spwn_id.set(self.spwn_id)
                await message.author.add_roles(
                    role,
                    reason=f"SPWN 權限審核通過"
                )
                close_channel = self.bot.get_channel(902566905192284212)
                await close_channel.set_permissions(message.author, read_messages=False)
                close_channel = self.bot.get_channel(input_channel_ids)
                await close_channel.set_permissions(message.author, read_messages=False)
                close_channel = self.bot.get_channel(902566671171092550)
                await close_channel.set_permissions(message.author, read_messages=False)
            elif reaction == "Cancel":
                raise ModRefused
            else:
                raise ReactionTimeout
        except NoSPWNID:
            error_name = "沒有提供 SPWN UID"
        except NoDiscordID:
            error_name = "沒有提供 Discord User ID"
        except WrongSPWNID:
            error_name = "錯誤的 SPWN UID"
        except RepeatSPWNID:
            error_name = "重複的 SPWN UID"
        except ModRefused:
            handler_msg = f"處理人：{mod.mention}"
            pass
        except ReactionTimeout:
            # error_name = "管理員未在一天內審核"
            log.info(f"未審核：{message.id}, {message.content}")
            return
        except ServerError:
            error_name = "伺服器錯誤"
            await result_channel.send(
                f"{message.author.mention}",
                embed=discord.Embed(
                    color=0x77b255,
                    title=_("伺服器錯誤"),
                    description="""伺服器錯誤，請稍後一下""",
                )
            )
            return
        else:
            await result_channel.send(
                f"{message.author.mention}",
                embed=discord.Embed(
                    color=0x77b255,
                    title=_("✅審核通過"),
                    description=f"""增加身分組：{role.mention}
請確認看得見會員頻道：{new_channel.mention}
處理人：{mod.mention}""",
                )
            )
            return

        err_msg = err_msg.format(handler_msg)
        if error_name:
            err_msg = f"**{error_name}**，{err_msg}"
            await result_channel.send(
                f"{message.author.mention}",
            embed=discord.Embed(
                color=0xff0000,
                title=_("❌審核未通過"),
                description= err_msg,
            )
        )

    async def _clear_react(
            self, message: discord.Message, emoji: MutableMapping = None) -> asyncio.Task:
        """Non blocking version of clear_react."""
        task = self.bot.loop.create_task(self.clear_react(message, emoji))
        return task

    async def clear_react(self, message: discord.Message, emoji: MutableMapping = None) -> None:
        try:
            await message.clear_reactions()
        except discord.Forbidden:
            if not emoji:
                return
            with contextlib.suppress(discord.HTTPException):
                async for key in AsyncIter(emoji.values(), delay=0.2):
                    await message.remove_reaction(key, self.bot.user)
        except discord.HTTPException:
            return

    async def send_reaction_check_cross(self, message):
        # mods = list(set([role.members for role in await self.bot.get_mod_roles(message.guild)]))
        emojis = {
            "\N{WHITE HEAVY CHECK MARK}": "Done",
            "\N{NEGATIVE SQUARED CROSS MARK}": "Cancel"
        }
        emojis_list = list(emojis.keys())

        async def add_reaction():
            with contextlib.suppress(discord.NotFound):
                for emoji in emojis_list:
                    await message.add_reaction(emoji)
        task = asyncio.create_task(add_reaction())
        try:
            while True:
                (r, u) = await self.bot.wait_for(
                    "reaction_add",
                    check=ReactionPredicate.with_emojis(emojis_list, message),
                    timeout=86400  # 1 天
                )
                if await is_mod_or_superior(self.bot, u):
                    if u != message.author or await self.bot.is_owner(u):
                        break
                    else:
                        log.info(f"{u.id} 對 {message.author.id} 的審核做出回應，但權限不符合" )
                else:
                    log.info(f"{u.id} 不是 mod 或 superior" )
        except asyncio.TimeoutError:
            return None, None
        if task is not None:
            task.cancel()
        await self._clear_react(message, emojis_list)
        return emojis[r.emoji], u
    
def get_info(message):
    discord_id = False
    spwn_id = None
    message = strQ2B(message).replace(" ", "").replace("_", "").replace("-", "")
    message = message.lower()
    for s in message.split('\n'):
        tmp = s.split(':')
        if len(tmp) < 2:
            continue
        key, value = tmp
        if key == "discordid":
            discord_id = True
        elif key == "spwnid" or key == "spwnuid":
            if len(value) != 28:
                raise WrongSPWNID
            for c in value:
                if (c >= 'a' and c <= 'z') or (c >= '0' and c <= '9'):
                    pass
                else:
                    raise WrongSPWNID
            spwn_id = value
    if not spwn_id:
        raise NoSPWNID
    if not discord_id:
        raise NoDiscordID
    return {
        "spwn_id": spwn_id
    }

def strQ2B(ustring):
    """把字串全形轉半形"""
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code==0x3000:
            rstring += " "
        elif inside_code > 65281 and inside_code < 65374 :
            rstring += chr(inside_code - 0xfee0)
        else:
            rstring += uchar
    return rstring
