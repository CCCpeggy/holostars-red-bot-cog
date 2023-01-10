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
        "standby_message_format": "{time}\n{title}\n{url}{next_msg}",
        "notify_message_format": "{mention}{channel_name}開播了！\n討論請至{chat_channel}",
        "collab_notify_message_format": "{mention}聯動開始了，討論請到{chat_channel}",
        "start_message_format": "!stream https://youtu.be/{video_id}{next_msg}!yt_start",
        "notify_embed_enable": True,
        "info_text_channel": None,
        "live_list_channel": None,
        "live_list_header": "直播討論頻道列表",
        "live_list_footer": "",
        "live_list_msg_id": None,
        "standby_emoji": None,
    }

    def __init__(self, bot: Red, manager: "Manager"):
        self.bot = bot
        self.manager = manager
        self.config = Config.get_conf(self, 77656984)
        self.config.register_global(**self.global_defaults)
        self.config.register_guild(**self.guild_defaults)
        self.live_list_channel = None
    
    @commands.group(name="starsset")
    @checks.mod_or_permissions(manage_channels=True)
    async def starsset_group(self, ctx: commands.Context):
        pass

    @starsset_group.command(name="standby_emoji")
    async def set_shared_standby_emoji(self,  ctx: commands.Context, emoji: EmojiConverter):
        """
        當沒有個人的 emoji 或超過 20 人時，通用的待機符號
        """
        standby_emoji = f"<:{emoji.name}:{emoji.id}>" if isinstance(emoji, discord.Emoji) else emoji
        await self.config.guild(ctx.guild).standby_emoji.set(standby_emoji)
        await Send.set_up_completed(ctx, "共用待機表情符號", standby_emoji)

    @commands.guild_only()
    @starsset_group.group(name="message")
    async def message_group(self, ctx: commands.Context):
        pass
    
    @message_group.command(name="list")
    async def get_message_list(self,  ctx: commands.Context):
        standby_message_format = await self.config.guild(ctx.guild).standby_message_format()
        notify_message_format = await self.config.guild(ctx.guild).notify_message_format()
        notify_collab_message_format = await self.config.guild(ctx.guild).collab_notify_message_format()
        notify_embed_enable = await self.config.guild(ctx.guild).notify_embed_enable()
        standby_message_format = standby_message_format.replace("\n", "{new_line}")
        notify_message_format = notify_message_format.replace("\n", "{new_line}")
        notify_collab_message_format = notify_collab_message_format.replace("\n", "{new_line}")
        data = [
            f"**待機台的訊息格式**: {standby_message_format}",
            f"**通知的訊息格式**: {notify_message_format}",
            f"**聯動開播的訊息格式**: {notify_collab_message_format}",
            f"**是否啟用通知的內嵌訊息**: {notify_embed_enable}",
        ]
        await Send.send(ctx, "\n".join(data))

    @message_group.command(name="standby")
    async def set_standby_string_format(self,  ctx: commands.Context, message_format: str):
        """
        可使用的標籤：{time}, {title}, {channel_name}, {member_name}, {url}, {mention}, {description}, {new_line}, {next_msg}
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

    @message_group.command(name="start")
    async def set_standby_string_format(self,  ctx: commands.Context, message_format: str):
        """
        可使用的標籤：{time}, {title}, {video_id}, {channel_name}, {member_name}, {url}, {mention}, {description}, {new_line}, {next_msg}
        其中 video_id 是第一個直播人的 video_id
        """
        await self.config.guild(ctx.guild).start_message_format.set(message_format)
        await Send.set_up_completed(ctx, "開播後討論區的訊息格式", message_format)
        
    @message_group.command(name="info_channel")
    async def set_info_channel(self,  ctx: commands.Context, text_channel: Union[discord.TextChannel, discord.Thread]):
        await self.config.guild(ctx.guild).info_text_channel.set(text_channel.id)
        await Send.set_up_completed(ctx, "傳送訊息的頻道", text_channel)

    @commands.guild_only()
    @starsset_group.group(name="live_list")
    async def live_list_group(self, ctx: commands.Context):
        pass     
    
    @live_list_group.command(name="text_channel")
    async def set_live_list_text_channel(self, ctx: commands.Context, text_channel: Union[discord.TextChannel, discord.Thread]):
        await self.config.guild(ctx.guild).live_list_channel.set(text_channel.id)
        await Send.set_up_completed(ctx, "直播討論頻道列表發送頻道", text_channel)
    
    @live_list_group.command(name="header")
    async def set_live_list_header(self, ctx: commands.Context, *, header: str):
        await self.config.guild(ctx.guild).live_list_header.set(header)
        await Send.set_up_completed(ctx, "直播討論頻道列表標題", header)
    
    @live_list_group.command(name="footer")
    async def set_live_list_footer(self, ctx: commands.Context, *, footer: str):
        await self.config.guild(ctx.guild).live_list_footer.set(footer)
        await Send.set_up_completed(ctx, "直播討論頻道列表註腳", footer)

    async def get_info_channel(self, guild):
        info_text_channel_id = await self.config.guild(guild).info_text_channel()
        return get_text_channel(guild, info_text_channel_id)
        
    # async def get_start_channel(self, guild:discord.Guild):
    #     return await self.config.guild(guild).stream_start_message_format.get()

    async def check(self):
        for guild_id, guild_manager in self.manager.streams_manager.guild_managers.items():
            guild = self.bot.get_guild(guild_id)

            # 尋找同頻道中最早的
            find_newest_guild_collab_stream = {}
            for guild_collab_stream in guild_manager.guild_collab_streams.values():
                if guild_collab_stream._status in [StreamStatus.UPCOMING, StreamStatus.LIVE]:
                    time = guild_collab_stream.time
                    standby_text_channel_id = guild_collab_stream._standby_text_channel_id
                    if standby_text_channel_id in find_newest_guild_collab_stream:
                        if find_newest_guild_collab_stream[standby_text_channel_id].time > time:
                            find_newest_guild_collab_stream[standby_text_channel_id] = guild_collab_stream
                    else:
                        find_newest_guild_collab_stream[standby_text_channel_id] = guild_collab_stream
            find_newest_guild_collab_stream = list(find_newest_guild_collab_stream.values())

            debug_info_need_send = []
            debug_info_no_send = []
            for guild_collab_stream in guild_manager.guild_collab_streams.values():
                need_update = guild_collab_stream._info_update
                # 發送待機台(準備直播或正在直播)
                if guild_collab_stream._status in [StreamStatus.UPCOMING, StreamStatus.LIVE]:
                    # 確定要發送的
                    if guild_collab_stream in find_newest_guild_collab_stream:
                        # 需要更新資料
                        if need_update:
                            await self.send_standby(guild, guild_collab_stream)
                            guild_collab_stream._info_update = False
                        debug_info_need_send.append(str(guild_collab_stream))
                    # 更之後的直播
                    else:
                        # 如果有更近的待機台，就刪除已發送的
                        standby_msg = await get_message(guild_collab_stream.standby_text_channel, guild_collab_stream.standby_msg_id)
                        if standby_msg:
                            await standby_msg.delete()
                            guild_collab_stream.standby_msg_id = 0
                            log.info(f"{standby_msg} 因為有更早的，所以刪掉了")
                        debug_info_no_send.append(str(guild_collab_stream))
                    await guild_collab_stream._saved_func()
                # 發送開播通知(正在直播)
                if guild_collab_stream._status in [StreamStatus.LIVE] and need_update:
                    await self.send_notify(guild, guild_collab_stream)
            log.info(f"正在待機台的：{', '.join(debug_info_need_send)}")
            log.info(f"預備待機台的：{', '.join(debug_info_no_send)}")

            await self.send_live_list(guild_manager)
    async def send_standby(self, guild: discord.Guild, guild_collab_stream: "GuildCollabStream") -> None:
        try:
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
                log.debug(f"在 {standby_text_channel.name} 中發送了 {msgs[0]}")
                await standby_msg.pin()
                
                # 發送表情符號
                try:
                    individual_emoji = False
                    if len(guild_collab_stream._members) < 20:
                        for member in guild_collab_stream._members:
                            if member.standby_emoji:
                                log.info(f"發送{member.name}的表情符號{member.standby_emoji}")
                                await standby_msg.add_reaction(member.standby_emoji)
                                individual_emoji = True
                    shared_standby_emoji = await self.config.guild(guild).standby_emoji()
                    if not individual_emoji and shared_standby_emoji:
                        log.info(f"發送整體的表情符號{shared_standby_emoji}")
                        await standby_msg.add_reaction(shared_standby_emoji)
                except Exception as e:
                    log.error("發送表情符號：" + str(e))
                
                await unpin(standby_text_channel, self.bot.user.id)
                # 發送其後的
                for i in range(1, len(msgs)):
                    if msgs[i] != "":
                        await standby_text_channel.send(content=msgs[i])
                guild_collab_stream.standby_msg_id = standby_msg.id

            # 變更頻道名字
            channel_name = guild_collab_stream.channel_name
            if channel_name == "default":
                member_emoji = ''.join([getEmoji(standby_text_channel.guild.emojis, member.emoji) for member in guild_collab_stream._members])
                channel_name = f"聯動頻道{member_emoji}"
            elif channel_name == "no":
                channel_name = None

            if channel_name:
                await standby_text_channel.edit(name=channel_name)
            
            # 開播後在討論頻道發訊息
            if not guild_collab_stream.is_send_start_msg and guild_collab_stream._status == StreamStatus.LIVE:
                msg_format = await self.config.guild(guild).start_message_format()

                # 取得 video_id
                for guild_stream in guild_collab_stream._guild_streams.values():
                    if guild_stream._stream._status == StreamStatus.LIVE:
                        msg_format = msg_format.replace("{video_id}", guild_stream.id)
                        break

                msgs = guild_collab_stream.get_standby_msg(msg_format)
                log.debug(f"在 {standby_text_channel.name} 中發送了 {msg_format}")
                for msg in msgs:
                    await standby_text_channel.send(content=msg)
                guild_collab_stream.is_send_start_msg = True

        except Exception as e:
            log.error(f"發送待機台：{e}")

    def get_collab_notify_msg(self, member: "Member", message_format: str, chat_channel: Union[discord.TextChannel, discord.Thread]) -> str:
        message_format = message_format.replace("{mention}", get_roles_str(chat_channel.guild, member.mention_roles))
        message_format = message_format.replace("{chat_channel}", chat_channel.mention)
        return message_format

    async def send_notify(self, guild: discord.Guild, guild_collab_stream: "GuildCollabStream") -> None:
        saved_func = None
        try:
            collab_start_msg_format = await self.config.guild(guild).collab_notify_message_format()
            standby_text_channel = guild_collab_stream.standby_text_channel
            for guild_stream in guild_collab_stream._guild_streams.values():
                if not guild_stream.notify_msg_enable or not guild_stream.notify_text_channel:
                    continue

                notify_text_channel = guild_stream.notify_text_channel
                
                # get discord message
                notify_msg = await get_message(notify_text_channel, guild_stream.notify_msg_id)
                
                # get send data
                stream_start_msg_format = await self.config.guild(guild).notify_message_format()
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
                        log.debug(f"在 {notify_text_channel.name} 中發送了 {msg}")
                        guild_stream.notify_msg_id = notify_msg.id
                        saved_func = guild_stream._saved_func
                # elif not guild_collab_stream.standby_msg_id:
                #     await self.update_standby_msg(guild_collab_stream)
            # 聯動中其他尚未開台的也會收到通知
            for member in guild_collab_stream._members:
                if member.name not in guild_collab_stream.notify_sent_member_names and member.notify_text_channel:
                        guild_collab_stream.notify_sent_member_names.append(member.name)
                        msg = self.get_collab_notify_msg(member, collab_start_msg_format, standby_text_channel)
                        await member.notify_text_channel.send(
                            content=msg, allowed_mentions=discord.AllowedMentions(roles=True)
                        )
        
        except Exception as e:
            log.error(f"發送通知：{e}")

        if saved_func:
            await saved_func()
        await guild_collab_stream._saved_func()

    async def send_live_list(self, guild_manager) -> None:
        guild = guild_manager.guild
        live_list_channel_id = await self.config.guild(guild).live_list_channel()

        # 判斷是否暫存過頻道，且暫存的頻道是否正確
        if self.live_list_channel is None or self.live_list_channel.id != live_list_channel_id:
            self.live_list_channel = get_text_channel(guild, live_list_channel_id)
        if self.live_list_channel is None:
            return
        
        # 取得 guild 中對應的設定
        live_list_header = await self.config.guild(guild).live_list_header()
        live_list_footer = await self.config.guild(guild).live_list_footer()
        live_list_msg_id = await self.config.guild(guild).live_list_msg_id()
        live_list_msg = await get_message(self.live_list_channel, live_list_msg_id)

        # 創造直播待機列表的 embed
        embed = discord.Embed(title=live_list_header)
        embed.set_footer(text=live_list_footer)
        embed.timestamp = Time.get_now()

        # 將 guild_collab_stream 依時間排序
        times = []
        time_to_guild_collab_stream = {}
        for i, guild_collab_stream in enumerate(guild_manager.guild_collab_streams.values()):
            if guild_collab_stream.time:
                timestamp = Time.get_total_seconds(guild_collab_stream.time)
                sort_number = timestamp * 1000 + i
                times.append(sort_number)
                time_to_guild_collab_stream[sort_number] = guild_collab_stream
        times.sort()

        # 依據時間，將待機表資訊做成 field 加入至 embed
        for timestamp in times:
            guild_collab_stream = time_to_guild_collab_stream[timestamp]
            # 沒有對應的直播或待機台訊息就不需要加入
            if len(guild_collab_stream._guild_streams.values()) == 0:
                continue
            if guild_collab_stream.standby_msg_id is None:
                continue
            try:
                member_emoji = ''.join([getEmoji(self.live_list_channel.guild.emojis, member.emoji) for member in guild_collab_stream._members if member.emoji])
                stream_title = list(guild_collab_stream._guild_streams.values())[0]._stream.title
                content = f"> <t:{timestamp // 1000}:F> / <t:{timestamp // 1000}:R>\n> "
                content += f"[待機室點我](https://discord.com/channels/{guild.id}/{guild_collab_stream.standby_text_channel.id}/{guild_collab_stream.standby_msg_id}) / "
                content += f"{guild_collab_stream.standby_text_channel.mention}"
                embed.add_field(name=f'{member_emoji}{stream_title}', value=content, inline=False)
            except Exception as e:
                log.error(f"發送直播待機列表：{e}")
        
        if live_list_msg is not None:
            await live_list_msg.edit(embed=embed)
        else:
            live_list_msg = await self.live_list_channel.send(embed=embed)
            await self.config.guild(guild).live_list_msg_id.set(live_list_msg.id)
