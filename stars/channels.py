# redbot
from redbot.core import checks, commands, Config

# other
import asyncio

# local
from .utils import *
from .streams import StreamsManager
from .channel.channel import Channel
from .channel.youtube_channel import YoutubeChannel

_, log = get_logger()

class ChannelsManager(commands.Cog):
    
    global_defaults = {
        "channels_": {}
    }

    guild_defaults = {
    }

    def __init__(self, bot: Red, manager: "Manager", **kwargs):
        self.bot = bot
        self.manager: "Manager" = manager
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
            
        self._init_task: asyncio.Task = self.bot.loop.create_task(async_load())
    
    def get_streams_manager(self):
        return self.streams_manager

    async def remove_channel(self, channel_id) -> "Channel":
        if channel_id in channel_id:
            channel = self.channels.pop(channel_id)
            await self.save_channels()
            return channel
        return None

    async def add_channel(self, Channel, channel_id: str) -> Tuple[Channel, bool]:
        if channel_id not in self.channels:
            channel = Channel(bot=self.bot, id=channel_id)
            self.channels[channel_id] = channel
            await self.save_channels()
            return channel, True
        return self.channels[channel_id], False
    
    async def save_channels(self) -> None:
        await self.config.channels_.set(ConvertToRawData.dict(self.channels))

    def get_channel_belong_member(self, channel_id: str):
        members = self.manager.members_manager.get_all_member()
        members = {member for member in members if channel_id in member.channel_ids}
        return members

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
        if not Youtube.check_id(channel_id):
            await Send.data_error(ctx, "頻道 ID", channel_id)
            return
        member = self.manager.members_manager.get_member(ctx.guild, name)
        if member == None:
            await Send.not_existed(ctx, "成員資料", name)
            return
        channel, successful = await self.add_channel(YoutubeChannel, channel_id)            
        if successful:
            await Send.add_completed(ctx, "頻道資料", channel)
        else:
            await Send.already_existed(ctx, "頻道資料", channel)
        if await member.add_channel(channel_id):
            await Send.add_completed(ctx, f"{name} 成員資料對於此頻道", channel)
        else:
            await Send.already_existed(ctx, f"{name} 成員資料對於此頻道", channel)

    @channel_group.command(name="list")
    async def list_channel(self, ctx: commands.Context, id: str=None, output_member: bool=False):
        def get_channel_str(channel) -> str:
            data = [str(channel)]
            if output_member:
                members = self.get_channel_belong_member(channel.id)
                data.append(f"頻道所屬成員：{', '.join({m.name for m in members})}")
            return "\n".join(data)
        data = []
        if len(self.channels) == 0:
            await Send.empty(ctx, "頻道資料")
            return
        elif id == None or id == "None":
            for channel in self.channels.values():
                data.append(get_channel_str(channel))
        elif id in self.channels:
            data.append(get_channel_str(self.channels[id]))
        else:
            await Send.not_existed(ctx, "頻道資料", id)
            return
        await Send.send(ctx, "\n".join(data))
