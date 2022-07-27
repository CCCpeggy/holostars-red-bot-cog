# local
from stars.utils import *

_, log = get_logger()

class Channel:
    type_name = "default"

    def __init__(self, **kwargs):
        self._bot: Red = kwargs.pop("bot")
        self.id: str = kwargs.pop("id")
        self.name: str = kwargs.pop("name", None)
        self.url: str = kwargs.pop("url", None)
        self.source_name: str = kwargs.pop("source_name", None)
        self.source_url: str = kwargs.pop("source_url", None)
        self.type = "Channel"

    def __repr__(self):
        data = [
            f"{self.type}",
            f"> 頻道 ID：{self.id}",
            f"> 頻道名稱：{self.name}",
        ]
        return "\n".join(data)

    async def fetch_channel_data(self):
        pass

    @staticmethod
    async def get_stream_info(stream_id: str, youtube_key: str=None) -> Dict:
        from .holodex import HolodexChannel
        stream_info = await HolodexChannel.get_stream_info(stream_id)
        if stream_info is not None:
            return stream_info
        from .youtube import YoutubeChannel
        stream_info = await YoutubeChannel.get_stream_info(stream_id, youtube_key)
        if stream_info is not None:
            return stream_info
        return None

    @staticmethod
    async def get_streams_info(self, ids: List[str]) -> List[Dict]:
        return []

    @staticmethod
    def check_channel_id(channel_id):
        return True

    @staticmethod
    def get_class(class_type: str):
        from .youtube import YoutubeChannel
        from .holodex import HolodexChannel
        if class_type == YoutubeChannel.__name__:
            return YoutubeChannel
        elif class_type == HolodexChannel.__name__:
            return HolodexChannel
        else:
            return Channel

    @staticmethod
    def get_class_by_name(name: str):
        from .youtube import YoutubeChannel
        from .holodex import HolodexChannel
        if name == YoutubeChannel.type_name:
            return YoutubeChannel
        elif name == HolodexChannel.type_name:
            return HolodexChannel
        else:
            return None

