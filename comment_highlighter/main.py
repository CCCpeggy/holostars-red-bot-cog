# discord
import discord

# redbot
from redbot.core.bot import Red
from redbot.core import checks, commands, Config
from redbot.core.i18n import cog_i18n, Translator

# other
import logging
from typing import *
import asyncio

# local
from comment_highlighter.utils import *
from comment_highlighter.message import Message

# get logger
_ = Translator("HighLighter", __file__)
log = logging.getLogger("red.core.cogs.HighLighter")
log.setLevel(logging.DEBUG)

@cog_i18n(_)
class CommentHighLighter(commands.Cog):

    global_defaults = {
        track_message = {} # message_id, TrackedMessage
    }

    guild_defaults = {
        detect = {}, # channel_id, count
        send_channel_id = 0,
    }

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, 55661234)
        self.config.register_global(**self.global_defaults)
        self.config.register_guild(**self.guild_defaults)
        self.track_message: Dict[int, TrackedMessage] = {}

        for message_id, track_message in (await guild_config.track_message()).values():
            def wait_and_delete():
                await track_message.await_until_invalid()
                if message_id in self.track_message:
                    del self.track_message[message_id]
                    await self.save_track()
                    log.info(f"精華留言取消追蹤 {message_id}")
            self.bot.loop.create_task(self.wait_and_delete())
    
    async def save_track(self):
        await self.config.track_message.set(self.track_message)
    
    @bot.group(name='hl')
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def _highlight(ctx):
        """ 精華留言 Cog
        """
        pass

    @_highlight.command(name='channel')
    async def _highlight_channel(ctx, channel: discord.TextChannel, count: int=0):
        """ 設定文字頻道的表情符號作為精華留言的達成數量，如要取消取消則設定為 0
        """
        detect = await self.config.guild(ctx.guild).detect()
        if count > 0:
            detect[channel.id] = count
            await ctx.channel.send(f"已將 {channel.mention} 精華留言表情符號標準設定為 {count}")
        elif channel.id in detect:
            del detect[channel.id]
            await ctx.channel.send(f"已取消 {channel.mention} 的精華留言設定")
        await self.config.guild(guild).detect.set(detect)

    @_highlight.command(name='send')
    async def _highlight_channel(ctx, channel: discord.TextChannel):
        """ 設定精華留言的發送頻道
        """
        await self.config.guild(ctx.guild).send_channel_id.set(channel.id)
        await ctx.channel.send(f"已將精華留言的發送頻道設定為 {channel.mention}")

    @_highlight.command(name='list')
    async def _highlight_channel(ctx):
        """ 列出頻道對應的設定值
        """
        guild_config = self.config.guild(ctx.guild)

        # 取得精華留言頻道
        send_channel_id = await guild_config.send_channel_id()
        send_channel = ctx.guild.get_channel(send_channel_id)

        channel_data = []
        # 個別頻道達成表符數量
        for k, v in (await guild_config.detect()).items():
            channel = ctx.guild.get_channel(k)
            if channel:
                channel_data.append(f"> #{channel.name}: {v}")
        channel_data = "\n".join(channel_data)

        data = f"""伺服器設定
精華留言頻道：{send_channel.mention if send_channel else None}
達成表符數量：
{channel_data}
"""
        await ctx.channel.send(data)

    async def get_threshold(self, channel: Optional[discord.TextChannel, discord.Thread]):
        channel_id = channel.parent_id if isinstance(channel, discord.Thread) else channel.id
        return (await self.config.guild(channel.guild).detect()).get(channel_id, 0)

    async def get_hl_message(self, guild, message_id: int) -> discord.Message:
        send_channel = self.bot.get_channel(await self.config.guild(guild).send_channel_id())
        try:
            return await channel.fetch_message(message_id)
        except:
            return None

    @bot.event
    @commands.guild_only()
    async def on_raw_reaction_remove(payload):
        track_message = self.track_message.get(payload.message_id, None)
        # 不是精華留言的
        if track_message is None or track_message.hl_message_id <= 0:
            return

        guild_config = self.config.guild(payload.guild_id)
        msg_channel = self.bot.get_channel(payload.channel_id)
        threshold = await self.get_threshold(msg_channel)
        message = await msg_channel.fetch_message(payload.message_id)
        hl_msg = await get_hl_message(msg_channel.guild, track_message.hl_message_id)
        if not hl_msg:
            return

        if is_need_delete_highlight(message, threshold):
            await hl_msg.delete()
            track_message.hl_message_id = 0
            await self.save_track()
            log.info(f"表符小於{threshold}，所以刪除 {message.id} 的精華 {hl_msg.id}")
        else:
            msg, embed = create_highlight_msg(payload, message, threshold)
            await hl_msg.edit(msg, embed=embed)
            log.info(f"修改 {message.id} 的精華 {hl_msg.id}")

    @bot.event
    @commands.guild_only()
    async def on_raw_reaction_add(payload):
        # 確認是否是要追蹤的頻道
        msg_channel = self.bot.get_channel(payload.channel_id)
        threshold = await self.get_threshold(msg_channel)
        if threshold <= 0:
            return

        # 確認是否是追蹤的訊息，沒有追蹤則開始追蹤
        track_message = self.track_message.get(payload.message_id, None)
        if track_message is None:
            track_message = TrackedMessage(
                message_id=payload.message_id,
                channel_id=payload.channel_id,
            )
            self.track_message[payload.message_id] = track_message

        guild_config = self.config.guild(payload.guild_id)
        message = await msg_channel.fetch_message(payload.message_id)
        if message.content != "" and message.content[0] in ["!", "-"]:
            return
        send_channel = self.bot.get_channel(guild_config.send_channel_id)

        hl_msg = await get_hl_message(msg_channel.guild, track_message.hl_message_id)
      
        # 判斷是否已發送，已發送則更新
        if hl_msg:
            msg, embed = create_highlight_msg(payload, message, threshold)
            await hl_msg.edit(msg, embed=embed)
            log.info(f"已修改 {message.id} 的精華 {hl_msg.id}")
        elif is_need_highlight(message, threshold):
            msg, embed = create_highlight_msg(payload, message, threshold)
            hl_msg = await send_channel.send(msg, embed=embed)
            log.info(f"已新增 {message.id} 的精華 {hl_msg.id}")
            track_message.hl_message_id = hl_msg.id
            await self.save_track()

            await track_message.await_until_invalid()
            if message.id in self.track_message:
                del self.track_message[message_id]
                await self.save_track()
                log.info(f"精華留言取消追蹤 {message.id}")
