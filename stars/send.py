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
        "stream_start_message_format": None
    }

    def __init__(self):
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
        await self.config.guild(ctx.guild).stream_start_message_format.set(message_format)
        await Send.set_up_completed(ctx, "直播開始通知", message_format)

    async def get_start_channel(self, guild:discord.Guild):
        return await self.config.guild(guild).stream_start_message_format.get()