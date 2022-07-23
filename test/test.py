# redbot
from glob import glob
from redbot.core.i18n import Translator
from redbot.core import checks, commands, Config
from redbot.core.bot import Red


class Test(commands.Cog):
    def __init__(self, bot: Red, **kwargs):
        super().__init__()
        self.bot = bot
        