# discord
import discord

# redbot
from redbot.core.bot import Red
from redbot.core import commands

# other
from typing import *

import logging

def getEmoji(guild_emojis, ori_emoji):
    if ori_emoji is None:
        return None
    # check guild
    for e in guild_emojis:
        if str(e.id) in ori_emoji and e.name in ori_emoji:
            return e
    # check emoji dictionary
    import emoji
    if ori_emoji in emoji.EMOJI_DATA:
        return ori_emoji
    return None

class EmojiConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg_emoji: str) -> str:
        emoji = getEmoji(ctx.guild.emojis, arg_emoji)
        if emoji:
            return emoji
        else:
            raise commands.BadArgument(arg_emoji + " is bad emoji!!")

class ConvertToRawData:
    @staticmethod
    def export_class(data):
        export_func = getattr(data, "export", None)
        if callable(export_func):
            return data.export()
        else:
            from datetime import datetime
            from enum import Enum
            raw_data = {}
            for k, v in data.__dict__.items():
                if k.startswith("_"):
                    continue
                if not v:
                    raw_data[k] = None
                elif isinstance(v, (int, str, list, dict, Enum)):
                    raw_data[k] = v
                elif isinstance(v, datetime):
                    raw_data[k] = Time.to_standard_time_str(v)
                else:
                    raw_data[k] = v.id
        return raw_data

    @staticmethod
    def dict(data: dict):
        raw_data = {}
        for key, value in data.items():
            raw_data[str(key)] = ConvertToRawData.export_class(value)
        return raw_data

    @staticmethod
    def list(data: list):
        raw_data = []
        for value in data:
            raw_data.append(ConvertToRawData.export_class(value))
        return raw_data
