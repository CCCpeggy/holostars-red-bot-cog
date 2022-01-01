# redbot
from redbot.core.i18n import Translator

# local
from .utils import *
from .streams import StreamsManager
from .channels import ChannelsManager
from .members import MembersManager
from .send import SendManager

_, log = get_logger()

class Manager():
    def __init__(self, bot: Red, **kwargs):
        self.bot = bot
        self.channels_manager: "ChannelsManager" = ChannelsManager(bot, self)
        bot.add_cog(self.channels_manager)
        self.streams_manager: "StreamsManager" = StreamsManager(bot, self)
        bot.add_cog(self.streams_manager)
        self.members_manager: "MembersManager" = MembersManager(bot, self)
        bot.add_cog(self.members_manager)
        self.send_manager: "SendManager" = SendManager()
        bot.add_cog(self.send_manager)

   