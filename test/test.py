import discord
from discord.utils import get
from discord.ext import commands
import logging
import asyncio
import os
import re

client = discord.Client()

mm = ""
mm = ""
    
@client.event
async def on_message(message):
    if message.channel.id == 911486701656997938 or message.channel.id == 864755730677497876 :
        # mm[message.id] = []
        if message.content == "投票":
            await message.add_reaction("<:1_1Miyabi:890277022658592800>")
            await message.add_reaction("<:1_2Izuru:890278709297287279>")
            await message.add_reaction("<:1_3Arurandeisu:890279210839597137>")
            await message.add_reaction("<:1_4Rikka:890279428016443443>")
            await message.add_reaction("<:1_5Astel:890280329741484032>")
            await message.add_reaction("<:1_6Temma:890280329724694579>")
            await message.add_reaction("<:1_7Roberu:890280329741471754>")
            await message.add_reaction("<:1_8Shien:890280329909252126>")
            await message.add_reaction("<:1_9Oga:890280329812787211>")
        if message.content == "結果" and message.reference:
            ref_msg_id = message.reference.message_id
            ref_msg = await message.channel.fetch_message(ref_msg_id)
            d = ""
            for r in ref_msg.reactions:
                async for user in r.users():
                    if user.id != 875013341007999037:
                        d += '{0.name}: {1.emoji}\n'.format(user, r)
            if d != "":
                await message.channel.send(d)
        elif message.content.startswith("結果") and message.reference:
            ref_msg_id = message.reference.message_id
            ref_msg = await message.channel.fetch_message(ref_msg_id)
            e = message.content[2:]
            p = re.compile('<:\w*:[0-9]*>')
            e = p.match(e)
            if e:
                e = e.group()
                d = ""
                for r in ref_msg.reactions:
                    if str(r) == e:
                        async for user in r.users():
                            if user.id != 875013341007999037:
                                d += '{0.name}: {1.emoji}\n'.format(user, r)
                if d != "":
                    await message.channel.send(d)

# @client.event
# async def on_raw_reaction_add(payload):
#     msg_channel = client.get_channel(payload.channel_id)
#     message = await msg_channel.fetch_message(payload.message_id)
#     if message.id in mm:
#         mm[message.id].append(": ".join([message.author.name, payload.emoji]))


if __name__ == "__main__":
    client.run("ODc1MDEzMzQxMDA3OTk5MDM3.YRPVrQ.EmX4gTRm_6ZrIwHoVhmRjsRCr4U")
