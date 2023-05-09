# redbot
from redbot.core import checks, commands, Config
from redbot.core.bot import Red
import discord

from typing import *


import logging
def get_logger(level: int=logging.DEBUG)->logging.Logger:
    from redbot.core.i18n import Translator
    _ = Translator("Test", __file__)
    log = logging.getLogger("red.core.cogs.Test")
    log.setLevel(level)
    return _, log
_, log = get_logger()

class Test(commands.Cog):
    def __init__(self, bot: Red, **kwargs):
        super().__init__()
        self.bot = bot

    @commands.command(name="t")
    async def set_standby_textchannel(self, ctx: commands.Context, emoji_name: str, emoji_id: int, gif: bool):
        emoji = f"<a:{emoji_name}:{emoji_id}>" if gif else f"<:{emoji_name}:{emoji_id}>"
        log.warning(emoji)
        msg = await ctx.send(f"加上 {emoji}" )
        await msg.add_reaction(emoji)
        # for i in range(0, len(ctx.guild.emojis), 10):
        #     end = min(i+10, len(ctx.guild.emojis))
        #     emojis = [f"<:{emoji.name}:{emoji.id}>" if emoji.animated else f"<a:{emoji.name}:{emoji.id}>" for emoji in ctx.guild.emojis[i:end]]
        #     all_emoji = ", ".join(emojis)
        #     log.info(all_emoji)
        #     # await ctx.send(all_emoji)