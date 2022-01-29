# discord
import discord

# redbot
from redbot.core.bot import Red
from redbot.core import checks, commands, Config
from redbot.core.i18n import cog_i18n, Translator

# other
import os
import logging

# local
from .utils import *

_, log = get_logger()

@cog_i18n(_)
class SendManager(commands.Cog):

    global_defaults = {
        # "refresh_timer": 100000
    }

    guild_defaults = {
        "standby_message_format": None
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

    @message_group.command(name="start")
    async def set_message_start(self,  ctx: commands.Context, message_format: str):
        """
        {time}, {title}, {channel_name}, {member_name}, {url}, {mention},
        {description}, {new_line}, {new_message}
        """
        await self.config.guild(ctx.guild).standby_message_format.set(message_format)
        await Send.set_up_completed(ctx, "待機台訊息格式", message_format)

    async def get_start_channel(self, guild:discord.Guild):
        return await self.config.guild(guild).stream_start_message_format.get()

    async def check(self):
        for guild_manager in self.manager.streams_manager.guild_managers.values():
            for guild_collab_stream in guild_manager.guild_collab_streams.values():
                from .streams import StreamStatus
                if not guild_collab_stream._info_update:
                    continue
                if guild_collab_stream._status == StreamStatus.UPCOMING \
                    or guild_collab_stream._status == StreamStatus.LIVE:
                    await self.check_upcoming_stream(guild_collab_stream)

    async def check_upcoming_stream(self, guild_collab_stream: "GuildCollabStream"):
        standby_text_channel = guild_collab_stream.standby_text_channel
        if guild_collab_stream.standby_msg_enable \
            and guild_collab_stream.standby_text_channel:
            standby_msg = await get_message(standby_text_channel, guild_collab_stream.standby_msg_id)
            if standby_msg:
                await standby_msg.edit(content=str(guild_collab_stream))
            else:
                standby_msg_id = await standby_text_channel.send(guild_collab_stream)
                guild_collab_stream.standby_msg_id = standby_msg_id
                await guild_collab_stream._saved_func()
            # elif not guild_collab_stream.standby_msg_id:
            #     await self.update_standby_msg(guild_collab_stream)
