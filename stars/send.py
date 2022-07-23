# discord
from dis import dis
import discord

# redbot
from redbot.core.bot import Red
from redbot.core import checks, commands, Config
from redbot.core.i18n import cog_i18n, Translator

# other

# local
from .utils import *
from .streams import StreamStatus

_, log = get_logger()

@cog_i18n(_)
class SendManager(commands.Cog):

    global_defaults = {
        # "refresh_timer": 100000
    }

    guild_defaults = {
        "standby_message_format": "{time}\n{title}\n{url}{next_msg}!stream https://youtu.be/{video_id}{next_msg}!yt_start",
        "notify_message_format": "{mention}{channel_name}開播了！\n討論請至{chat_channel}",
        "collab_notify_message_format": "{mention}聯動開始了，討論請到{chat_channel}",
        "notify_embed_enable": True,
        "info_text_channel": None
    }

    def __init__(self, bot: Red, manager: "Manager"):
        self.bot = bot
        self.manager = manager
        self.config = Config.get_conf(self, 77656984)
        self.config.register_global(**self.global_defaults)
        self.config.register_guild(**self.guild_defaults)
    
    @commands.group(name="starsset")
    @checks.mod_or_permissions(manage_channels=True)
    async def starsset_group(self, ctx: commands.Context):
        pass

    @commands.guild_only()
    @starsset_group.group(name="message")
    async def message_group(self, ctx: commands.Context):
        pass
    
    @message_group.command(name="list")
    async def get_message_list(self,  ctx: commands.Context):
        standby_message_format = await self.config.guild(ctx.guild).standby_message_format()
        notify_message_format = await self.config.guild(ctx.guild).notify_message_format()
        notify_tmp_message_format = await self.config.guild(ctx.guild).collab_notify_message_format()
        notify_embed_enable = await self.config.guild(ctx.guild).notify_embed_enable()
        data = [
            f"**待機台的訊息格式**: {standby_message_format}",
            f"**通知的訊息格式**: {notify_message_format}",
            # f"**notify(tmp) message format**: {notify_tmp_message_format}",
            f"**是否啟用通知的內嵌訊息**: {notify_embed_enable}",
        ]
        await Send.send(ctx, "\n".join(data))

    @message_group.command(name="standby")
    async def set_standby_string_format(self,  ctx: commands.Context, message_format: str):
        """
        可使用的標籤：{time}, {title}, {video_id}, {channel_name}, {member_name}, {url}, {mention}, {description}, {new_line}, {next_msg}
        其中 video_id 是隨便一個人的 video_id
        """
        await self.config.guild(ctx.guild).standby_message_format.set(message_format)
        await Send.set_up_completed(ctx, "待機台訊息格式", message_format)

    @message_group.command(name="notify")
    async def set_notify_string_format(self,  ctx: commands.Context, message_format: str, need_embed: bool=True):
        """
        可使用的標籤：{title}, {channel_name}, {url}, {mention}, {description}, {new_line}, {chat_channel}
        """
        await self.config.guild(ctx.guild).notify_message_format.set(message_format)
        await self.config.guild(ctx.guild).notify_embed_enable.set(need_embed)
        await Send.set_up_completed(ctx, "開播通知訊息格式", message_format)

    @message_group.command(name="notify_collab")
    async def set_notify_collab_string_format(self,  ctx: commands.Context, message_format: str):
        """
        可使用的標籤：{mention}, {chat_channel}
        """
        await self.config.guild(ctx.guild).collab_notify_message_format.set(message_format)
        await Send.set_up_completed(ctx, "聯動開播通知訊息格式", message_format)
        
    @message_group.command(name="info_channel")
    async def set_info_channel(self,  ctx: commands.Context, text_channel: discord.TextChannel):
        await self.config.guild(ctx.guild).info_text_channel.set(text_channel.id)
        await Send.set_up_completed(ctx, "傳送訊息的頻道", text_channel)

    async def get_info_channel(self, guild):
        info_text_channel_id = await self.config.guild(guild).info_text_channel()
        return get_text_channel(guild, info_text_channel_id)
        
    # async def get_start_channel(self, guild:discord.Guild):
    #     return await self.config.guild(guild).stream_start_message_format.get()

    async def check(self):
        for guild_id, guild_manager in self.manager.streams_manager.guild_managers.items():
            guild = self.bot.get_guild(guild_id)
            for guild_collab_stream in guild_manager.guild_collab_streams.values():
                # from .streams import StreamStatus
                if not guild_collab_stream._info_update:
                    continue
                if guild_collab_stream._status in [StreamStatus.UPCOMING, StreamStatus.LIVE]:
                    await self.send_standby(guild, guild_collab_stream)
                if guild_collab_stream._status in [StreamStatus.LIVE]:
                    await self.send_notify(guild, guild_collab_stream)
                guild_collab_stream._info_update = False

    async def send_standby(self, guild: discord.Guild, guild_collab_stream: "GuildCollabStream") -> None:
        # 可發送多則，但修改只會修改第一則
        standby_text_channel = guild_collab_stream.standby_text_channel
        if not guild_collab_stream.standby_msg_enable or not standby_text_channel:
            return
            
        # get discord message
        standby_msg = await get_message(standby_text_channel, guild_collab_stream.standby_msg_id)
        
        # get send data
        msg_format = await self.config.guild(guild).standby_message_format()
        
        # get message content
        msgs = guild_collab_stream.get_standby_msg(msg_format)
        if standby_msg:
            await standby_msg.edit(content=msgs[0])
        else:
            # 發送第一則 (id 要保留)
            standby_msg = await standby_text_channel.send(
                content=msgs[0], allowed_mentions=discord.AllowedMentions(roles=True)
            )
            # 發送其後的
            for i in range(1, len(msgs)):
                await standby_text_channel.send(content=msgs[i])
            guild_collab_stream.standby_msg_id = standby_msg.id
            await guild_collab_stream._saved_func()
        # elif not guild_collab_stream.standby_msg_id:
        #     await self.update_standby_msg(guild_collab_stream)

    def get_collab_notify_msg(self, member: "Member", message_format: str, chat_channel: discord.TextChannel) -> str:
        message_format = message_format.replace("{mention}", get_roles_str(chat_channel.guild, member.mention_roles))
        message_format = message_format.replace("{chat_channel}", chat_channel.mention)
        return message_format

    async def send_notify(self, guild: discord.Guild, guild_collab_stream: "GuildCollabStream") -> None:
        saved_func = None
        for guild_stream in guild_collab_stream._guild_streams.values():
            if not guild_stream.notify_msg_enable or not guild_stream.notify_text_channel:
                continue

            notify_text_channel = guild_stream.notify_text_channel
            standby_text_channel = guild_collab_stream.standby_text_channel
            
            # get discord message
            notify_msg = await get_message(notify_text_channel, guild_stream.notify_msg_id)
            
            # get send data
            stream_start_msg_format = await self.config.guild(guild).notify_message_format()
            collab_start_msg_format = await self.config.guild(guild).collab_notify_message_format()
            need_embed = await self.config.guild(guild).notify_embed_enable()
            
            # get message content
            if guild_stream._stream._status == StreamStatus.LIVE:
                msg, embed = guild_stream.get_notify_msg(stream_start_msg_format, need_embed, standby_text_channel)
                if guild_stream.member_name not in guild_collab_stream.notify_sent_member_names:
                    guild_collab_stream.notify_sent_member_names.append(guild_stream.member_name)

                if notify_msg:
                    await notify_msg.edit(content=msg, embed=embed)
                else:
                    notify_msg = await notify_text_channel.send(
                        content=msg, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True)
                    )
                    guild_stream.notify_msg_id = notify_msg.id
                    saved_func = guild_stream._saved_func
            # elif not guild_collab_stream.standby_msg_id:
            #     await self.update_standby_msg(guild_collab_stream)
        # 聯動中其他尚未開台的也會收到通知
        for member in guild_collab_stream._members:
            if member.name not in guild_collab_stream.notify_sent_member_names:
                guild_collab_stream.notify_sent_member_names.append(guild_stream.member_name)
                msg = self.get_collab_notify_msg(member, collab_start_msg_format, standby_text_channel)
                notify_msg = await notify_text_channel.send(
                    content=msg, allowed_mentions=discord.AllowedMentions(roles=True)
                )

        if saved_func:
            await saved_func()
        await guild_collab_stream._saved_func()