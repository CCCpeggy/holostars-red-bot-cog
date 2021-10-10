import discord
import utils
from discord.utils import get
from discord.ext import commands
import logging
import asyncio
import os

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='-h', intents=intents)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='highlight.log',
                    filemode='a')
log = logging.getLogger("HighLightMessage")
config = utils.load_config(bot)

@bot.event
async def on_ready():
    config.bot_ready()

@bot.group(name='l')
@commands.guild_only()
@commands.check_any(commands.has_role('mod'), commands.has_role('Mod（有問題就@）'))
async def _highlight(ctx):
    """ highlight
    """
    pass

@_highlight.command(name='help')
async def _help(ctx):
    info = """這是用來偵測精華留言的機器人
當表符達到某個數值時，就會被認作精華留言
指令清單：
`-hl help` 說明
`-hl channel [discord.TextChannel] [達成數量]` 設定特定頻道成為精華留言的達成數量
`-hl send [discord.TextChannel]` 設定精華留言的發送頻道
    """
    await ctx.channel.send(info)

@_highlight.command(name='channel')
async def _highlight_channel(ctx, channel: discord.TextChannel, count: int):
    guild_config = config.get(ctx.guild.id)
    guild_config.detect[channel.id] = count
    config.save()
    await ctx.channel.send(f"理論上設定完成")

@_highlight.command(name='send')
async def _highlight_channel(ctx, channel: discord.TextChannel):
    guild_config = config.get(ctx.guild.id)
    guild_config.send_channel_id = channel.id
    config.save()
    await ctx.channel.send(f"理論上設定完成")

@_highlight.command(name='list')
async def _highlight_channel(ctx):
    guild_config = config.get(ctx.guild.id)

    # 取得精華留言頻道
    send_channel_id = guild_config.send_channel_id
    send_channel = bot.get_channel(send_channel_id)

    channel_data = []
    # 個別頻道達成表符數量
    for k, v in guild_config.detect.items():
        channel = bot.get_channel(k)
        channel_data.append(f"> #{channel.name}: {v}")
    channel_data = "\n".join(channel_data)

    data = f"""伺服器設定
精華留言頻道：{send_channel.mention if send_channel else None}
達成表符數量：
{channel_data}
"""
    await ctx.channel.send(data)


@bot.event
@commands.guild_only()
async def on_raw_reaction_remove(payload):
    if not config:
        return
    guild_config = config.get(payload.guild_id)
    if payload.message_id not in guild_config.track:
        return
    threshold = guild_config.detect[payload.channel_id]
    msg_channel = bot.get_channel(payload.channel_id)
    message = await msg_channel.fetch_message(payload.message_id)
    send_channel = bot.get_channel(guild_config.send_channel_id)
    if utils.is_need_delete_highlight(message, threshold):
        hl_msg_id = guild_config.track[message.id].hl_msg_id
        hl_msg = await send_channel.fetch_message(hl_msg_id)
        log.info(f"刪除 {message.id} 的精華 {hl_msg.id}")
        await hl_msg.delete()

@bot.event
@commands.guild_only()
async def on_raw_reaction_add(payload):
    if not config:
        return
    guild_config = config.get(payload.guild_id)
    if payload.channel_id not in guild_config.detect:
        return
    threshold = guild_config.detect[payload.channel_id]
    msg_channel = bot.get_channel(payload.channel_id)
    message = await msg_channel.fetch_message(payload.message_id)
    send_channel = bot.get_channel(guild_config.send_channel_id)
    # member = message.guild.get_member(message.author.id)
    if message.content != "" and message.content[0] in ["!", "-"]:
        return
    # def create_highlight_msg():
    #     link = f'https://discordapp.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}'
    #     user = message.author
    #     name = user.nick if user.nick else user.name

    #     emoji_count = utils.get_valid_emojis(message, threshold)
    #     emoji_msg = " | ".join([f"{e}  × **{c}**" for e, c in emoji_count.items()])
    #     if utils.is_only_url(message):
    #         msg = f"{msg_channel.mention} | {emoji_msg}\n\n{message.content}\n\n傳送門：{link}"
    #         return msg, None
    #     else:
    #         embed = discord.Embed(
    #             description=f'{message.content}\n\n[傳送門]({link})',
    #             color=0xff9831
    #         )
    #         embed.set_author(name=name, icon_url=user.avatar)
    #         embed = utils.add_attachment(embed, message)
    #         msg = f"{msg_channel.mention} | {emoji_msg}"
    #         return msg, embed

    def create_highlight_msg():
        link = f'https://discordapp.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}'
        user = message.author
        name = user.nick if user.nick else user.name

        emoji_count = utils.get_valid_emojis(message, threshold)
        emoji_msg = " | ".join([f"{e}  × **{c}**" for e, c in emoji_count.items()])
        # urls = utils.extract_url(message)
        if False and utils.is_only_url(message):
            embed = discord.Embed(
                description=f'[傳送門]({link})',
                color=0xff9831
            )
            msg = f"{msg_channel.mention} | {emoji_msg}\n{message.content}"
        else:
            embed = discord.Embed(
                description=f'{message.content}\n\n[傳送門]({link})',
                color=0xff9831
            )
            msg = f"{msg_channel.mention} | {emoji_msg}"
        embed.set_author(name=name, icon_url=user.avatar)
        embed = utils.add_attachment(embed, message)
        created_at_str = message.created_at.strftime("%Y/%m/%d, %H:%M:%S")
        embed.set_footer(text=created_at_str)
        return msg, embed


    # 判斷是否已發送，已發送則更新
    if message.id in guild_config.track:
        msg, embed = create_highlight_msg()
        hl_msg_id = guild_config.track[message.id].hl_msg_id
        hl_msg = await send_channel.fetch_message(hl_msg_id)
        log.info(f"修改 {message.id} 的精華 {hl_msg.id}")
        await hl_msg.edit(msg, embed=embed)

    elif utils.is_need_highlight(message, threshold):
        msg, embed = create_highlight_msg()
        hl_msg = await send_channel.send(msg, embed=embed)
        guild_config.append_track(message, hl_msg)
        log.info(f"新增 {message.id} 的精華 {hl_msg.id}")
        await utils.hl_timer(guild_config, message)
        
        

if __name__ == "__main__":
    if not config.token:
        config.token = input("請輸入 token: ")
        config.save()
    bot.run(config.token)