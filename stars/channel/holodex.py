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
        self.source_name: str = "YouTube"
        self.source_url: str = "https://www.youtube.com/"

    async def fetch_channel_data(self) -> None:
        channel_url = f"https://holodex.net/api/v2/channels/{self.id}"
        data = await getHttpData(channel_url)
        self.name = data["name"]
        self.url: str = f"https://www.youtube.com/channel/{self.id}"

    @staticmethod
    async def get_stream_info(stream_id: str) -> Dict:
        video_url = f"https://holodex.net/api/v2/videos/{stream_id}"
        try:
            video_info = await getHttpData(live_url)
            return {
                "id": video_info["id"],
                "channel_id": video_info["channel_id"],
                "title": video_info["title"],
                "type": video_info["type"],
                "topic": video_info.get("topic_id", None),
                "status": video_info.get("status"),
                "start_actual": video_info.get("start_actual"),
                "url": f"https://www.youtube.com/watch?v={video_info['id']}",
                "thumbnail": f"https://img.youtube.com/vi/{video_info['id']}/hqdefault.jpg",
                "time": Time.to_datetime(video_info["start_scheduled"]),
            }
        except:
            return None

    async def get_streams_info(self, ids: List[str]) -> List[Dict]:
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
                "start_actual": ori_video.get("start_actual"),
                "url": f"https://www.youtube.com/watch?v={ori_video['id']}",
                "thumbnail": f"https://img.youtube.com/vi/{ori_video['id']}/maxresdefault.jpg",
                "time": Time.to_datetime(ori_video["start_scheduled"]),
            }
            new_videos.append(new_video)
            if ori_video["id"] in ids:
                ids.remove(ori_video["id"])
        for stream_id in ids:
            stream_info = await HolodexChannel.get_stream_info(stream_id)
            if stream_info is not None:
                new_videos.append(stream_info)

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