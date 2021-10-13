import os
import re
import json
import discord
import logging 
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Union
from config import Config, GuildConfig
from discord.ext import commands
log = logging.getLogger("HighLightMessage")
track_time = timedelta(hours=12)
# track_time = timedelta(seconds=30)
# config

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

# message

async def get_message(channel: discord.TextChannel, message_id: int):
    try:
        return await channel.fetch_message(message_id)
    except:
        return None

def get_diff_datetime(d1: datetime, d2: datetime=None):
    if not d2:
        d2 = datetime.now(timezone.utc)
    return d1 - d2

def is_need_highlight(message: discord.Message, threshold: int):
    diff = -get_diff_datetime(message.created_at)
    if diff > track_time:
        return False
    for r in message.reactions:
        if r.count >= threshold:
            print(diff)
            return True
    return False

def is_need_delete_highlight(message: discord.Message, threshold: int):
    for r in message.reactions:
        if r.count >= threshold - 5:
            return False
    return True

def sort_dict_by_value(data: dict):
    return {k: v for k, v in sorted(data.items(), key=lambda item: item[1])}

url_re_str = "(?P<url>https?://[^\s]+)"
url_re = re.compile(url_re_str)
empty_str = "[^ .,\n\r\t]"
empty_re = re.compile(empty_str)
def extract_url(message):
    return url_re.findall(message.content)

def is_only_url(message):
    urls = extract_url(message)
    if len(urls) == 0:
        return False
    tmp = message.content
    for url in urls:
        tmp = tmp.replace(url, "")
    return not empty_re.match(tmp)

def get_valid_emojis(message, threshold):
    emoji_count = {}
    for r in message.reactions:
        if r.count >= threshold:
            emoji_count[r] = r.count
    return sort_dict_by_value(emoji_count)

def add_attachment(embed, message):
    if message.attachments:
        attachment = message.attachments[0]
        spoiler = attachment.is_spoiler()
        if spoiler:
            embed.add_field(
                name="Attachment", value=f"||[{attachment.filename}]({attachment.url})||"
            )
        elif not attachment.url.lower().endswith(("png", "jpeg", "jpg", "gif", "webp")):
            embed.add_field(
                name="Attachment", value=f"[{attachment.filename}]({attachment.url})"
            )
        else:
            embed.set_image(url=attachment.url)
    return embed

def create_highlight_msg(payload, message, threshold):
    link = f'https://discordapp.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}'
    user = message.author
    name = user.nick if user.nick else user.name

    emoji_count = get_valid_emojis(message, threshold)
    emoji_msg = " | ".join([f"{e}  × **{c}**" for e, c in emoji_count.items()])
    # urls = utils.extract_url(message)
    if False and is_only_url(message):
        embed = discord.Embed(
            description=f'[傳送門]({link})',
            color=0xff9831
        )
        msg = f"{message.channel.mention} | {emoji_msg}\n{message.content}"
    else:
        embed = discord.Embed(
            description=f'{message.content}\n\n[傳送門]({link})',
            color=0xff9831
        )
        msg = f"{message.channel.mention} | {emoji_msg}"
    embed.set_author(name=name, icon_url=user.avatar)
    embed = add_attachment(embed, message)
    created_at_str = message.created_at.strftime("%Y/%m/%d, %H:%M:%S")
    embed.set_footer(text=created_at_str)
    return msg, embed

async def hl_timer(guild_config: GuildConfig, message: discord.Message):
    seconds_left = track_time.total_seconds() + get_diff_datetime(message.created_at).total_seconds()
    # seconds_left = timedelta(seconds=30).total_seconds() + get_diff_datetime(message.created_at).total_seconds()
    if seconds_left > 0:
        await asyncio.sleep(seconds_left)
    if message.id in guild_config.track:
        del guild_config.track[message.id]
        guild_config._parent.save()
        log.info(f"取消追蹤 {message.id}")

# async def sleep_12_hours(self):
#     await self.bot.wait_until_red_ready()
#     try:
#         tr_coros = []
#         for guild_id, members in (await self.config.all_members()).items():
#             guild: discord.Guild = self.bot.get_guild(int(guild_id))
#             for member_id, temp_roles in members.items():
#                 member: discord.Member = guild.get_member(int(member_id))
#                 for tr, ts in temp_roles["temp_roles"].items():
#                     role: discord.Role = guild.get_role(int(tr))
#                     tr_coros.append(self._tr_timer(member, role, ts))
#         await asyncio.gather(*tr_coros)
#     except Exception:
#         pass
