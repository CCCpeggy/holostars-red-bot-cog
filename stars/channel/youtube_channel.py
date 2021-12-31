# local
from stars.utils import *
from .channel import Channel

_, log = get_logger()

class YoutubeChannel(Channel):
    
    toke_name = "youtube"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "YoutubeChannel"