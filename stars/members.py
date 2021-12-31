from redbot.core import checks, commands, Config
from redbot.core.config import Group
from redbot.core.i18n import Translator

# other
import asyncio

# local
from .utils import *
from .streams import StreamsManager
from .channel.channel import Channel
from .channel.youtube_channel import YoutubeChannel
from . import channel as _channel_types

_ = Translator("StarStreams", __file__)
log = logging.getLogger("red.core.cogs.StarStreams")

class MembersManager():
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = MembersManagerConfig(bot)
        self.streams_manager = StreamsManager()
        bot.add_cog(self.config)

    def get_streams_manager(self):
        return self.streams_manager

class MembersManagerConfig(commands.Cog):

    global_defaults = {
        "channels_": {}
    }

    guild_defaults = {
        "members": {}
    }

    class Guild():
        def __init__(self, bot: Red, config: Group):
            self.config = config
            self.members = {}
            self.bot = bot
            
            async def async_load():
                async def load_members():
                    for key, value in (await config.members()).items():
                        await self.add_member(saved=False, **value)
                await load_members()
            self._init_task: asyncio.Task = self.bot.loop.create_task(async_load())

        async def save_memebers(self):
            await self.config.members.set(ConvertToRawData.dict(self.members))

        async def add_member(self, saved=True, **kwargs) -> Tuple["Member", bool]:
            name = kwargs.get("name")
            if name not in self.members:
                member = Member(bot=self.bot, _save_func=self.save_memebers, **kwargs)
                self.members[name] = member
                if saved:
                    await self.save_memebers()
                return member, True
            return self.members[name], False
        
        def remove_member(self, name: str, saved: bool=True) -> bool:
            if name in self.members:
                members.pop(name)
                if saved:
                    save_memebers()
                return True
            return False

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 45611846)
        self.config.register_global(**self.global_defaults)
        self.config.register_guild(**self.guild_defaults)
        self.guild_configs = {}
        self.channels = {}
        async def async_load():
            async def load_channels():
                for id, raw_data in (await self.config.channels_()).items():
                    _class = Channel.get_class(raw_data["type"])
                    self.channels[id] = _class(bot=bot, **raw_data)
            await load_channels()
            async def load_guild():
                for guild_id, config in (await self.config.all_guilds()).items():
                    self.get_guild_config(guild_id)
            await load_guild()
            
        self._init_task: asyncio.Task = self.bot.loop.create_task(async_load())

    async def save_channels(self):
        await self.config.channels_.set(ConvertToRawData.dict(self.channels))

    @commands.group(name="member")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def member_group(self, ctx: commands.Context):
        pass
    
    def get_guild_config(self, guild: Union[int, discord.Guild]) -> "MembersManagerConfig.Guild":
        guild = guild if isinstance(guild, discord.Guild) else self.bot.get_guild(guild)
        if not guild.id in self.guild_configs:
            self.guild_configs[guild.id] = MembersManagerConfig.Guild(self.bot, self.config.guild(guild))
        return self.guild_configs[guild.id]

    @member_group.command(name="add")
    async def add_member(self, ctx: commands.Context, name: str):
        guild_config = self.get_guild_config(ctx.guild)
        member, successful = await guild_config.add_member(name=name)
        if successful:
            await Send.add_completed(ctx, "成員資料", member)
        else:
            await Send.already_existed(ctx, "成員資料", member)

    @member_group.command(name="remove")
    async def remove_member(self, ctx: commands.Context, name: str):
        guild_config = self.get_guild_config(ctx.guild)
        # TODO: delete channel
        if guild_config.remove_member(name):
            await Send.remove_completed(ctx, "成員資料", name)
        else:
            await Send.not_existed(ctx, "成員資料", name)

    @member_group.command(name="list")
    async def list_member(self, ctx: commands.Context, name: str=None):
        guild_config = self.get_guild_config(ctx.guild)
        data = None
        if len(guild_config.members) == 0:
            await Send.empty(ctx, "成員資料")
            return
        elif name == None:
            data = [str(m) for m in guild_config.members.values()]
        elif name in guild_config.members:
            data = [str(guild_config.members[name])]
        else:
            await Send.not_existed(ctx, "成員資料", name)
            return
        await Send.send(ctx, "\n".join(data))
    # @memberset_group.group(name="set")
    # async def set_member_group(self, ctx: commands.Context, name: str):
    #     if name not in self.members:
    #         await Send.not_existed(ctx, "成員資料", name)
    #     else:
    #         member = self.members[name]

    # @set_member_group.command(name="notify_channel")
    # async def set_member(self, ctx: commands.Context, notify_text_channel:discord.TextChannel):
    #     member.notify_text_channel = notify_text_channel

    # async def get_start_channel(self, guild:discord.Guild):
    #     return await self.config.guild(guild).stream_start_message_format.get()
        
    @commands.group(name="channel")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def channel_group(self, ctx: commands.Context):
        pass

    @channel_group.group(name="youtube")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def youtube_group(self, ctx: commands.Context):
        pass

    @youtube_group.command(name="add")
    async def add_youtube_channel(self, ctx: commands.Context, name: str, channel_id: str):
        guild_config = self.get_guild_config(ctx.guild)
        if not Youtube.check_id(channel_id):
            await Send.data_error(ctx, "頻道 ID", channel_id)
            return
        if name not in guild_config.members:
            await Send.not_existed(ctx, "成員資料", name)
            return
        channel, successful = await self.add_channel(YoutubeChannel, channel_id)            
        if successful:
            await Send.add_completed(ctx, "頻道資料", channel)
        member = guild_config.members[name]
        if await member.add_channel(channel_id):
            await Send.add_completed(ctx, f"{name} 成員資料對於此頻道", channel)
        else:
            await Send.already_existed(ctx, f"{name} 成員資料對於此頻道", channel)

    @channel_group.command(name="list")
    async def list_channel(self, ctx: commands.Context, id: str=None):
        data = None
        if len(self.channels) == 0:
            await Send.empty(ctx, "頻道資料")
            return
        elif id == None:
            data = [str(m) for m in self.channels.values()]
        elif id in self.channels:
            data = [str(self.channels[id])]
        else:
            await Send.not_existed(ctx, "頻道資料", id)
            return
        await Send.send(ctx, "\n".join(data))

    async def add_channel(self, Channel, channel_id: str) -> Tuple[Channel, bool]:
        if channel_id not in self.channels:
            channel = Channel(bot=self.bot, id=channel_id)
            self.channels[channel_id] = channel
            await self.save_channels()
            return channel, True
        return self.channels[channel_id], False

