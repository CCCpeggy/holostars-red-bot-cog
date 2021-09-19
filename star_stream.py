import discord
from discord.utils import get

from redbot.core.bot import Red
from redbot.core import checks, commands, Config
from redbot.core.i18n import cog_i18n, Translator, set_contextual_locales_from_guild
from redbot.core.utils._internal_utils import send_to_owners_with_prefix_replaced
from redbot.core.utils.chat_formatting import escape, pagify
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils.mod import is_mod_or_superior
from redbot.core.utils import AsyncIter
from .youtube_stream import YouTubeStream, get_video_belong_channel
from .scheduled_stream import ScheduledStream
from .temprole import TempRole

from .errors import (
    APIError,
    InvalidYoutubeCredentials,
    OfflineStream,
    StreamNotFound,
    StreamsError,
    YoutubeQuotaExceeded,
)

from .errors import (
    WrongDateFormat,
    WrongChannelName,
    NoDate,
    NoChannelName,
    FutureDate,
    PassDate,
    ModRefused,
    ReactionTimeout,
    ServerError,
    NotFound,
)

import re
import json
import time
import emoji
import logging
import asyncio
import aiohttp
import contextlib
import subprocess
from io import BytesIO
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse as parse_time
from dateutil import relativedelta
from typing import Optional, List, Tuple, Union, Dict, MutableMapping

_ = Translator("StarStreams", __file__)
log = logging.getLogger("red.core.cogs.StarStreams")
next_message = r'{next_message}'

youtube_url_format_2 = "https://www.youtube.com/watch?v={}"
youtube_url_format_3 = "https://youtu.be/{}"


