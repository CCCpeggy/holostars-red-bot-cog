# redbot
from redbot.core import checks, commands, Config
from redbot.core.config import Group

# other
import asyncio
from typing import *

# local
from .utils import *

_, log = get_logger()

class GuildMembersManager():
    def __init__(self, bot: Red, config: Group, guild: discord.Guild, manager: "Manager", **kwargs):
        self.bot: Red = bot
        self.config: Config = config
        self.manager: "Manager" = manager
        self.guild: discord.Guild = guild
        self.members: Dict[str, "Member"] = {}
        self.is_init = False
        
    async def initial(self):
        async def load_members():
            for key, value in (await self.config.members()).items():
                await self.add_member(saved=False, **value)
        await load_members()
        self.is_init = True

    async def save_memebers(self) -> None:
        await self.config.members.set(ConvertToRawData.dict(self.members))

    async def add_member(self, name: str, channel_ids: List[str]=[], save=True, **kwargs) -> Tuple["Member", bool]:
        if name not in self.members:
            member = Member(
                bot=self.bot,
                name=name,
                save_func=self.save_memebers,
                channel_ids=channel_ids,
                channels={id: self.manager.channels_manager.channels[id] for id in channel_ids},
                **kwargs
            )
            await member.initial()
            self.members[name] = member
            if save:
                await self.save_memebers()
            return member, True
        return self.members[name], False
    
    async def remove_member(self, member_name: str, saved: bool=True) -> "Member":
        if member_name in self.members:
            member = self.members.pop(member_name)
            if saved:
                await self.save_memebers()
            return member
        return None

    def get_member(self, member_name: str) -> "Member":
        return self.members.get(member_name, None)

    async def check(self):
        guild_streams_manager = await self.manager.streams_manager.get_guild_manager(self.guild)
        for stream in self.manager.streams_manager.streams.values():
            for member in self.members.values():
                if stream.channel_id in member.channel_ids:
                    guild_stream = await guild_streams_manager.add_guild_stream(stream.id)

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
        self.guild_managers: Dict[int, "GuildMembersManager"] = {}
        self.is_init = False

    async def initial(self):
        async def load_guild():
            for guild_id, config in (await self.config.all_guilds()).items():
                await self.get_guild_manager(int(guild_id))
        await load_guild()
        self.is_init = True
            
    def get_all_member(self) -> list:
        members = []
        for guild_manager in self.guild_managers.values():
            members += list(guild_manager.members.values())
        return members

    async def get_guild_manager(self, guild: Union[int, discord.Guild]) -> "GuildMembersManager":
        guild = guild if isinstance(guild, discord.Guild) else self.bot.get_guild(guild)
        if not guild.id in self.guild_managers:
            self.guild_managers[guild.id] = GuildMembersManager(
                self.bot, self.config.guild(guild), guild, self.manager)
            await self.guild_managers[guild.id].initial()
        return self.guild_managers[guild.id]

    async def get_member(self, guild: Union[int, discord.Guild], member_name: str) -> "Member":
        return (await self.get_guild_manager(guild)).get_member(member_name)

    async def check(self):
        for id, members_guild_managers in self.guild_managers.items():
            await members_guild_managers.check()

    @commands.group(name="member")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def member_group(self, ctx: commands.Context):
        pass

    @member_group.command(name="add")
    async def add_member(self, ctx: commands.Context, name: str):
        guild_manager = await self.get_guild_manager(ctx.guild)
        member, successful = await guild_manager.add_member(name=name)
        if successful:
            await Send.add_completed(ctx, "成員資料", member)
        else:
            await Send.already_existed(ctx, "成員資料", member)

    @member_group.command(name="remove")
    async def remove_member(self, ctx: commands.Context, name: str):
        guild_manager = await self.get_guild_manager(ctx.guild)
        member = await guild_manager.remove_member(name)
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
        guild_manager = await self.get_guild_manager(ctx.guild)
        data = None
        if len(guild_manager.members) == 0:
            await Send.empty(ctx, "成員資料")
            return
        elif name == None:
            data = [str(m) for m in guild_manager.members.values()]
        elif name in guild_manager.members:
            data = [str(guild_manager.members[name])]
        else:
            await Send.not_existed(ctx, "成員資料", name)
            return
        await Send.send(ctx, "\n".join(data))

    @member_group.group(name="set")
    async def memberset_group(self, ctx: commands.Context):
        pass

    @memberset_group.command(name="notify_channel")
    async def set_notify_channel(
        self, ctx: commands.Context, name: str, notify_text_channel: discord.TextChannel):
        guild_members_manager = await self.get_guild_manager(ctx.guild)
        member = guild_members_manager.members.get(name, None)
        if member:
            member.notify_text_channel = notify_text_channel
            await member._save_func()
            await Send.set_up_completed(ctx, f"{name} 的通知文字頻道", notify_text_channel)
        else:
            await Send.not_existed(ctx, "成員頻道", name)

    @memberset_group.command(name="chat_channel")
    async def set_chat_channel(
        self, ctx: commands.Context, name: str, chat_text_channel: discord.TextChannel):
        guild_members_manager = await self.get_guild_manager(ctx.guild)
        member = guild_members_manager.members.get(name, None)
        if member:
            member.chat_text_channel = chat_text_channel
            await member._save_func()
            await Send.set_up_completed(ctx, f"{name} 的討論文字頻道", chat_text_channel)
        else:
            await Send.not_existed(ctx, "成員頻道", name)

    @memberset_group.command(name="member_channel")
    async def set_member_channel(
        self, ctx: commands.Context, name: str, memeber_text_channel: discord.TextChannel):
        guild_members_manager = await self.get_guild_manager(ctx.guild)
        member = guild_members_manager.members.get(name, None)
        if member:
            member.memeber_text_channel = memeber_text_channel
            await member._save_func()
            await Send.set_up_completed(ctx, f"{name} 的會員文字頻道", memeber_text_channel)
        else:
            await Send.not_existed(ctx, "成員頻道", name)

    # async def get_start_channel(self, guild:discord.Guild):
    #     return await self.config.guild(guild).stream_start_message_format.get()
        
   

