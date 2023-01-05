import re
import discord
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Union
from config import Config, GuildConfig
track_time = timedelta(hours=12)

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
    created_at_str = (message.created_at + timedelta(hours=8)).strftime("%Y/%m/%d, %H:%M:%S")
    embed.set_footer(text=created_at_str)
    return msg, Embed
