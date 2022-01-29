# local
from stars.utils import *

_, log = get_logger()

class Channel:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.id: str = kwargs.pop("id")
        self.name: str = kwargs.pop("name", None)
        self.type = "Channel"

        # async def async_load():
        #     return
        #     self.notify_text_channel: discord.TextChannel = await get_text_channel(self.bot, kwargs.pop("notify_text_channel", None))
        #     self.chat_text_channel: discord.TextChannel = await get_text_channel(self.bot, kwargs.pop("chat_text_channel", None))
        #     self.memeber_channel: discord.TextChannel = await get_text_channel(self.bot, kwargs.pop("memeber_channel", None))

    def __repr__(self):
        data = [
            f"{self.type}",
            f"> 頻道 ID：{self.id}",
            f"> 頻道名稱：{self.name}",
        ]
        return "\n".join(data)

    async def fetch_channel_data(self):
        pass

    async def get_streams_info(self) -> List[Dict]:
        return []

    @staticmethod
    def get_class(class_type: str):
        if class_type == "YoutubeChannel":
            from .youtube import YoutubeChannel
            return YoutubeChannel
        elif class_type == "HolodexChannel":
            from .holodex import HolodexChannel
            return HolodexChannel
        else:
            return Channel
