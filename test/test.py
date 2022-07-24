# redbot
from redbot.core import checks, commands, Config
from redbot.core.bot import Red

log = logging.getLogger("red.core.cogs.Test")

class Test(commands.Cog):
    def __init__(self, bot: Red, **kwargs):
        super().__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        message.channel.debug(123)
        message.channel.debug(self.bot.get_channel(1000107429792587887).name)

        # await create_thread(*, name, auto_archive_duration=in-minutes)
        