@cog_i18n(_)
class StarStream(commands.Cog):
    """Streaming bot for Holostars Chinese Fan Server.

    It will check YouTube stream and send notification.
    """

    global_defaults = {
        "refresh_timer": 100000,
        "tokens": {},
        "streams": [],
        "scheduled_streams": [],
    }

    guild_defaults = {
        "autodelete": False,
        "mention_everyone": False,
        "mention_here": False,
        "chat_message": None,
        "mention_message": None,
        "scheduled_message": None,
        "collab_mention_message": None,

        # 會員審核
        "membership_input_channel_id": None,
        "membership_result_channel_id": None,
        "membership_command_channel_id": None,
        "membership_names": [],
        "membership_roles": [],
        "membership_text_channel_ids": [],
        "membership_enable": False,
    }

    def __init__(self, bot: Red, temp_role: TempRole = None):
        super().__init__()
        self.config: Config = Config.get_conf(self, 27272727)
        self.config.register_global(**self.global_defaults)
        self.config.register_guild(**self.guild_defaults)
        self.temp_role = temp_role

        self.bot: Red = bot

        self.streams: List[Stream] = []
        self.task: Optional[asyncio.Task] = None

        self._ready_event: asyncio.Event = asyncio.Event()
        self._init_task: asyncio.Task = self.bot.loop.create_task(
            self.initialize())
        self._youtube_video_re = re.compile(
            r"https?://(www.youtube.com/watch\?v=|youtube.com/watch\?v=|m.youtube.com/watch\?v=|youtu.be/)([0-9A-Za-z_-]{10}[048AEIMQUYcgkosw])")

    async def red_delete_data_for_user(self, **kwargs):
        """ Nothing to delete """
        return

    def check_name_or_id(self, data: str) -> bool:
        channel_id_re = re.compile("^UC[-_A-Za-z0-9]{21}[AQgw]$")
        matched = channel_id_re.fullmatch(data)
        if matched is None:
            return True
        return False

    async def initialize(self) -> None:
        """Should be called straight after cog instantiation."""
        await self.bot.wait_until_ready()

        try:
            await self.move_api_keys()
            self.streams = await self.load_streams()
            self.scheduled_streams = await self.load_scheduled_streams()
            self.task = self.bot.loop.create_task(self._stream_alerts())
        except Exception as error:
            log.exception("Failed to initialize Streams cog:", exc_info=error)

        self._ready_event.set()

    async def cog_before_invoke(self, ctx: commands.Context):
        await self._ready_event.wait()

    async def move_api_keys(self) -> None:
        """Move the API keys from cog stored config to core bot config if they exist."""
        tokens = await self.config.tokens()
        youtube = await self.bot.get_shared_api_tokens("youtube")
        for token_type, token in tokens.items():
            if "api_key" not in youtube:
                await self.bot.set_shared_api_tokens("youtube", api_key=token)
        await self.config.tokens.clear()

    @commands.group()
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def stars(self, ctx: commands.Context):
        """Manage holostars discord server."""
        pass

    @stars.group(name='channel')
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def _stars_channel(self, ctx: commands.Context):
        """Manage members' channel settings."""
        pass

    @_stars_channel.command(name="set")
    async def _channel_set(self, ctx: commands.Context, channel_name_or_id: str, mention_channel: discord.TextChannel = None, chat_channel: discord.TextChannel = None, channel_emoji: str = None):
        """Set tracking YouTube channel.

        Use: [p]stars channel set [YT channel id | YT channel name] [mention channel] [default chat channel] [emoji]
        """
        # if str(_emoji) == emoji for _emoji in message.guild.emojis:
        if channel_emoji:
            def get_emoji_name(word):
                if word in emoji.UNICODE_EMOJI['en']:
                    return word
                elif word in [str(e) for e in ctx.guild.emojis]:
                    for e in ctx.guild.emojis:
                        if word == str(e):
                            return e.name
                return None
            channel_emoji = get_emoji_name(channel_emoji)
            if not channel_emoji:
                await ctx.send("Emoji is not corrent")
                return
        stream = self.get_stream(channel_name_or_id)
        chat_channel_id = chat_channel.id if chat_channel else None
        mention_channel_id = mention_channel.id if mention_channel else None
        if not stream:
            token = await self.bot.get_shared_api_tokens(YouTubeStream.token_name)
            if not self.check_name_or_id(channel_name_or_id):
                stream = YouTubeStream(
                    _bot=self.bot, id=channel_name_or_id, token=token, config=self.config, chat_channel_id=chat_channel_id, mention_channel_id=mention_channel_id, emoji=channel_emoji
                )
            else:
                stream = YouTubeStream(
                    _bot=self.bot, name=channel_name_or_id, token=token, config=self.config, chat_channel_id=chat_channel_id, mention_channel_id=mention_channel_id, emoji=channel_emoji
                )
            try:
                exists = await stream.check_exists()
            except InvalidYoutubeCredentials:
                await ctx.send(
                    _(
                        "The YouTube API key is either invalid or has not been set. See "
                        "{command}."
                    ).format(command=f"`{ctx.clean_prefix}streamset youtubekey`")
                )
                return
            except YoutubeQuotaExceeded:
                await ctx.send(
                    _(
                        "YouTube quota has been exceeded."
                        " Try again later or contact the owner if this continues."
                    )
                )
            except APIError as e:
                log.error(
                    "Something went wrong whilst trying to contact the stream service's API.\n"
                    "Raw response data:\n%r",
                    e,
                )
                await ctx.send(
                    _("Something went wrong whilst trying to contact the stream service's API.")
                )
                return
            else:
                if not exists:
                    await ctx.send(_("That channel doesn't seem to exist."))
                    return
                # add stream
                self.streams.append(stream)
                await ctx.send(
                    _(
                        "I'll now send a notification in this channel when {stream.name} is live."
                    ).format(stream=stream)
                )

        else:
            # update stream
            self.streams.remove(stream)
            if chat_channel:
                stream.chat_channel_id = chat_channel_id
            if mention_channel:
                stream.mention_channel_id = mention_channel_id
            stream.emoji = channel_emoji
            self.streams.append(stream)
            await ctx.send(
                _(
                    "I have already updated {stream.name} settings."
                ).format(stream=stream)
            )

        await self.save_streams()

    @_stars_channel.command(name="unset")
    async def _channel_unset(self, ctx: commands.Context, channel_name_or_id_or_all: str):
        """Unset tracking YouTube channel.

        Use: [p]stars channel unset [YT channel id | YT channel name | all]
        """
        async def send_remove_message(stream):
            await ctx.send(
                f"I won't send notifications about {stream.name} in this channel anymore."
            )
        try:   
            if channel_name_or_id_or_all == "all":
                for stream in self.streams:
                    await send_remove_message(stream)
                self.streams = []
            else:
                stream = self.get_stream(channel_name_or_id_or_all)
                if not stream:
                    raise NotFound
                self.streams.remove(stream)
                await send_remove_message(stream)
            await self.save_streams()
        except NotFound:
            await ctx.send(f"在設定中找不到 `{channel_name_or_id_or_all}` 對應的頻道")

    @_stars_channel.command(name="list")
    async def _stars_channel_list(self, ctx: commands.Context):
        """List all active stream alerts in this server."""
        streams_list = defaultdict(list)
        guild_channels_ids = [c.id for c in ctx.guild.channels]
        msg = _("Active alerts:\n\n")

        if len(self.streams) == 0:
            await ctx.send(_("There are no active alerts in this server."))
            return

        for stream in self.streams:
            msg += f"**{stream.name}**\n"
            if stream.mention_channel_id:
                msg += f" - mention channel: `#{ctx.guild.get_channel(stream.mention_channel_id)}`\n"
            if stream.chat_channel_id:
                msg += f" - chat channel: `#{ctx.guild.get_channel(stream.chat_channel_id)}`\n"
            if len(stream.mention) > 0:
                roles_str = ', '.join(
                    [f'`@{get(ctx.guild.roles, id=role_id).name}`' for role_id in stream.mention])
                msg += f" - mention roles: {roles_str}\n"
            if stream.emoji:
                emoji = self.getEmoji(ctx, stream.emoji)
                msg += f" - representative emoji: {emoji}\n"

        for page in pagify(msg):
            await ctx.send(page)

    @stars.group(name='set')
    @checks.mod_or_permissions(manage_channels=True)
    async def starsset(self, ctx: commands.Context):
        """Manage stream alert settings."""
        pass

    @starsset.command(name="timer")
    @checks.is_owner()
    async def _starsset_refresh_timer(self, ctx: commands.Context, refresh_time: int):
        """Set stream check refresh time."""
        if refresh_time < 60:
            return await ctx.send(_("You cannot set the refresh timer to less than 60 seconds"))

        await self.config.refresh_timer.set(refresh_time)
        await ctx.send(
            _("Refresh timer set to {refresh_time} seconds".format(
                refresh_time=refresh_time))
        )

    @starsset.command()
    @checks.is_owner()
    async def youtubekey(self, ctx: commands.Context):
        """Explain how to set the YouTube token."""

        message = _(
            "To get one, do the following:\n"
            "1. Create a project\n"
            "(see https://support.google.com/googleapi/answer/6251787 for details)\n"
            "2. Enable the YouTube Data API v3 \n"
            "(see https://support.google.com/googleapi/answer/6158841 for instructions)\n"
            "3. Set up your API key \n"
            "(see https://support.google.com/googleapi/answer/6158862 for instructions)\n"
            "4. Copy your API key and run the command "
            "{command}\n\n"
            "Note: These tokens are sensitive and should only be used in a private channel\n"
            "or in DM with the bot.\n"
        ).format(
            command="`{}set api youtube api_key {}`".format(
                ctx.clean_prefix, _("<your_api_key_here>")
            )
        )

        await ctx.maybe_send_embed(message)

    @_stars_channel.command(name="mention")
    async def _stars_mention(self, ctx: commands.Context, yt_channel_id_or_name: str, role: discord.Role):
        """Set mention role in each channel
        Use stars mention [channel id | channel name] [role]
        """
        stream = self.get_stream(yt_channel_id_or_name)
        if not stream:
            await ctx.send(f"`{yt_channel_id_or_name}` is not found")
            return
        if role.id not in stream.mention:
            stream.mention.append(role.id)
        else:
            stream.mention.remove(role.id)

        if len(stream.mention) > 0:
            await ctx.send(
                _(
                    f'I will send mention `{", ".join([get(ctx.guild.roles, id=role_id).name for role_id in stream.mention])}`.'
                )
            )
        else:
            await ctx.send(
                _(
                    "No mention role in this channel."
                ).format(stream=stream)
            )
        await self.save_streams()

    @stars.group(name="stream")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def _stars_stream(self, ctx: commands.Context):
        """Mange stream
        """

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

    @_stars_stream.command(name="set")
    async def _stream_set(self, ctx: commands.Context, chat_channel: discord.TextChannel, stream_time: str, description=None, change_channel_name: bool = True):
        token = await self.bot.get_shared_api_tokens(YouTubeStream.token_name)
        scheduled_stream = ScheduledStream(
            _bot=self.bot, token=token, config=self.config,
            text_channel_id=chat_channel.id,
            description=description,
            time=datetime_plus_8_to_0_isoformat(stream_time),
            change_channel_name=change_channel_name
        )
        message = await ctx.send("請選擇連動人員，選擇完畢後請按\N{WHITE HEAVY CHECK MARK}，取消請按\N{NEGATIVE SQUARED CROSS MARK}")
        emojis = {
            "\N{WHITE HEAVY CHECK MARK}": "Done",
            "\N{NEGATIVE SQUARED CROSS MARK}": "Cancel"
        }
        selected = {}
        for stream in self.streams:
            if not stream.emoji:
                continue
            new_emoji = self.getEmoji(ctx, stream.emoji)
            if not new_emoji:
                log.warning("not found emoji" + new_emoji)
                continue
            emojis[new_emoji] = stream
            selected[new_emoji] = False
        emojis_list = list(emojis.keys())
        # log.info(emojis.keys())

        async def add_reaction():
            with contextlib.suppress(discord.NotFound):
                for emoji in emojis.keys():
                    await message.add_reaction(emoji)

        task = asyncio.create_task(add_reaction())
        # # await add_reaction()
        try:
            async def reaction_task(event):
                nonlocal selected
                while True:
                    r, u = await self.bot.wait_for(
                        event, check=ReactionPredicate.with_emojis(
                            emojis_list, message, ctx.author)
                    )
                    if emojis[r.emoji] == "Done":
                        break
                    elif emojis[r.emoji] == "Cancel":
                        selected = {}
                        break
                    else:
                        selected[r.emoji] = not selected[r.emoji]
            tasks = [
                asyncio.create_task(reaction_task('reaction_remove')),
                asyncio.create_task(reaction_task('reaction_add'))
            ]
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=30)
            for task in tasks:
                if task is not None:
                    task.cancel()
        except asyncio.TimeoutError:
            pass
        await self._clear_react(message, emojis_list)

        if task is not None:
            task.cancel()

        selected = {k: v for k, v in selected.items() if v}
        for emoji in selected.keys():
            stream = emojis[emoji]
            scheduled_stream.add_collab(stream.id, stream.name)

        if selected != {}:
            for old_scheduled_stream in {v for v in self.scheduled_streams if scheduled_stream.text_channel_id == chat_channel.id}:
                self.scheduled_streams.remove(old_scheduled_stream)
            self.scheduled_streams.append(scheduled_stream)
            await ctx.send(f"#{chat_channel.name} 已設置直播，直播者有：{', '.join(scheduled_stream.channel_names)}")
            await self.save_scheduled_streams()

    @_stars_stream.command(name="add")
    async def _stream_add(self, ctx: commands.Context, video_id: str, chat_channel: discord.TextChannel = None):
        """ Add stream
        If not assign **chat channel**, it will set by yotube channel settings.
        Use: [p]stars stream add [YT video id] <[chat channel]>
        """
        token = await self.bot.get_shared_api_tokens(YouTubeStream.token_name)
        yt_channel_id = await get_video_belong_channel(token, video_id)
        if yt_channel_id:
            stream = self.get_stream(yt_channel_id)
            if stream:
                if video_id not in stream.livestreams:
                    stream.livestreams.append(video_id)
                    await self.save_streams()
                await ctx.send(f"新增 {video_id}` 到 {stream.name}` 追蹤的直播，開播將會通知")
            else:
                await ctx.send(f"沒有設置 `{yt_channel_id}` 的頻道")
        else:
            await ctx.send(f"沒有找到 `{video_id}`.")

        if chat_channel:
            scheduled_stream = self.get_scheduled_stream(
                text_channel_id=chat_channel.id)
            if scheduled_stream:
                if stream.id in scheduled_stream.channel_ids:
                    idx = scheduled_stream.channel_ids.index(stream.id)
                    scheduled_stream.video_ids[idx] = video_id
                else:
                    await ctx.send(f"{chat_channel}` 沒有設定這個頻道")
            else:
                await ctx.send(f"{chat_channel}` 沒有設定的直播")

    @_stars_stream.command(name="resend")
    async def _stream_resend(self, ctx: commands.Context, video_id: str):
        """ 重新發送通知
        不管之前是否發送過訊息，當下次偵測的時候，會重新發送通知
        """
        token = await self.bot.get_shared_api_tokens(YouTubeStream.token_name)
        yt_channel_id = await get_video_belong_channel(token, video_id)
        if yt_channel_id:
            stream = self.get_stream(yt_channel_id)
            if stream:
                if video_id not in stream.livestreams:
                    stream.livestreams.append(video_id)
                stream.scheduled_sent.pop(video_id, None)
                if video_id in stream.streaming_sent:
                    stream.streaming_sent.remove(video_id)
                await self.save_streams()
                await ctx.send(f"`{video_id}` 會再次發送通知")
            else:
                await ctx.send(f"沒有設置 `{yt_channel_id}` 的頻道")
        else:
            await ctx.send(f"沒有找到 `{video_id}`.")

    @stars.command(name="check")
    async def _stars_check(self, ctx: commands.Context):
        """ Force to check the status of all channels and videos
        """
        await self.check_streams()
        await ctx.send(f"I have checked the status of all channels and videos.")

    @stars.command(name="update")
    @checks.is_owner()
    async def _stars_update(self, ctx: commands.Context):
        """ 將程式碼更新
        需求：電腦需要安裝 git bash，且這個 cog 是 git 的資料夾
        更新完畢後，需要重新 reload 這個 cog
        """
        cmd = f"cd {os.path.abspath(os.getcwd())} & git pull origin master"
        # f = os.popen(cmd, "r")
        # message = f.read()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        # log.info(f"{cmd}: {message}")
        output = output.decode("utf-8") 
        error = error.decode("utf-8") 
        log.info(f"{output}{error}")
        await ctx.send(f"{output}{error}")
        try:
            if "Aborting" in error:
                raise Exception
            elif "fatal" in error:
                raise Exception
            elif "changed" in output:
                await ctx.send(f"已更新到 origin master 的最新版本，請使用 reload 重新載入程式。")
            elif "Already up to date" in output:
                await ctx.send(f"已經是最新版本了。")
            else:
                raise Exception
        except:
            await ctx.send(f"沒有更新成功，可能 `git` 設定錯誤或其他原因，詳情請確認 log 的錯誤訊息。")
        # f.close()

    async def _stream_alerts(self):
        await self.bot.wait_until_ready()
        while True:
            await self.check_streams()
            await asyncio.sleep(await self.config.refresh_timer())

    async def _send_stream_alert(
            self,
            channel: discord.TextChannel,
            embed: discord.Embed,
            content: str = None):
        if content == None:
            m = await channel.send(
                None,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(
                    roles=True, everyone=True),
            )
        else:
            content = content.split(next_message)
            m = await channel.send(
                content[0],
                embed=embed,
                allowed_mentions=discord.AllowedMentions(
                    roles=True, everyone=True),
            )
            ms = [m]
            for i in range(1, len(content)):
                if content[i] == "":
                    continue
                time.sleep(2)
                m = await channel.send(
                    content[i],
                    allowed_mentions=discord.AllowedMentions(
                        roles=True, everyone=True),
                )
                ms.append(m)
            return ms

    @stars.group()
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def message(self, ctx: commands.Context):
        """Manage custom messages for stream alerts."""
        pass

    @message.command(name='chat')
    async def _message_chat(self, ctx: commands.Context, *, message: str):
        guild = ctx.guild
        await self.config.guild(guild).chat_message.set(message)
        await ctx.send(_("Stream alert message set!"))

    @message.command(name='mention')
    async def _message_mention(self, ctx: commands.Context, *, message: str):
        guild = ctx.guild
        await self.config.guild(guild).mention_message.set(message)
        await ctx.send(_("Stream alert message set!"))

    @message.command(name='scheduled')
    async def _message_schduled(self, ctx: commands.Context, *, message: str):
        guild = ctx.guild
        await self.config.guild(guild).scheduled_message.set(message)
        await ctx.send(_("Stream alert message set!"))

    @message.command(name='collab_mention')
    async def _message_collab_mention(self, ctx: commands.Context, *, message: str):
        guild = ctx.guild
        await self.config.guild(guild).collab_mention_message.set(message)
        await ctx.send(_("Stream alert message set!"))

    @stars.command()
    @commands.guild_only()
    @checks.is_owner()
    async def settings(self, ctx: commands.Context):
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
        # log.info(await self.config.get_raw())

    async def check_streams(self):
        for stream in self.streams:
            try:
                try:
                    scheduled_datas, streaming_data = await stream.is_online()
                except StreamNotFound:
                    log.info("Stream with name %s no longer exists", stream.name)
                    continue
                except OfflineStream:
                    stream.messages.clear()
                    stream.scheduled_sent.clear()
                    stream.streaming_sent.clear()
                    stream.livestreams.clear()
                    continue
                except APIError as e:
                    log.error(
                        "Something went wrong whilst trying to contact the stream service's API.\n"
                        "Raw response data:\n%r",
                        e,
                    )
                    continue
                else:
                    # alert_msg = await self.config.guild(channel.guild).live_message_mention()

                    sent_channel_ids = []
                    for scheduled_data in scheduled_datas:
                        log.info(YouTubeStream.get_info(scheduled_data)["video_id"])
                        if scheduled_data:
                            sent_channel_id = await self.process_scheduled_data(stream, scheduled_data, sent_channel_ids)
                            if sent_channel_id:
                                sent_channel_ids.append(sent_channel_id)

                    if streaming_data:
                        await self.process_streaming_data(stream, streaming_data)

            except Exception as e:
                log.error(
                    "An error has occured with Streams. Please report it.", exc_info=e)
        await self.save_streams()
        await self.save_scheduled_streams()

    async def process_scheduled_data(self, stream, scheduled_data, sent_channel_ids):
        info = YouTubeStream.get_info(scheduled_data)
        scheduled_stream = self.get_scheduled_stream(
            yt_channel_id=info["channel_id"],
            time=info["time"],
            video_ids=[info["video_id"], ""]
        )
        # 有設定直播
        if scheduled_stream:
            send_channel_id = scheduled_stream.text_channel_id
            idx = scheduled_stream.channel_ids.index(info["channel_id"])
            scheduled_stream.video_ids[idx] = info["video_id"]
        # 沒有設定直播
        else:
            send_channel_id = stream.chat_channel_id

        send_channel = self.bot.get_channel(send_channel_id)
        # 此文字頻道發送過通知則不再發送
        if send_channel_id in sent_channel_ids and not scheduled_stream:
            # 如果原本已經發送，則刪除原訊息
            if info["video_id"] in stream.scheduled_sent:
                message_id = stream.scheduled_sent[info["video_id"]]
                if message_id:
                    message = await self.get_message(send_channel, message_id)
                    if message:
                        await message.delete()
                    stream.scheduled_sent.pop(info["video_id"])
            return None

        # 預定直播已經送過了
        # if scheduled_stream and scheduled_stream.message_id:
        #     if await self.get_message(send_channel, scheduled_stream.message_id):
        #         return send_channel_id
        # 自動偵測直播已經送過了
        if info["video_id"] in stream.scheduled_sent: # TODO
            if await self.get_message(send_channel, stream.scheduled_sent[info["video_id"]]):
                return send_channel_id
            chat_channel = self.bot.get_channel(stream.chat_channel_id)
            if await self.get_message(chat_channel, stream.scheduled_sent[info["video_id"]]):
                return send_channel_id

        scheduled_message = await self.config.guild(send_channel.guild).scheduled_message()
        message = await self.send_scheduled(
            send_channel_id, pin=True, content=scheduled_message,
            info=info, scheduled_stream=scheduled_stream
        )
        stream.scheduled_sent[info["video_id"]] = message.id
        return send_channel_id

    async def process_streaming_data(self, stream, streaming_data):
        info = YouTubeStream.get_info(streaming_data)
        scheduled_stream = self.get_scheduled_stream(
            yt_channel_id=info["channel_id"],
            time=info["time"],
            video_ids=[info["video_id"], ""]
        )
        if info["video_id"] in stream.streaming_sent:
            return False
        mention_channel = self.bot.get_channel(stream.mention_channel_id)
        mention_message = await self.config.guild(mention_channel.guild).mention_message()
        chat_channel_id = scheduled_stream.text_channel_id if scheduled_stream else stream.chat_channel_id
        # 一般開播通知
        if stream.mention_channel_id:
            await self.send_streaming(
                streaming_data, stream.mention_channel_id,
                is_mention=True, embed=True,
                chat_channel_id=chat_channel_id,
                content=mention_message,
                scheduled_stream=scheduled_stream,
            )
        # 連動直播第一個開播發其他人的開播通知
        if scheduled_stream and not scheduled_stream.streaming_sent:
            collab_mention_message = await self.config.guild(mention_channel.guild).collab_mention_message()
            for yt_channel_id in scheduled_stream.channel_ids: 
                if yt_channel_id == stream.id:
                    continue
                await self.send_streaming(
                    streaming_data,
                    self.get_stream(yt_channel_id).mention_channel_id,
                    is_mention=True, embed=True,
                    chat_channel_id=chat_channel_id,
                    content=collab_mention_message,
                    scheduled_stream=scheduled_stream,
                    yt_channel_id=yt_channel_id
                )
        # 聊天室開播訊息
        if scheduled_stream and scheduled_stream.streaming_sent:
            pass
        elif chat_channel_id:
            chat_channel = self.bot.get_channel(stream.chat_channel_id)
            chat_message = await self.config.guild(chat_channel.guild).chat_message()
            await self.send_streaming(
                streaming_data, chat_channel_id,
                is_mention=False, embed=False,
                content=chat_message
            )
        stream.streaming_sent.append(info["video_id"])
        if scheduled_stream:
            scheduled_stream.streaming_sent = True
        
    async def send_scheduled(self, channel_id, info=None, pin=False, scheduled_stream=None, content="{time}\n{description}\n{url}"):
        channel = self.bot.get_channel(channel_id)
        if not channel or await self.bot.cog_disabled_in_guild(self, channel.guild):
            return

        content = content.replace("{new_line}", "\n")
        content = content.replace("{title}", info["title"])

        if scheduled_stream:
            content = content.replace("{description}",
                scheduled_stream.description if scheduled_stream.description else info["title"]
            )
            scheduled_stream.description = info["title"]
            content = content.replace("{channel_name}", ", ".join(scheduled_stream.channel_names))
            content = content.replace("{time}", getDiscordTimeStamp(scheduled_stream.get_time()))
            url = ""
            for i in range(len(scheduled_stream.channel_ids)):
                if scheduled_stream.video_ids[i] != "":
                    yt_url = youtube_url_format_2.format(
                        scheduled_stream.video_ids[i])
                    url += f"{scheduled_stream.channel_names[i]}:\n{yt_url}\n"
            content = content.replace("{url}", url)

            # 改頻道名稱
            if scheduled_stream.change_channel_name:
                emojis = [self.getEmoji(channel, stream.emoji)
                          for stream in self.streams if stream.id in scheduled_stream.channel_ids]
                emojis = [f'{e}' for e in emojis if e]
                await channel.edit(name=f"連動頻道{''.join(emojis)}")
        else:
            content = content.replace("{channel_name}", info["channel_name"])
            content = content.replace("{description}", info["title"])
            content = content.replace("{url}", youtube_url_format_2.format(info["video_id"]))
            if info["time"]:
                content = content.replace("{time}", getDiscordTimeStamp(info["time"]))

        if scheduled_stream and scheduled_stream.message_id:
            ms = await self.get_message(channel, scheduled_stream.message_id)
            if ms:
                await ms.edit(content=content)
                return ms
        ms = await self._send_stream_alert(channel, None, content)
        if pin:
            await ms[0].pin()
        if scheduled_stream:
            scheduled_stream.message_id = ms[0].id
        return ms[0]

    async def send_streaming(
        self, data, channel_id, is_mention, content="{url}", embed=False, pin=False, chat_channel_id=None, scheduled_stream=None, yt_channel_id=None
    ):
        channel = self.bot.get_channel(channel_id)
        if not channel or await self.bot.cog_disabled_in_guild(self, channel.guild):
            return
        embed = YouTubeStream.make_embed(data) if embed else None
        info = YouTubeStream.get_info(data)

        # 取代字串
        content = content.replace("{channel_name}", info["channel_name"])
        content = content.replace("{url}", youtube_url_format_2.format(info["video_id"]))
        if scheduled_stream:# and scheduled_stream.description:
            content = content.replace("{description}", scheduled_stream.description)
        else:
            content = content.replace("{description}", info["title"])
        content = content.replace("{title}", info["title"])
        content = content.replace("{new_line}", "\n")
        if chat_channel_id:
            chat_channel = self.bot.get_channel(chat_channel_id)
            if chat_channel:
                content = content.replace("{chat_channel}", chat_channel.mention)
        if not yt_channel_id:
            yt_channel_id = info["channel_id"]
        mention_str, edited_roles = (await self._get_mention_str(
            channel.guild, channel, [yt_channel_id]
        )) if is_mention else ("", [])
        content = content.replace("{mention}", mention_str)
    
        ms = await self._send_stream_alert(channel, embed, content)
        if pin:
            await ms[0].pin()

    async def get_message(self, channel, message_id):
        try:
            message = await channel.fetch_message(message_id)
        except:
            return False
        else:
            return message

    async def _get_mention_str(
        self, guild: discord.Guild, channel: discord.TextChannel, ch_ids: list
    ) -> Tuple[str, List[discord.Role]]:
        """Returns a 2-tuple with the string containing the mentions, and a list of
        all roles which need to have their `mentionable` property set back to False.
        """
        settings = self.config.guild(guild)
        mentions = []
        edited_roles = []
        if await settings.mention_everyone():
            mentions.append("@everyone")
        if await settings.mention_here():
            mentions.append("@here")

        can_mention_everyone = channel.permissions_for(
            guild.me).mention_everyone
        role_ids = []
        for ch_id in ch_ids:
            role_ids += self.get_stream(ch_id).mention
        role_ids = list(set(role_ids))
        for role_id in role_ids:
            role = get(guild.roles, id=role_id)
            if not can_mention_everyone and not role.mentionable:
                try:
                    await role.edit(mentionable=True)
                except discord.Forbidden:
                    # Might still be unable to edit role based on hierarchy
                    pass
                else:
                    edited_roles.append(role)
            mentions.append(role.mention)
        return " ".join(mentions), edited_roles

    async def load_streams(self):
        streams = []
        for raw_stream in await self.config.streams():
            token = await self.bot.get_shared_api_tokens(YouTubeStream.token_name)
            if token:
                raw_stream["config"] = self.config
                raw_stream["token"] = token
            raw_stream["_bot"] = self.bot
            streams.append(YouTubeStream(**raw_stream))

        return streams

    async def load_scheduled_streams(self):
        scheduled_streams = []
        for raw_stream in await self.config.scheduled_streams():
            token = await self.bot.get_shared_api_tokens(YouTubeStream.token_name)
            if token:
                raw_stream["config"] = self.config
                raw_stream["token"] = token
            raw_stream["_bot"] = self.bot
            scheduled_streams.append(ScheduledStream(**raw_stream))

        return scheduled_streams

    async def save_streams(self):
        raw_streams = []
        for stream in self.streams:
            raw_streams.append(stream.export())
        await self.config.streams.set(raw_streams)

    async def save_scheduled_streams(self):
        raw_scheduled_streams = []
        for stream in self.scheduled_streams:
            raw_scheduled_streams.append(stream.export())

        await self.config.scheduled_streams.set(raw_scheduled_streams)

    def cog_unload(self):
        if self.task:
            self.task.cancel()

    def get_stream(self, name):
        for stream in self.streams:
            if self.check_name_or_id(name) and stream.name.lower() == name.lower():
                return stream
            elif not self.check_name_or_id(name) and stream.id == name:
                return stream
        return None

    def get_scheduled_stream(self, text_channel_id=None, yt_channel_id=None, video_ids=None, time=None):
        for scheduled_stream in self.scheduled_streams:
            if text_channel_id and text_channel_id != scheduled_stream.text_channel_id:
                continue

            if yt_channel_id and yt_channel_id not in scheduled_stream.channel_ids:
                continue
            elif video_ids:
                idx = scheduled_stream.channel_ids.index(yt_channel_id)
                video_id = scheduled_stream.video_ids[idx]
                if video_id not in video_ids:
                    continue
                if video_id != "":
                    return scheduled_stream

            if time:
                shared_scheduled_time = getTimeStamp(
                    scheduled_stream.get_time())
                search_scheduled_time = getTimeStamp(time)
                diff = abs(shared_scheduled_time - search_scheduled_time)
                if not (diff < 1800):
                    continue
            return scheduled_stream
        return None

    def getEmoji(self, ctx, in_emoji):
        for e in ctx.guild.emojis:
            if in_emoji == e.name:
                return e
        if in_emoji in emoji.UNICODE_EMOJI['en']:
            return in_emoji
        return None

    # 會員審核
    @stars.group(name='membership')
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def _stars_membership(self, ctx: commands.Context):
        """會員審核設定"""
        pass

    @_stars_membership.command(name='enable')
    async def _stars_membership_enable(self, ctx: commands.Context):
        """啟用會員審核功能"""
        guild = ctx.guild
        await self.config.guild(guild).membership_enable.set(True)
        await ctx.send(_("已啟用會員審核"))

    @_stars_membership.command(name='disable')
    async def _stars_membership_disable(self, ctx: commands.Context):
        """禁用會員審核功能"""
        guild = ctx.guild
        await self.config.guild(guild).membership_enable.set(False)
        await ctx.send(_("已禁用會員審核"))

    @_stars_membership.command(name='input')
    async def _stars_membership_input(self, ctx: commands.Context, text_channel: discord.TextChannel = None):
        """設定使用者輸入會員資料的文字頻道"""
        guild = ctx.guild
        await self.config.guild(guild).membership_input_channel_id.set(text_channel.id)
        await ctx.send(_(f"已設定"))

    @_stars_membership.command(name='result')
    async def _stars_membership_result(self, ctx: commands.Context, text_channel: discord.TextChannel = None):
        """設定回覆使用者審核結果的文字頻道"""
        guild = ctx.guild
        await self.config.guild(guild).membership_result_channel_id.set(text_channel.id)
        await ctx.send(_(f"已設定"))

    @_stars_membership.command(name='command')
    async def _stars_membership_command(self, ctx: commands.Context, text_channel: discord.TextChannel = None):
        """設定下會員設定指令的文字頻道"""
        guild = ctx.guild
        await self.config.guild(guild).membership_command_channel_id.set(text_channel.id)
        await ctx.send(_(f"已設定"))

    @_stars_membership.command(name='role')
    async def _stars_membership_role(self, ctx: commands.Context, membership_name: str, role: discord.Role, text_channel: discord.TextChannel):
        """設定下會員所屬的名字與在頻道內對應的身分組"""
        guild = ctx.guild
        names = await self.config.guild(guild).membership_names()
        roles = await self.config.guild(guild).membership_roles()
        text_channel_ids = await self.config.guild(guild).membership_text_channel_ids()
        membership_name = membership_name.lower()
        for key_word in [" ", "channel", "ch", "."]:
            membership_name = membership_name.replace(key_word, "")
        if membership_name in names:
            idx = names.index(membership_name)
            roles[idx] = role.id
            text_channel_ids[idx] = text_channel.id
        else:
            names.append(membership_name)
            roles.append(role.id)
            text_channel_ids.append(text_channel.id)
            await self.config.guild(guild).membership_names.set(names)
        names = await self.config.guild(guild).membership_names()
        await self.config.guild(guild).membership_roles.set(roles)
        await self.config.guild(guild).membership_text_channel_ids.set(text_channel_ids)

        await ctx.send(_(f"已設定"))

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if message.content == "":
            return
        await self.audit_membership(message)

    async def audit_membership(self, message):
        if not self.config or not message or not message.guild:
            return
        if not (await self.config.guild(message.guild).membership_enable()):
            return
        # TODO: 在 initial 時設給 self
        input_channel_id = await self.config.guild(message.guild).membership_input_channel_id()
        if message.channel.id != input_channel_id:
            return
        command_channel_id = await self.config.guild(message.guild).membership_command_channel_id()
        result_channel_id = await self.config.guild(message.guild).membership_result_channel_id()
        names = await self.config.guild(message.guild).membership_names()
        roles = await self.config.guild(message.guild).membership_roles()
        text_channel_ids = await self.config.guild(message.guild).membership_text_channel_ids()
        error_name = None
        handler_msg = "此為機器人自動偵測。"
        err_msg = """請重新檢查**__YT、頻道、日期、截圖__**後重新傳送審核資料。
 有任何疑問請至 <#863343338933059594>。
 {}"""

        color=0xff0000,
        title=_("❌會員頻道權限審核未通過")
        try:
            info = get_membership_info(
                message.content, names, roles, text_channel_ids)
       
            diff = getTimeStamp(info["date"]) - \
                getTimeStamp(datetime.now(timezone.utc))
            if diff <= 0:
                raise PassDate
            if diff > 31*24*60*60:
                raise FutureDate
            reaction, mod = await self.send_reaction_check_cross(message)
            member_channel = self.bot.get_channel(info["text_channel_id"])
            if reaction == "Done":
                role = get(message.guild.roles, id=info["role"])
                await self.send_message_by_channel_id(
                    result_channel_id, f"{message.author.mention}",
                    embed=discord.Embed(
                        color=0x77b255,
                        title=_("✅會員頻道權限審核通過"),
                        description=f"""增加身分組：{role.mention}
 請確認看得見會員頻道：{member_channel.mention}
 處理人：{mod.mention}""",
                    )
                )
                # success_msg = success_msg.format(role.mention, member_channel.mention, mod.mention)
                ctx = await self.bot.get_context(message)
                channel = self.bot.get_channel(command_channel_id)
                if not channel:
                    raise ServerError
                if await self.bot.cog_disabled_in_guild(self, channel.guild):
                    raise ServerError
                await self.temp_role.add(
                    ctx, mod, channel, message.author,
                    role, timedelta(seconds=diff)
                )
                # await self.send_message_by_channel_id(command_channel_id, f"?temprole {message.author.id} {info['date']} {role}")
            elif reaction == "Cancel":
                raise ModRefused
            else:
                raise ReactionTimeout
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
            handler_msg = f"處理人：{mod.mention}"
            pass
        except ReactionTimeout:
            error_name = "管理員未在一天內審核"
        except ServerError:
            error_name = "伺服器錯誤"
            await self.send_message_by_channel_id(
                result_channel_id, f"{message.author.mention}",
                embed=discord.Embed(
                    color=0x77b255,
                    title=_("伺服器錯誤"),
                    description="""伺服器錯誤，請稍後一下""",
                )
            )
        else:
