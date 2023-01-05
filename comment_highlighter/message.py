from comment_highlighter.utils import *
from datetime import datetime, timezone, timedelta

class TrackedMessage():

    def __init__(self, **kwargs):
        self.message_id: int = kwargs.pop("message_id")
        self.hl_message_id: int = kwargs.pop("hl_message_id", 0)
        self.channel_id: int = kwargs.pop("channel_id")

        self.time: int = 0
        if "created_at" in kwargs:
            self.time = int(time.mktime(kwargs.pop("created_at").timetuple()))
        else:
            self.time = kwargs.pop("time")
    
    async def await_until_invalid(self):
        econds_left = track_time.total_seconds() + get_diff_datetime(message.created_at).total_seconds()
        # seconds_left = timedelta(seconds=30).total_seconds() + get_diff_datetime(message.created_at).total_seconds()
        if seconds_left > 0:
            await asyncio.sleep(seconds_left)