class Member:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.name: str = kwargs.pop("name")
        self.emoji: str = kwargs.pop("emoji", None)
        self.channels: dict = kwargs.pop("channels", [])
        self._save_func = kwargs.pop("_save_func", None)

        self.notify_text_channel = None
        self.chat_text_channel = None
        self.memeber_channel = None

        async def async_load():
            self.notify_text_channel: discord.TextChannel = await get_channel(self._bot, kwargs.pop("notify_text_channel", None))
            self.chat_text_channel: discord.TextChannel = await get_channel(self._bot, kwargs.pop("chat_text_channel", None))
            self.memeber_channel: discord.TextChannel = await get_channel(self._bot, kwargs.pop("memeber_channel", None))

        self._init_task: asyncio.Task = self._bot.loop.create_task(async_load())

    def __repr__(self):
        def getChannelMention(channel, default="未設定"):
            return channel.mention if channel else '未設定'
        data = [
            f"成員名稱：{self.name}",
            f"> Emoji：{self.emoji if self.emoji else '未設定'}",
            f"> 通知文字頻道：{getChannelMention(self.notify_text_channel)}",
            f"> 討論文字頻道：{getChannelMention(self.chat_text_channel)}",
            f"> 會員文字頻道：{getChannelMention(self.memeber_channel)}",
            f"> 頻道 ID：{', '.join(self.channels)}",
        ]
        return "\n".join(data)
        
    async def add_channel(self, channel_id: str) -> bool:
        if channel_id in self.channels:
            return False
        else:
            self.channels.append(channel_id)
            if self._save_func:
                await self._save_func()
            return True