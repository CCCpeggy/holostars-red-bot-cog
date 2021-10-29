import json
import asyncio
import discord
from datetime import datetime, timezone, timedelta
from discord.ext import commands

class Config():

    def __init__(self, bot: commands.Bot, **kwargs):
        self._bot = bot
        self._filename = kwargs.pop("filename", "settings.json")
        self.token = kwargs.pop("token", None)
        self.channel_ids = kwargs.pop("channel_ids", [])
        self.pin_queue_ids = kwargs.pop("pin_queue_ids", [])

    def export(self):
        data = {}
        for k, v in self.__dict__.items():
            if not k.startswith("_"):
                data[k] = v
        return data
        
    def save(self):
        try:
            raw_data = self.export()
        except:
            raise Exception
        else:
            f = open(self._filename, "w")
            json.dump(raw_data, f)
            f.close()