#             await self.send_message_by_channel_id(
#                 result_channel_id, f"{message.author.mention}",
#                 embed=discord.Embed(
#                     color=0x77b255,
#                     title=_("✅會員頻道權限審核通過"),
#                     description=f"""增加身分組：{role.mention}
#  請確認看得見會員頻道：{member_channel.mention}
#  處理人：{mod.mention}""",
#                 )
#             )
            return 

        err_msg = err_msg.format(handler_msg)
        if error_name:
            err_msg = f"**{error_name}**，{err_msg}"
        await self.send_message_by_channel_id(
            result_channel_id, f"{message.author.mention}",
            embed=discord.Embed(
                color=0xff0000,
                title=_("❌會員頻道權限審核未通過"),
                description= err_msg,
            )
        )
       
    async def send_message_by_channel_id(self, channel_id, msg, embed):
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
        if await self.bot.cog_disabled_in_guild(self, channel.guild):
            return
        await channel.send(msg, embed=embed)

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
        except asyncio.TimeoutError:
            return None, None
        if task is not None:
            task.cancel()
        await self._clear_react(message, emojis_list)
        return emojis[r.emoji], u


def getTimeType(date_str):
    if date_str == "":
        return datetime.now(timezone.utc)
    return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')


def getTimeStamp(date):
    return int(time.mktime(date.timetuple()))


