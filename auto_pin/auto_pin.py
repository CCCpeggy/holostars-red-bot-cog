#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import os
import json
import discord
import logging
import asyncio
import contextlib
from config import Config
from discord.utils import get
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='釘選', intents=intents)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='auto_pin.log',
                    filemode='a')
log = logging.getLogger("AutoPin")
emojis = {
    "\U0001F4CC	": "Done",
    "\U0000274C": "Cancel"
}

def load_config(bot: commands.Bot, filename="settings.json"):
    if os.path.isfile(filename):
        f = open(filename, "r")
        config_json = json.loads(f.read())
        f.close()
        return Config(bot, **config_json, filename="settings.json")
    config = Config(bot)
    config.save()
    log.info(f"創了 {filename}")
    return config

@bot.command(name='設置開')
@commands.guild_only()
@commands.check_any(commands.has_role('mod'), commands.has_role('Mod（有問題就@）'))
async def _set(ctx, channel: discord.TextChannel):
    """ 設定頻道開啟
    """
    if channel.id not in config.channel_ids:
        config.channel_ids.append(channel.id)
        config.save()
    await ctx.channel.send(f"{channel.mention} 已開啟")

@bot.command(name='設置關閉')
@commands.guild_only()
@commands.check_any(commands.has_role('mod'), commands.has_role('Mod（有問題就@）'))
async def _set(ctx, channel: discord.TextChannel):
    """ 設定頻道關閉
    """
    if channel.id in config.channel_ids:
        config.channel_ids.remove(channel.id)
        config.save()
    await ctx.channel.send(f"{channel.mention} 已關閉")

async def get_message(channel, message_id):
    try:
        message = await channel.fetch_message(message_id)
    except:
        return False
    else:
        return message

@bot.command(name='訊息')
@commands.guild_only()
async def _auto_pin(ctx):
    if ctx.channel.id not in config.channel_ids:
        if ctx.channel.parent_id not in config.channel_ids:
            print("沒有權限")
            return
    if not ctx.message.reference:
        ctx.channel.send("沒有回覆釘選訊息")
        return
    message_id = ctx.message.reference.message_id
    ref_msg = await get_message(ctx.channel, message_id)
    if not ref_msg:
        await ctx.channel.send("訊息找不到")
        return
    if ref_msg.pinned:
        await ctx.channel.send("已經釘選了！")
        return
    await ref_msg.pin()
    config.pin_queue_ids.append(ctx.message.id)

    if len(config.pin_queue_ids) > 12:
        config.pin_queue_ids = config.pin_queue_ids[1:]
    config.save()

    emojis_list = list(emojis.keys())
    async def add_reaction():
        with contextlib.suppress(discord.NotFound):
            for emoji in emojis_list:
                await ctx.message.add_reaction(emoji)
    task = asyncio.create_task(add_reaction())

@bot.event
@commands.guild_only()
async def on_raw_reaction_add(payload):
    if payload.message_id not in config.pin_queue_ids:
        return
    msg_channel = bot.get_channel(payload.channel_id)
    message = await msg_channel.fetch_message(payload.message_id)

    count0 = 0
    count1 = 0
    for r in message.reactions:
        if emojis[r.emoji] == "Done":
            count0 = r.count
        if emojis[r.emoji] == "Cancel":
            count1 = r.count
    if count1 > count0:
        ref_msg_id = message.reference.message_id
        ref_msg = await get_message(msg_channel, ref_msg_id)
        if ref_msg:
            config.pin_queue_ids.remove(payload.message_id)
            await ref_msg.unpin()
            config.save()


if __name__ == "__main__":
    config = load_config(bot)
    if not config.token:
        config.token = input("請輸入 token: ")
        config.save()
    bot.run(config.token)
