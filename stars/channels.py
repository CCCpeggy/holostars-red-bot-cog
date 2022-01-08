# redbot
from redbot.core import checks, commands, Config

# other
import asyncio

# local
from .utils import *
from .streams import StreamsManager
from .channel.channel import Channel
from .channel.youtube import YoutubeChannel
from .channel.holodex import HolodexChannel

_, log = get_logger()

class ChannelsManager(commands.Cog):
    
    global_defaults = {
        "channels_": {}
    }

    guild_defaults = {
    }

    def __init__(self, bot: Red, manager: "Manager", **kwargs):
        self.bot: Red = bot
        self.manager: "Manager" = manager
        self.config: Config = Config.get_conf(self, 45611846)
        self.config.register_global(**self.global_defaults)
        self.config.register_guild(**self.guild_defaults)
        self.channels: Dict[str, Channel] = {}
        self.is_init = False

    async def initial(self):
        async def load_channels():
            for id, raw_data in (await self.config.channels_()).items():
                _class = Channel.get_class(raw_data["type"])
                self.channels[id] = _class(bot=self.bot, **raw_data)
        await load_channels()
        self.is_init = True

    async def remove_channel(self, channel_id: str) -> "Channel":
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

    def get_channel_belong_member(self, channel_id: str) -> "Member":
        members = self.manager.members_manager.get_all_member()
        members = {member for member in members if channel_id in member.channel_ids}
        return members

    @commands.group(name="channel")
    @commands.guild_only()
    @checks.mod_or_permissions(manage_channels=True)
    async def channel_group(self, ctx: commands.Context):
        pass

    @channel_group.command(name="add")
    async def add_youtube_channel(self, ctx: commands.Context, name: str, channel_type_name: str, channel_id: str):
        ChannelType = Channel.get_class_by_name(channel_type_name)
        if not ChannelType:
            await Send.data_error(ctx, "頻道類型錯誤", channel_type_name)
        if not ChannelType.check_channel_id(channel_id):
            await Send.data_error(ctx, "頻道 ID", channel_id)
            return
        member = await self.manager.members_manager.get_member(ctx.guild, name)
        if member == None:
            await Send.not_existed(ctx, "成員資料", name)
            return
        channel, successful = await self.add_channel(ChannelType, channel_id)            
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


    @channel_group.command(name="remove")
    async def _remove_channel(self, ctx: commands.Context, channel_id: str):
        channel = await self.remove_channel(channel_id)
        if channel:
            await Send.remove_completed(ctx, "頻道資料", channel)
        else:
            await Send.not_existed(ctx, "頻道資料", channel_id)

    async def check(self):
        self.manager.streams_manager.set_stream_to_notsure()
        for id, channel in self.channels.items():
            streams_info = await channel.get_streams_info()
            for stream_info in streams_info:
                stream = self.manager.streams_manager.get_stream(stream_info["id"])
                if stream:
                    stream.update_info(**stream_info)
                else:
                    stream = await self.manager.streams_manager.add_stream(**stream_info)