def getDiscordTimeStamp(date):
    return "<t:{}:f>".format(getTimeStamp(date)-time.timezone)


def datetime_plus_8_to_0_isoformat(date):
    date = parse_time(date)
    timestamp = getTimeStamp(date) + time.timezone
    date = datetime.fromtimestamp(timestamp)
    return date.isoformat()


def get_membership_info(message, membership_names: List, roles: List, text_channel_ids: List):
    date = None
    idx = -1
    message = strQ2B(message).replace(" ", "")
    for s in message.split('\n'):
        tmp = s.split(':')
        if len(tmp) != 2:
            continue
        key, value = tmp
        if key == "頻道":
            value = value.lower()
            for key_word in [" ", "channel", "ch", "."]:
                value = value.replace(key_word, "")
            if value not in membership_names:
                raise WrongChannelName
            idx = membership_names.index(value)
        elif key == "日期":
            for fmt in ('%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d'):
                try:
                    date = datetime.strptime(value, fmt)
                    break
                except:
                    pass
            if not date:
                raise WrongDateFormat
    if not date:
        raise NoDate
    if idx < 0:
        raise NoChannelName
    return {
        "date": date,
        "membership_name": membership_names[idx],
        "role": roles[idx],
        "text_channel_id": text_channel_ids[idx],
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
