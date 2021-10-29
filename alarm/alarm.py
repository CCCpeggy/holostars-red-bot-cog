import discord
import logging
from redbot.core.bot import Red
from redbot.core import commands, Config
from redbot.core.i18n import cog_i18n, Translator

_ = Translator("StarStreams", __file__)
log = logging.getLogger("red.core.cogs.Alarm")

class Alarm(commands.Cog):

    global_defaults = {
        "refresh_timer": 100000,
        "tokens": {},
        "streams": [],
        "scheduled_streams": [],
    }
    def __init__(self, bot: Red):
        super().__init__()
        self.config: Config = Config.get_conf(self, 27272727)
        self.config.register_global(**self.global_defaults)
        self.bot: Red = bot
        self._init_task: asyncio.Task = self.bot.loop.create_task(
            self.load_streams())
    
    async def load_streams(self):
        self.streams = await self.config.streams()
        return
        streams = []
        for raw_stream in await self.config.streams():
            streams.append(YouTubeStream(**raw_stream))

        return streams
    
    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, message):
        print(self.streams)
