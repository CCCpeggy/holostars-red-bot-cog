from redbot.core import checks, commands, Config
from redbot.core.bot import Red
import asyncio

def setup(bot):
    bot.add_cog(Test(bot))

class Test(commands.Cog):
    def __init__(self, bot: Red):
        self.bot: Red = bot
    
    async def get_message(self, channel, message_id):
        try:
            message = await channel.fetch_message(message_id)
        except:
            return False
        else:
            return message

    async def cycle_pin(self, channel):
        pins = await channel.pins()
        print(f"Total pin message: {len(pins)}")
        bot_pin_count = 0
        unpin_count = 0
        remain_pin = 15
        for i in range(len(pins)):
            print(f"Author {pins[i].author.id}")
            if pins[i].author.id == 875013341007999037:
                if bot_pin_count > remain_pin:
                    unpin_count += 1
                    await pins[i].unpin()
                    await asyncio.sleep(1)
                    print(f"Unpinned {pins[i].content}")
                bot_pin_count += 1
        print(f"Unpinned {unpin_count} messages from {channel.mention}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == 864755730677497876:
            if message.channel.content == "投票":
                message.add_reaction("<:Sh_hmmm:887761992352407552>")
                await message.add_reaction("<:1_1Miyabi:890277022658592800>")
                await message.add_reaction("<:1_2Izuru:890278709297287279>")
                await message.add_reaction("<:1_3Arurandeisu:890279210839597137>")
                await message.add_reaction("<:1_4Rikka:890279428016443443>")
                await message.add_reaction("<:1_5Astel:890280329741484032>")
                await message.add_reaction("<:1_6Temma:890280329724694579>")
                await message.add_reaction("<:1_7Roberu:890280329741471754>")
                await message.add_reaction("<:1_8Shien:890280329909252126>")
                await message.add_reaction("<:1_9Oga:890280329812787211>")
        # await msg.add_reaction("<:Te_tensai:887747027637792888>")
        # if message.channel.id == 884066848822427708:
        #     if message.author.id == 405327571903971333:#889015029377138739:
        #         await self.cycle_pin(message.channel)
                # msg = await self.get_message(message.channel, 889028951475908630)
        #         await message.channel.send(f"-gstars add {msg.embeds[0].url.split('=')[-1]}")
        #         await message.channel.send(f"-gstars check")
        