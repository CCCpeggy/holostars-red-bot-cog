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
        self._init_task: asyncio.Task = self.bot.loop.create_task(self.initial())
    
    async def initial(self):
        self.bot.add_cog(self)
        self.send_manager: "SendManager" = SendManager()
        self.bot.add_cog(self.send_manager)
        self.channels_manager: "ChannelsManager" = ChannelsManager(self.bot, self)
        await self.channels_manager.initial()
        self.bot.add_cog(self.channels_manager)
        self.members_manager: "MembersManager" = MembersManager(self.bot, self)
        await self.members_manager.initial()
        self.bot.add_cog(self.members_manager)
        self.streams_manager: "StreamsManager" = StreamsManager(self.bot, self)
        self.bot.add_cog(self.streams_manager)
        await self.streams_manager.initial()


    @commands.group(name="test")
    @commands.guild_only()
    @checks.is_owner()
    async def test(self, ctx):
        pass

    @test.command(name="data")
    async def test_data(self, ctx):
        member_name = "astel"
        channel_id = "UCqoW8wtwI20rmtr69UItpvw"
        stream_id = "YVm6IrOcSSM"
        await self.members_manager.add_member(ctx=ctx, name=member_name)
        member = await self.members_manager.get_member(ctx.guild, member_name)
        await self.channels_manager.add_youtube_channel(ctx, member_name, channel_id)
        channel = self.channels_manager.channels[channel_id]
        stream = await self.streams_manager.add_stream(stream_id, channel.id, time=Time.get_now())
        if stream:
            await Send.add_completed(ctx, type(stream).__name__, stream)
        else:
            stream = self.streams_manager.get_stream(stream_id)
            await Send.already_existed(ctx, type(stream).__name__, stream)
        guild_streams_manager = await self.streams_manager.get_guild_manager(ctx.guild)
        guild_stream = await guild_streams_manager.add_guild_stream(stream.id)
        if guild_stream:
            await Send.add_completed(ctx, type(guild_stream).__name__, guild_stream)
        else:
            guild_stream = guild_streams_manager.get_guild_stream(stream_id)
            await Send.already_existed(ctx, type(guild_stream).__name__, guild_stream)
        if guild_stream._guild_collab_stream:
            guild_collab_stream = guild_stream._guild_collab_stream
            await Send.already_existed(ctx, type(guild_collab_stream).__name__, guild_collab_stream)
        else:
            guild_collab_stream = await guild_streams_manager.add_guild_collab_stream([stream.id])
            await Send.add_completed(ctx, type(guild_collab_stream).__name__, guild_collab_stream)

    @test.command(name="channel")
    async def test_channel(self, ctx):
        from .channel.holodex import HolodexChannel
        info = {
            "bot": self.bot,
            "id": "UCZgOv3YDEs-ZnZWDYVwJdmA"
        }
        channel = HolodexChannel(info)
        print(channel)