# local
from stars.utils import *

_, log = get_logger()

class Channel:

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.id: str = kwargs.pop("id")
        self.type = "Channel"

        async def async_load():
            return
            self.notify_text_channel: discord.TextChannel = await get_channel(self.bot, kwargs.pop("notify_text_channel", None))
            self.chat_text_channel: discord.TextChannel = await get_channel(self.bot, kwargs.pop("chat_text_channel", None))
            self.memeber_channel: discord.TextChannel = await get_channel(self.bot, kwargs.pop("memeber_channel", None))

        self._init_task: asyncio.Task = self._bot.loop.create_task(async_load())

    def __repr__(self):
        data = [
            f"頻道 ID：{self.id}",
        ]
        return "\n".join(data)

    @staticmethod
    def get_class(class_type: str):
        if class_type == "YoutubeChannel":
            from .youtube_channel import YoutubeChannel
            return YoutubeChannel
        else:
            return Channel

