# local
from stars.utils import *
from .channel import Channel

_, log = get_logger()

class YoutubeChannel(Channel):
    
    toke_name = "youtube"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "YoutubeChannel"
    
    def __repr__(self):
        data = super().__repr__()
        data += "\n".join([
            # f"> 頻道 ID：{self.id}",
        ])
        return data