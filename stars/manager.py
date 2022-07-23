# redbot
from glob import glob
from redbot.core.i18n import Translator
from redbot.core import checks, commands, Config

# local
from .utils import *
from .streams import StreamsManager
from .channels import ChannelsManager
from .members import MembersManager
from .send import SendManager

# other
import asyncio

_, log = get_logger()
send_manager = None
channels_manager = None
members_manager = None
streams_manager = None

class Manager(commands.Cog):
    def __init__(self, bot: Red, **kwargs):
        super().__init__()
        self.bot = bot
        self.send_manager: "SendManager" = SendManager(self.bot, self)
        self.channels_manager: "ChannelsManager" = ChannelsManager(self.bot, self)
        self.members_manager: "MembersManager" = MembersManager(self.bot, self)
        self.streams_manager: "StreamsManager" = StreamsManager(self.bot, self)
        self.task = self.bot.loop.create_task(self.initial())

        global send_manager
        send_manager = self.send_manager
        global channels_manager
        channels_manager = self.channels_manager
        global members_manager
        members_manager = self.members_manager
        global streams_manager
        streams_manager = self.streams_manager

    async def initial(self):
        await self.bot.add_cog(self.send_manager)
        await self.bot.add_cog(self.channels_manager)
        await self.bot.add_cog(self.members_manager)
        await self.bot.add_cog(self.streams_manager)
    
        await self.bot.wait_until_red_ready()
        await self.channels_manager.initial()
        await self.members_manager.initial()
        await self.streams_manager.initial()
        while True:
            await self.check(None)
            await asyncio.sleep(60)

    async def cog_unload(self):
        if self.task:
            self.task.cancel()
        await self.bot.remove_cog(self.send_manager)
        await self.bot.remove_cog(self.channels_manager)
        await self.bot.remove_cog(self.members_manager)
        await self.bot.remove_cog(self.streams_manager)

    @commands.command(name="check")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def check(self, ctx):
        log.debug("---------check start---------")
        await self.channels_manager.check()
        await self.streams_manager.delete_not_valid_and_notsure_stream()
        await self.members_manager.check()
        await self.streams_manager.check()
        await self.send_manager.check()
        log.debug("---------check end---------")
        if ctx:
            await Send.send(ctx, "檢查結束")

    @commands.group(name="test")
    @commands.guild_only()
    @checks.is_owner()
    async def test(self, ctx):
        pass

    @test.command(name="set")
    async def test_set(self, ctx):
        member_name = "gura"
        channel_id = "UCoSrY_IQQVpmIRZ9Xf-y93g"
        await self.members_manager.add_member(ctx, name=member_name)
        member = await self.members_manager.get_member(ctx.guild, member_name)
        await self.channels_manager._add_channel(ctx, member, "holodex", channel_id)
        channel = self.channels_manager.channels[channel_id]
        
        await self.members_manager.set_notify_channel(ctx, member, get_text_channel(ctx.guild, 1000064180239474728))
        await self.members_manager.set_chat_channel(ctx, member, get_text_channel(ctx.guild, 1000064200758022265))
        await self.members_manager.set_member_channel(ctx, member, get_text_channel(ctx.guild, 1000064221817618562))
        await self.check(None)

    @test.command(name="astel")
    async def test_astel(self, ctx):
        member_name = "astel"
        channel_id = "UCNVEsYbiZjH5QLmGeSgTSzg"
        await self.members_manager.add_member(ctx=ctx, name=member_name)
        member = await self.members_manager.get_member(ctx.guild, member_name)
        await self.channels_manager._add_channel(ctx, member, "holodex", channel_id)
        channel = self.channels_manager.channels[channel_id]

    @test.command(name="data")
    async def test_data(self, ctx):
        member_name = "gura"
        channel_id = "UCoSrY_IQQVpmIRZ9Xf-y93g"
        stream_id = "Cvs7XL60xKM"
        await self.members_manager.add_member(ctx, name=member_name)
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

    @test.command(name="youtube")
    async def test_youtube(self, ctx):
        log.debug("-------------------test_holodex---------------------")
        member_name = "プテラたかはし"
        channel_id = "UC65uVBk6DQMj-a17jFK0oRg"
        await self.members_manager.remove_member(ctx, member_name)
        await self.check(None)

        # add member
        await self.members_manager.add_member(ctx, member_name)
        member = await self.members_manager.get_member(ctx.guild, member_name)
        await self.members_manager.add_mention_role(ctx, member, get_role(ctx.guild, 1000066476021133454))
        await self.members_manager.add_mention_role(ctx, member, get_role(ctx.guild, 1000066661426151505))
        await self.members_manager.set_color(ctx, member, 0x00, 0x47, 0xAB)
        await self.members_manager.set_emoji(ctx, member, ":performing_arts:")
        await self.members_manager.set_notify_channel(ctx, member, get_text_channel(ctx.guild, 1000064180239474728))
        await self.members_manager.set_chat_channel(ctx, member, get_text_channel(ctx.guild, 1000064200758022265))
        await self.members_manager.set_member_channel(ctx, member, get_text_channel(ctx.guild, 1000064221817618562))
        
        # add channel
        await self.channels_manager._add_channel(ctx, member, "youtube", channel_id)
        channel = self.channels_manager.channels[channel_id]
        await self.streams_manager.add_stream("", channel_id, save=True)

        await self.check(None)

    @test.command(name="holodex")
    async def test_holodex(self, ctx):
        log.debug("-------------------test_holodex---------------------")
        member_name = "astel"
        channel_id = "UCNVEsYbiZjH5QLmGeSgTSzg"
        video_id = "d0Ksx3Qymwc"
        await self.members_manager.remove_member(ctx, member_name)
        await self.check()

        # add member
        await self.members_manager.add_member(ctx, member_name)
        member = await self.members_manager.get_member(ctx.guild, member_name)
        await self.members_manager.add_mention_role(ctx, member, get_role(ctx.guild, 1000066476021133454))
        await self.members_manager.add_mention_role(ctx, member, get_role(ctx.guild, 1000066661426151505))
        await self.members_manager.set_color(ctx, member, 0x00, 0x47, 0xAB)
        await self.members_manager.set_emoji(ctx, member, ":performing_arts:")
        await self.members_manager.set_notify_channel(ctx, member, get_text_channel(ctx.guild, 1000064180239474728))
        await self.members_manager.set_chat_channel(ctx, member, get_text_channel(ctx.guild, 1000064200758022265))
        await self.members_manager.set_member_channel(ctx, member, get_text_channel(ctx.guild, 1000064221817618562))
        await self.send_manager.set_message_start(ctx, "time: {time}{new_line}title: {title}\nchannel_name: {channel_name}\nurl: {url}\nmention: {mention}\ndescription: {description}")
        member = await self.members_manager.get_member(ctx.guild, member)
        
        # add channel
        await self.channels_manager._add_channel(ctx, member_name, "holodex", channel_id)
        channel = self.channels_manager.channels[channel_id]
        await self.streams_manager.add_stream(ctx, video_id, channel_id, save=True)
        await self.check()

    @test.command(name="member_only")
    async def test_member_only(self, ctx):
        member_name = "kaela"
        channel_id = "UCZLZ8Jjx_RN2CXloOmgTHVg"
        await self.members_manager.remove_member(ctx, member_name)
        await self.check(None)

        # add member
        await self.members_manager.add_member(ctx, member_name)
        member = await self.members_manager.get_member(ctx.guild, member_name)
        await self.members_manager.add_mention_role(ctx, member, get_role(ctx.guild, 1000066476021133454))
        await self.members_manager.add_mention_role(ctx, member, get_role(ctx.guild, 1000066661426151505))
        await self.members_manager.set_color(ctx, member, 0x00, 0x47, 0xAB)
        await self.members_manager.set_emoji(ctx, member, ":performing_arts:")
        await self.members_manager.set_notify_channel(ctx, member, get_text_channel(ctx.guild, 1000064180239474728))
        await self.members_manager.set_chat_channel(ctx, member, get_text_channel(ctx.guild, 1000064200758022265))
        await self.members_manager.set_member_channel(ctx, member, get_text_channel(ctx.guild, 1000064221817618562))
        
        # add channel
        await self.channels_manager._add_channel(ctx, member, "holodex", channel_id)
        channel = self.channels_manager.channels[channel_id]
        await self.check(None)


    @test.command(name="collab")
    async def test_collab(self, ctx):
        log.debug("-------------------test_collab---------------------")
        await self.send_manager.set_info_channel(ctx, get_text_channel(ctx.guild, 1000049609881682060))
        member_name1 = "Ollie"
        channel_id1 = "UCYz_5n-uDuChHtLo7My1HnQ"
        
        # remove member 1
        await self.members_manager.remove_member(ctx, member_name1)
        await self.check(None)
        
        # add member 1
        await self.members_manager.add_member(ctx, member_name1)
        member = await self.members_manager.get_member(ctx.guild, member_name1)
        await self.members_manager.set_emoji(ctx, member, "🆗")
        await self.members_manager.set_notify_channel(ctx, member, get_text_channel(ctx.guild, 1000064180239474728))
        await self.members_manager.set_chat_channel(ctx, member, get_text_channel(ctx.guild, 1000064200758022265))
        
        # add channel 1
        await self.channels_manager._add_channel(ctx, member, "holodex", channel_id1)
        channel = self.channels_manager.channels[channel_id1]
        
        # set collab
        from datetime import datetime
        time = datetime(2022, 7, 22, 22, 30)
        time = Time.add_timezone(time, 'Asia/Taipei')
        await self.streams_manager.create_collab(ctx, time, get_text_channel(ctx.guild, 1000067977405800599))
        # member_name2 = "aruran"
        # channel_id2 = "UCKeAhJvy8zgXWbh9duVjIaQ"
        # await self.members_manager.remove_member(ctx, member_name2)
        
        # await self.check()

        # # add member 1
        # await self.members_manager.add_member(ctx, member_name1)
        # member = await self.members_manager.get_member(ctx.guild, member_name1)
        # await self.members_manager.set_emoji(ctx, member, "🆗")
        # await self.members_manager.set_notify_channel(ctx, member, get_text_channel(ctx.guild, 884066848822427708))
        # await self.members_manager.set_chat_channel(ctx, member, get_text_channel(ctx.guild, 884066992762523649))
        
        # # add channel 1
        # await self.channels_manager._add_channel(ctx, member, "holodex", channel_id1)
        # channel = self.channels_manager.channels[channel_id1]
        
        # await self.check()

        # # add member 2
        # await self.members_manager.add_member(ctx, member_name2)
        # member = await self.members_manager.get_member(ctx.guild, member_name2)
        # await self.members_manager.set_emoji(ctx, member, "🍕")
        # await self.members_manager.set_notify_channel(ctx, member, get_text_channel(ctx.guild, 884066848822427708))
        # await self.members_manager.set_chat_channel(ctx, member, get_text_channel(ctx.guild, 884066992762523649))
        
        # # add channel 2
        # await self.channels_manager._add_channel(ctx, member, "holodex", channel_id2)
        # channel = self.channels_manager.channels[channel_id2]

        # await self.streams_manager.add_collab(ctx, "KYGJX6is71M")
        # await self.check()
        # # await self.streams_manager.add_collab(ctx, "IwqcjU5V2Xg")