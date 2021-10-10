import json
import utils
import asyncio
import discord
from datetime import datetime, timezone, timedelta
from discord.ext import commands

class MessageTrack():
    def __init__(self, **kwargs):
        self.hl_msg_id = kwargs.pop("hl_msg_id")
        self.ori_channel_id = kwargs.pop("ori_channel_id", 884066992762523649)

    def export(self):
        data = {}
        for k, v in self.__dict__.items():
            if not k.startswith("_"):
                data[k] = v
        return data

class GuildConfig():

    def __init__(self, bot: commands.Bot, parent, **kwargs):
        self._bot = bot
        self._parent = parent
        detect = kwargs.pop("detect", {})
        self.detect = {}
        for k, v in detect.items():
            self.detect[int(k)] = v
        self.send_channel_id = kwargs.pop("send_channel_id", None)

        self.track = {}
        track = kwargs.pop("track", {})
        if len(track) > 0:
            for k, v in track.items():
                self.track[int(k)] = MessageTrack(**v)
            bot.loop.create_task(self.handle_track())

    def append_track(self, ori_msg: discord.Message, hl_msg: discord.Message):
        self.track[ori_msg.id] = MessageTrack(
            hl_msg_id=hl_msg.id, 
            ori_channel_id=ori_msg.channel.id
        )
        self._parent.save()

    async def handle_track(self):
        tasks = []
        delete_key = []
        for k, v in self.track.items():
            channel = self._bot.get_channel(v.ori_channel_id)
            message = await channel.fetch_message(k)
            if message:
                tasks.append(utils.hl_timer(self, message))
            else:
                delete_key.append(k)
        if len(delete_key):
            for k in delete_key:
                del self.track[k]
            self._parent.save()
        await asyncio.gather(*tasks)
    
    def export(self):
        data = {}
        for k, v in self.__dict__.items():
            if k == "track":
                data[k] = {}
                for msg_id, msg_data in v.items():
                    data[k][msg_id] = msg_data.export()
            elif not k.startswith("_"):
                data[k] = v
        return data


class Config():

    def __init__(self, bot: commands.Bot, **kwargs):
        self._bot = bot
        self._filename = kwargs.pop("filename", "settings.json")
        self.config = {}
        for guild_id_str, guild_config_str in kwargs.pop("config", {}).items():
            self.config[int(guild_id_str)] = GuildConfig(bot, self, **guild_config_str)

    def export(self):
        data = {}
        for k, v in self.__dict__.items():
            if k == "config":
                data[k] = {}
                for guild_id, guild_config in v.items():
                    data[k][guild_id] = guild_config.export()
            elif not k.startswith("_"):
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

    def get(self, guild_id):
        if guild_id not in self.config:
            self.config[guild_id] = GuildConfig(self._bot, self)
        return self.config[guild_id]