# redbot
from redbot.core import checks, commands, Config
from redbot.core.config import Group

# other
import asyncio

# local
from .utils import *
from .channel.channel import Channel
from .channel.youtube_channel import YoutubeChannel
from . import channel as _channel_types

_, log = get_logger()

class GuildMembersManager():
    def __init__(self, bot: Red, config: Group, manager: "Manager", **kwargs):
        self.config = config
        self.manager = manager
        self.channel_manager = kwargs.pop("channel_manager", None)
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
    
    async def remove_member(self, name: str, saved: bool=True) -> "Member":
        if name in self.members:
            member = self.members.pop(name)
            if saved:
                await self.save_memebers()
            return member
        return None

class MembersManager(commands.Cog):

    global_defaults = {
    }

    guild_defaults = {
        "members": {}
    }

    def __init__(self, bot: Red, manager: "Manager"):
        self.bot = bot
        self.manager = manager
        self.config = Config.get_conf(self, 45611846)
        self.config.register_global(**self.global_defaults)
        self.config.register_guild(**self.guild_defaults)
        self.guild_configs = {}
        async def async_load():
            async def load_guild():
                for guild_id, config in (await self.config.all_guilds()).items():
                    self.get_guild_config(guild_id)
            await load_guild()
            
        self._init_task: asyncio.Task = self.bot.loop.create_task(async_load())

    def get_member(self, guild: Union[int, discord.Guild], name: str) -> "Member":
        guild_config = self.get_guild_config(guild)
        if name in guild_config.members:
            return guild_config.members[name]
        else:
            return None
    
    def get_all_member(self) -> list:
        members = []
        for guild_config in self.guild_configs.values():
            members += list(guild_config.members.values())
        return members

    def get_guild_config(self, guild: Union[int, discord.Guild]) -> "GuildMembersManager":
        guild = guild if isinstance(guild, discord.Guild) else self.bot.get_guild(guild)
        if not guild.id in self.guild_configs:
            self.guild_configs[guild.id] = GuildMembersManager(self.bot, self.config.guild(guild), self.manager)
        return self.guild_configs[guild.id]

    @commands.group(name="member")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def member_group(self, ctx: commands.Context):
        pass

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
        member = await guild_config.remove_member(name)
        if member:
            await Send.remove_completed(ctx, "成員資料", name)
            for channel_id in member.channel_ids:
                belong_members = self.manager.channels_manager.get_channel_belong_member(channel_id)
                if len(belong_members) == 0:
                    channel = await self.manager.channels_manager.remove_channel(channel_id)
                    await Send.remove_completed(ctx, f"只屬於 {member.name} 的頻道資料", channel)
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
        
   

class Member:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.name: str = kwargs.pop("name")
        self.emoji: str = kwargs.pop("emoji", None)
        self.channel_ids: dict = kwargs.pop("channel_ids", [])
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
            f"> 頻道 ID：{', '.join(self.channel_ids)}",
        ]
        return "\n".join(data)
        
    async def add_channel(self, channel_id: str) -> bool:
        if channel_id in self.channel_ids:
            return False
        else:
            self.channel_ids.append(channel_id)
            if self._save_func:
                await self._save_func()
            return True