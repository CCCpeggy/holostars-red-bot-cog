from redbot.core.utils.mod import is_mod_or_superior
from redbot.core import checks, commands, Config
from redbot.core.bot import Red
import asyncio
import random

class Talk(commands.Cog):

    global_defaults = {
        "learned_talk": {},
        "learned_talk_queue": []
    }

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, 21212121)
        self.config.register_global(**self.global_defaults)
        self.bot.loop.create_task(self.load_var())

    async def load_var(self):
        self.learned_talk = await self.config.learned_talk()
        self.learned_talk_queue = await self.config.learned_talk_queue()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if message.content == "":
            return
        await self.talk_bot(message)

    async def talk_bot(self, message):
        if message.author.id == 875013341007999037:
            return
        if not message.content.startswith("冷丸"):
            return
        if not await is_mod_or_superior(self.bot, message.author) and message.channel.id != 889525732122968074:
            return
        message.content = message.content.lower()
        if message.content.startswith("冷丸學"):
            tmp = message.content[3:].split(" ")
            que = tmp[0]
            ans = " ".join(tmp[1:])
            # que, ans = message.content[3:].split(" ")[:2]
            if que != "" and ans != "":
                if random.randint(0, 2) == 0:
                    if que in self.learned_talk_queue:
                        self.learned_talk_queue.remove(que)
                    self.learned_talk_queue.insert(0, que)
                    self.learned_talk[que] = ans
                    if len(self.learned_talk_queue) > 300:
                        old_que = self.learned_talk_queue.pop()
                        del old_que
                    await self.config.learned_talk.set(self.learned_talk)
                    await self.config.learned_talk_queue.set(self.learned_talk_queue)
                    await message.channel.send("大概有機會記住了")
                else:
                    await message.channel.send("不要")
            else:
                await message.channel.send("嘖嘖")
        elif message.content.startswith("冷丸選"):
            tmp = message.content[3:].split(" ")
            que = tmp[0]
            ans = list(set(tmp[1:]))
            if "" in ans:
                ans.remove("")
            # que, ans = message.content[3:].split(" ")[:2]
            if que != "" and len(ans) > 0:
                if random.randint(0, 2) == 0:
                    if que in self.learned_talk_queue:
                        self.learned_talk_queue.remove(que)
                    self.learned_talk_queue.insert(0, que)
                    self.learned_talk[que] = ans
                    if len(self.learned_talk_queue) > 300:
                        old_que = self.learned_talk_queue.pop()
                        del old_que
                    await self.config.learned_talk.set(self.learned_talk)
                    await self.config.learned_talk_queue.set(self.learned_talk_queue)
                    await message.channel.send("大概有機會記住了")
                else:
                    await message.channel.send("不要")
            else:
                await message.channel.send("嘖嘖")
        elif message.content[2:] in self.learned_talk_queue:
            ans = self.learned_talk[message.content[2:]]
            if isinstance(ans, str):
                await message.channel.send(ans)
            else:
                await message.channel.send(random.choice(ans))
        elif "天才" in message.content:
            await message.add_reaction("<:Te_tensai:887747027637792888>")
            await message.channel.send("<:Te_tensai:887747027637792888>")
        elif "天真" in message.content or "3D" in message.content:
            await message.add_reaction("<:Te_tensai:887747027637792888>")
            await message.channel.send("天真天才！<:Te_tensai:887747027637792888>")
        elif "月嵐" in message.content:
            await message.channel.send("月嵐 3150")
        elif "可愛" in message.content:
            if "比" in message.content:
                await message.channel.send("冷丸最可愛！")
            else:
                await message.channel.send(f"比{random.choice(['咖咩醬', '虛無雀', '天真'])}更可愛！")
        elif "在" in message.content:
            await message.channel.send(random.choice(["不在", "不在", "在"]))
        elif "娶" in message.content:
            await message.channel.send("Noo")
        elif "椰香" in message.content or "椰子" in message.content or "綠色乖乖" in message.content:
            await message.channel.send("<:As_bonk:887746980179247194><:As_bonk:887746980179247194>")
        elif "乖乖" in message.content:
            await message.channel.send("No" + "o" * random.randint(0, 20))
        elif "歐姆" in message.content:
            await message.channel.send("v=ir => av=air => 色即是空")
        elif "程式" in message.content or "代碼" in message.content:
            code = [
"""```C++
#include<iostream>
int main(){
    printf("Re: Hello world");
}
```""",
"""```C++
if () {

}
else if {

}
else {

}
```""",
"""```C++
while() {

}
```""",
"""```C++
for(;;) {
    
}
```"""]
        elif "python" in message.content:
            code = [
"""```python
# 輸入 + 輸出輸入的文字
a = input("請輸入一段文字")
print(a)
```""",
"""```python
# 輸出 + 不同型態
print("Re: Hello world") # 這是字串型態，並且輸出
print(1 + 2) # 這是數字型態，並且輸出
```""",
"""```python
# 引入其他函式庫(引入後就可以用它的功能)
import random
print(random.randint(1, 20)) # 輸出 1 - 20 之間的隨機數
```""",
"""```python
# list
i_am_list = ["i", "have", "an", "apple"]
print(i_am_list[3]) # 輸出 apple，因為 list 的編號式從 0 開始的，其中 0: i, 1: have, 2: an, 3: apple
```""",
"""```python
# if
content = "冷丸在嗎"
if "在" in content:
    print("不在")
```""",
"""```python
# if
content = "冷丸可愛嗎"
if "在" in content:
    print("不在")
elif "可愛" in content:
    print("比咖咩醬可愛")
```""",
"""```python
# if
content = "冷丸你會化學嗎"
if "在" in content:
    print("不在")
elif "可愛" in content:
    print("比咖咩醬可愛")
else:
    print("chi chi~")
```""",
"""```python
# 定義函式做到兩數傳入後回傳相加的結果
def add(num1, num2):
    return num1 + num2
print(add(1, 2))
```""",
"""```python
# 輸出字串
print("Re: Hello world")
```"""]
            await message.channel.send(random.choice(code))
        elif "機器人" in message.content:
            await message.channel.send("<:Ri_2GB_1:887732339600404490><:Ri_2GB_2:887732340825141318><:Ri_2GB_3:887732339982094366>")
        elif "廁所" in message.content:
            await message.channel.send("<:Roberu_question:887748105234174014>")
        elif "外掛" in message.content:
            await message.channel.send("!?")
        elif "本物" in message.content:
            await message.channel.send("Yesss")
        elif "籤" in message.content:
            await message.channel.send("平" * random.randint(1, 12))
        elif "吃雞" in message.content or "champion" in message.content or "冠軍" in message.content:
            await message.channel.send("蝦?????")
        elif "apex" in message.content:
            await message.channel.send("apex 31500000")
        elif "nice" in message.content:
            await message.channel.send("niceeeee")
        elif "性別" in message.content:
            await message.channel.send("女生")
        elif "吃" in message.content:
            await message.channel.send("不吃")
        elif "睡" in message.content:
            await message.channel.send("z" * random.randint(3, 20))
        elif "圓周率" in message.content:
            await message.channel.send("3.141592653589793238462643383279502884197169399375105820974944592307816406286203998")
        elif "貼貼" in message.content:
            await message.channel.send("<:Tee_Ro:887762077626794027><:Tee_Te:887762077689720953>")
        elif "對不起" in message.content:
            await message.channel.send(":pleading_face:")
        elif "不乖" in message.content or"叛逆" in message.content:
            await message.channel.send(":pleading_face:")
        elif "定理" in message.content or"定律" in message.content or "數學" in message.content or "物理" in message.content or "化學" in message.content or "生物" in message.content or "公式" in message.content or "喜歡誰" in message.content or "比" in message.content or "社會" in message.content or "歷史" in message.content:
            await message.channel.send("<:Sh_hmmm:887761992352407552> ")
        elif "乖" in message.content:
            await message.channel.send("No" + "o" * random.randint(0, 20))
        elif "棒" in message.content:
            await message.channel.send("<:As_bonk:887746980179247194>")
        elif "幫" in message.content:
            await message.channel.send("<:Te_gg:887747027180597278>")
        elif "a-z" in message.content:
            await message.channel.send("kMGTPEZY")
        elif "嗎" not in message.content and ("摸" in message.content or "喜歡" in message.content or "fire" in message.content or "water" in message.content):
            await message.channel.send("Fire" + "e" * random.randint(0, 10))
        elif "早" in message.content or "午" in message.content or "晚" in message.content:
            await message.channel.send("不好")
        elif "主人" in message.content:
            await message.channel.send("<:Sh_hmmm:887761992352407552>")
        elif "我" in message.content:
            await message.channel.send(f"I don't know you.")
        elif ":As_bonk:" in message.content:
            await message.channel.send("<:As_bonk:887746980179247194><:As_bonk:887746980179247194>")
        elif "會" in message.content and "嗎" in message.content:
            await message.channel.send("不會！")
        elif "黑" in message.content and "嗎" in message.content:
            await message.channel.send("白的！")
        elif "嗎" in message.content or "嘛" in message.content or "?" in message.content or "？" in message.content:
            await message.channel.send("不知道")
        elif "(" in message.content:
            await message.channel.send("(天才")
        elif "（" in message.content:
            await message.channel.send("（天才")
        else:
            await message.channel.send(random.choice(["chi~", "chi chi~", "chi chi chi~"]))
    
