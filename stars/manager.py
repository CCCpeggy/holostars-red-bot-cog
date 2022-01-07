# redbot
from redbot.core.i18n import Translator
from redbot.core import checks, commands, Config

# local
from .utils import *
from .streams import StreamsManager
from .channels import ChannelsManager
from .members import MembersManager
from .send import SendManager

_, log = get_logger()

class Manager(commands.Cog):
    def __init__(self, bot: Red, **kwargs):
        self.bot = bot
        bot.add_cog(self)
        self.send_manager: "SendManager" = SendManager()
        bot.add_cog(self.send_manager)
        self.channels_manager: "ChannelsManager" = ChannelsManager(bot, self)
        bot.add_cog(self.channels_manager)
        self.members_manager: "MembersManager" = MembersManager(bot, self)
        bot.add_cog(self.members_manager)
        self.streams_manager: "StreamsManager" = StreamsManager(bot, self)
        bot.add_cog(self.streams_manager)


    @commands.command(name="test")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def test(self, ctx):
        member_name = "astel"
        channel_id = "UCqoW8wtwI20rmtr69UItpvw"
        stream_id = "YVm6IrOcSSM"
        await self.members_manager.add_member(ctx, member_name)
        member = self.members_manager.get_member(ctx.guild, member_name)
        await self.channels_manager.add_youtube_channel(ctx, member_name, channel_id)
        channel = self.channels_manager.channels[channel_id]
        stream = await self.streams_manager.add_stream(stream_id, channel.id, time=Time.get_now())
        await ctx.send(stream)
        guild_streams_manager = self.streams_manager.get_guild_manager(ctx.guild)
        guild_stream = await guild_streams_manager.add_guild_stream(stream.id)
        # await ctx.send(guild_stream)
        guild_collab_stream = await guild_streams_manager.add_guild_collab_stream([stream.id])
        # await ctx.send(guild_stream)
        await ctx.send(guild_collab_stream)
