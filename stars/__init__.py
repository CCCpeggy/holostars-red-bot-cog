from .stars_stream import StarsStream
import json
from pathlib import Path

def setup(bot):
    star_stream_cog = StarsStream(bot)
    bot.add_cog(star_stream_cog)
