from stars.utils import *
from .channel import Channel

_, log = get_logger()

class HolodexChannel(Channel):
    
    toke_name = "holodex"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "YoutubeChannel"
    
    def __repr__(self):
        data = super().__repr__()
        data += "\n".join([
            # f"> 頻道 ID：{self.id}",
        ])
        return data