# redbot
from redbot.core.i18n import Translator

# local
from .utils import *
from .streams import StreamsManager
from .channels import ChannelsManager
from .members import MembersManager

_, log = get_logger()

class Manager():
    def __init__(self, bot: Red, **kwargs):
        self.bot = bot
        self.channels_manager = ChannelsManager(bot, self)
        self.streams_manager = StreamsManager(bot, self)
        self.members_manager = MembersManager(bot, self)

   