class Member:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.name: str = kwargs.pop("name")
        self.emoji: str = kwargs.pop("emoji", None)
        self.channel_ids: List[str] = kwargs.pop("channel_ids", [])
        if not isinstance(self.channel_ids, list):
            raise Exception
        self._channels: Dict[str, "Channel"] = kwargs.pop("channels", {})
        self._save_func = kwargs.pop("save_func", None)

        self.notify_text_channel: discord.TextChannel = None
        self.chat_text_channel: discord.TextChannel = None
        self.memeber_channel: discord.TextChannel = None
        self.is_init = False

        self._notify_text_channel_id: int = kwargs.pop("notify_text_channel", None)
        self._chat_text_channel_id: int = kwargs.pop("chat_text_channel", None)
        self._memeber_text_channel_id: str = kwargs.pop("memeber_channel", None)

    async def initial(self):
        async def load_channels():
            self.notify_text_channel = await get_text_channel(self._bot, self._notify_text_channel_id)
            self.chat_text_channel = await get_text_channel(self._bot, self._chat_text_channel_id)
            self.memeber_text_channel = await get_text_channel(self._bot, self._memeber_channel_id)
        self.is_init = True

    def __repr__(self):
        data = [
            f"成員名稱：{self.name}",
            f"> Emoji：{self.emoji if self.emoji else '未設定'}",
            f"> 通知文字頻道：{GetSendStr.get_channel_mention(self.notify_text_channel)}",
            f"> 討論文字頻道：{GetSendStr.get_channel_mention(self.chat_text_channel)}",
            f"> 會員文字頻道：{GetSendStr.get_channel_mention(self.memeber_channel)}",
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
