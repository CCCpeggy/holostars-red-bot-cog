from stars.utils import *
from .channel import Channel
from typing import *
import xml.etree.ElementTree as ET

_, log = get_logger()

class YoutubeChannel(Channel):
    
    toke_name = "youtube"
    type_name = "youtube"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "YoutubeChannel"
        self.source_name: str = "YouTube"
        self.source_url: str = "https://www.youtube.com/"
    
    # def get_video_ids_from_feed(self, feed):
    #     try:
    #         root = ET.fromstring(feed)
    #     except:
    #         return []
    #     else:
    #         rss_video_ids = []
    #         for child in root.iter("{http://www.w3.org/2005/Atom}entry"):
    #             for i in child.iter("{http://www.youtube.com/xml/schemas/2015}videoId"):
    #                 rss_video_ids.append(i.text)
    #         return rss_video_ids
    
    async def get_youtube_token(self):
        return (await self._bot.get_shared_api_tokens("youtube"))["api_key"]

    async def fetch_channel_data(self) -> None:
        params = {
            "key": await self.get_youtube_token(),
            "id": self.id,
            "part": "snippet",
        }
        channel_url = f"https://www.googleapis.com/youtube/v3/channels"
        data = await getHttpData(channel_url, params)
        self.name = data["items"][0]["snippet"]["title"]
        self.url: str = f"https://www.youtube.com/channel/{self.id}"

    @staticmethod
    async def get_stream_info(stream_id: str, key: str) -> Dict:
        video_url = f"https://www.googleapis.com/youtube/v3/videos"
        params = {
            "key": key,
            "id": stream_id,
            "part": "id,liveStreamingDetails,snippet",
        }
        data = await getHttpData(video_url, params)
        if data is None or "items" not in data or len(data["items"]) == 0:
            return None
        data = data["items"][0]
        data_snippet = data["snippet"]
        data_details = data.get("liveStreamingDetails", {})

        # 判斷狀態
        scheduled = data_details.get("scheduledStartTime", None)
        start_actual = data_details.get("actualStartTime", None)
        end_actual = data_details.get("actualEndTime", None)
        status = "notsure"

        if end_actual is not None:
            status = "past"
        elif start_actual is not None:
            status = "live"
        elif scheduled is not None:
            status = "upcoming"

        return {
            "id": stream_id,
            "channel_id": data_snippet["channelId"],
            "title": data_snippet["title"],
            "type": None,
            "topic": None,
            "status": status, # TODO
            "start_actual": start_actual,
            "url": f"https://www.youtube.com/watch?v={stream_id}",
            "thumbnail": f"https://img.youtube.com/vi/{stream_id}/maxresdefault.jpg",
            "time": Time.to_datetime(scheduled) if scheduled else Time.get_now(),
            "source": None,
            "source_url": None
        }

    async def get_streams_info(self, ids: List[str]) -> List[Dict]:
        # channel_rss = "https://www.youtube.com/feeds/videos.xml?channel_id={self.id}"
        # rssdata = await getHttpDataText(channel_rss)
        # video_ids = self.get_video_ids_from_feed(rssdata)
        key = await self.get_youtube_token()
        new_videos = []
        for stream_id in ids:
            stream_info = await YoutubeChannel.get_stream_info(stream_id, key)
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