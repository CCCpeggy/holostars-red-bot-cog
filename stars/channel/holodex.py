from stars.utils import *
from .channel import Channel
from typing import *

_, log = get_logger()

class HolodexChannel(Channel):
    
    toke_name = "holodex"
    type_name = "holodex"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "HolodexChannel"

    async def fetch_channel_data(self) -> None:
        channel_url = f"https://holodex.net/api/v2/channels/{self.id}"
        data = await getHttpData(channel_url)
        self.name = data["name"]

    async def get_streams_info(self) -> List[Dict]:
        live_url = f"https://holodex.net/api/v2/live"
        params = {
            "channel_id": self.id,
        }
        ori_videos = await getHttpData(live_url, params)
        new_videos = []
        for ori_video in ori_videos:
            new_video = {
                "id": ori_video["id"],
                "channel_id": self.id,
                "title": ori_video["title"],
                "type": ori_video["type"],
                "topic": ori_video.get("topic_id", None),
                "status": ori_video.get("status"),
                "time": Time.to_datetime(ori_video["start_scheduled"]),
            }
            new_videos.append(new_video)
        return new_videos
    
    def __repr__(self):
        data = super().__repr__()
        data += "\n".join([
            # f"> 頻道 ID：{self.id}",
        ])
        return data

    @staticmethod
    def check_channel_id(channel_id):
        return Youtube.check_channel_id(channel_id)