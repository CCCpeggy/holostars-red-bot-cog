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
        self.bot.add_cog(self)
        self.send_manager: "SendManager" = SendManager(self.bot, self)
        self.bot.add_cog(self.send_manager)
        self.channels_manager: "ChannelsManager" = ChannelsManager(self.bot, self)
        self.bot.add_cog(self.channels_manager)
        self.members_manager: "MembersManager" = MembersManager(self.bot, self)
        self.bot.add_cog(self.members_manager)
        self.streams_manager: "StreamsManager" = StreamsManager(self.bot, self)
        self.bot.add_cog(self.streams_manager)
        self.bot.loop.create_task(self.initial())

    async def initial(self):
        await self.bot.wait_until_red_ready()
        await self.channels_manager.initial()
        await self.members_manager.initial()
        await self.streams_manager.initial()
        await self.check()

    async def check(self):
        await self.channels_manager.check()
        await self.streams_manager.delete_not_valid_and_notsure_stream()
        await self.members_manager.check()
        await self.streams_manager.check()
        await self.send_manager.check()

    @commands.group(name="test")
    @commands.guild_only()
    @checks.is_owner()
    async def test(self, ctx):
        pass

    @test.command(name="set")
    async def test_set(self, ctx):
        member_name = "roboco"
        channel_id = "UCDqI2jOz0weumE8s7paEk6g"
        await self.members_manager.add_member(ctx=ctx, name=member_name)
        member = await self.members_manager.get_member(ctx.guild, member_name)
        await self.channels_manager._add_channel(ctx, member_name, "holodex", channel_id)
        channel = self.channels_manager.channels[channel_id]
        
        await self.members_manager.set_notify_channel(ctx, member_name, 884066848822427708)
        await self.members_manager.set_chat_channel(ctx, member_name, 884066992762523649)
        await self.members_manager.set_member_channel(ctx, member_name, 886454736344186963)
        await self.check()


    @test.command(name="astel")
    async def test_astel(self, ctx):
        member_name = "astel"
        channel_id = "UCNVEsYbiZjH5QLmGeSgTSzg"
        await self.members_manager.add_member(ctx=ctx, name=member_name)
        member = await self.members_manager.get_member(ctx.guild, member_name)
        await self.channels_manager._add_channel(ctx, member_name, "holodex", channel_id)
        channel = self.channels_manager.channels[channel_id]

    @test.command(name="data")
    async def test_data(self, ctx):
        member_name = "astel"
        channel_id = "UCNVEsYbiZjH5QLmGeSgTSzg"
        stream_id = "YVm6IrOcSSM"
        await self.members_manager.add_member(ctx=ctx, name=member_name)
        member = await self.members_manager.get_member(ctx.guild, member_name)
        await self.channels_manager._add_channel(ctx, member_name, "holodex", channel_id)
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

    @test.command(name="holodex")
    async def test_holodex(self, ctx):
        log.debug("-------------------test_holodex---------------------")
        member_name = "aruran"
        channel_id = "UCKeAhJvy8zgXWbh9duVjIaQ"
        await self.members_manager.remove_member(ctx=ctx, name=member_name)
        await self.check()

        # add member
        await self.members_manager.add_member(ctx=ctx, name=member_name)
        await self.members_manager.set_notify_channel(ctx, member_name, await get_text_channel(ctx.guild, 884066848822427708))
        await self.members_manager.set_chat_channel(ctx, member_name, await get_text_channel(ctx.guild, 884066992762523649))
        await self.send_manager.set_message_start(ctx, "time: {time}{new_line}title: {title}\nchannel_name: {channel_name}\nurl: {url}\nmention: {mention}\ndescription: {description}")
        member = await self.members_manager.get_member(ctx.guild, member_name)
        
        # add channel
        await self.channels_manager._add_channel(ctx, member_name, "holodex", channel_id)
        channel = self.channels_manager.channels[channel_id]

        await self.check()
