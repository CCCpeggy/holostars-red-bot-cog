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
        if message.channel.id in [889525732122968074, 861601484735381514]:
            if message.content.startswith("!t "):
                await message.add_reaction("\U00002B50")
                await message.add_reaction("\U0000274C")
            if message.content.startswith("!tags"):
                await message.channel.send("這個沒有作用啦")
        if not message.content.startswith("冷丸"):
            return
        if not await is_mod_or_superior(self.bot, message.author) and message.channel.id != 889525732122968074:
            return
        message.content = message.content.lower()
        author_name = message.author.nick if message.author.nick else message.author.name
        if message.content.startswith("冷丸學"):
            tmp = message.content[3:].split(" ")
            que = tmp[0]
            ans = " ".join(tmp[1:])
            # que, ans = message.content[3:].split(" ")[:2]
            if que != "" and ans != "":
                if random.randint(0, 20) != 0:
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
                    await message.channel.send("這不好說")
            else:
                await message.channel.send("嘖嘖")
        elif message.content.startswith("冷丸忘"):
            key = message.content[3:].split(" ")[0]
            if key in self.learned_talk_queue:
                self.learned_talk_queue.remove(key)
                self.learned_talk.pop(key)
                await self.config.learned_talk.set(self.learned_talk)
                await self.config.learned_talk_queue.set(self.learned_talk_queue)
                await message.channel.send(f"{key} 是什麼可以吃嗎")
            else:
                await message.channel.send("我沒學過那個東西")
        elif message.content.startswith("冷丸現在選"):
            tmp = message.content[5:].split(" ")
            ans = list(set(tmp[1:]))
            if "" in ans:
                ans.remove("")
            if len(ans) >= 2:
                if "睡覺" in ans:
                    await message.channel.send("睡覺")
                elif random.randint(0, 40) != 0:
                    await message.channel.send(random.choice(ans))
                else:
                    await message.channel.send("這不好說")
            else:
                await message.channel.send("嘖嘖")
        elif message.content.startswith("冷丸選"):
            tmp = message.content[3:].split(" ")
            que = tmp[0]
            ans = list(set(tmp[1:]))
            if "" in ans:
                ans.remove("")
            if que != "" and len(ans) >= 2:
                if random.randint(0, 20) != 0:
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
                    await message.channel.send("這不好說")
            else:
                await message.channel.send("嘖嘖")
        elif message.content.startswith("冷丸說"):
            if message.reference:
                ref_msg_id = message.reference.message_id
                ref_msg = await self.get_message(message.channel, ref_msg_id)
                await ref_msg.reply(message.content[3:], mention_author=False)
            else:
                await message.channel.send(message.content[3:])
            await message.delete()
        elif message.content == "冷丸功能":
            info = \
"""
冷丸學[項目] [內容]
冷丸選[項目] [選項1] [選項2] ... (這個會記住，`冷丸[項目]` 才會出現結果)
冷丸忘[項目] 
冷丸現在選[項目] [選項1] [選項2] ...
冷丸 + 機率
冷丸 + 籤
冷丸 + 人氣投票
需要的話也可以跟冷丸要個抱抱
"""
            await message.channel.send(info)
        elif message.content == "冷丸":
            await message.channel.send(f"{self.get_author_name(message)}")
        elif all([w in [":people_hugging:", "抱", " "] for w in message.content[2:]]):
            await message.channel.send(f"{message.author.mention} :people_hugging:")
        elif "機率" in message.content:
            if random.randint(0, 3) == 0:
                await message.channel.send(f"{random.randint(0, 100)}%")
            else:
                choice = [
                    "可能", "不可能", "大概", "有機會", "非常有機會", "不知道", "0.0001%", "比 papa 抽到藍色蠑螈機率還低",
                    "別做夢了", "醒"
                ]
                await message.channel.send(random.choice(choice))
        elif "籤" in message.content:
            choice = [
                "吉", "大吉", "給你一個超級大吉", "吉吉吉吉吉吉", "這是 5 個裡面唯一的兇"
            ]
            await message.channel.send(random.choice(choice))
        elif message.content[2:] in self.learned_talk_queue:
            ans = self.learned_talk[message.content[2:]]
            if isinstance(ans, str):
                await message.channel.send(ans)
            else:
                await message.channel.send(random.choice(ans))
        elif "天真" in message.content or "3D" in message.content:
            await message.channel.send("天真好棒！")
        elif "月嵐" in message.content:
            await message.channel.send("月嵐 3150")
        elif "可愛" in message.content:
            if "比" in message.content:
                await message.channel.send("冷丸最可愛！")
            else:
                await message.channel.send(f"比{random.choice(['咖咩醬', '虛無雀', '天真'])}更可愛！")
        elif "娶" in message.content:
            await message.channel.send("不要！")
        elif "椰香" in message.content or "椰子" in message.content or "綠色乖乖" in message.content:
            await message.channel.send("冷丸最乖了！")
        elif "乖乖" in message.content:
            await message.channel.send("乖乖好吃")
        elif "上班" in message.content:
            await message.channel.send("下次放假是什麼時候")
        elif "回來了" in message.content:
            await message.channel.send("我回來了")
        elif "回來" in message.content:
            await message.channel.send("我比較想放假")
        elif "去哪" in message.content:
            await message.channel.send("放假找天真去了")
        elif "冷丸好" == message.content:
            await message.channel.send(f"{author_name}好")
        elif "年終" in message.content and "沒" in message.content:
            await message.channel.send(f"{author_name} 是慣老闆")
        elif "喵" in message.content:
            await message.channel.send("汪")
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
            await message.channel.send(random.choice(code))
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
            await message.channel.send(":two: :regional_indicator_b: :regional_indicator_g:")
        elif "外掛" in message.content:
            await message.channel.send("!?")
        elif "本物" in message.content:
            await message.channel.send("Yesss")
        elif "吃雞" in message.content or "champion" in message.content or "冠軍" in message.content:
            await message.channel.send("蝦?????")
        elif "apex" in message.content:
            await message.channel.send("apex 31500000")
        elif "nice" in message.content:
            await message.channel.send("niceeeee")
        elif "性別" in message.content:
            await message.channel.send("女生")
        elif "睡" in message.content:
            await message.channel.send("z" * random.randint(3, 20))
        elif "圓周率" in message.content:
            await message.channel.send("3.141592653589793238462643383279502884197169399375105820974944592307816406286208998")
        elif "對不起" in message.content:
            await message.channel.send(":pleading_face:")
        elif "不乖" in message.content or"叛逆" in message.content:
            if await is_mod_or_superior(self.bot, message.author) and message.channel.id != 889525732122968074:
                await message.channel.send("<@405327571903971333>")
            else:
                await message.channel.send(":pleading_face:")
        elif "定理" in message.content or"定律" in message.content or "數學" in message.content or "物理" in message.content or "化學" in message.content or "生物" in message.content or "公式" in message.content or "喜歡誰" in message.content or "比" in message.content or "社會" in message.content or "歷史" in message.content:
            await message.channel.send("去問咖咩啦")
        elif "乖" in message.content:
            await message.channel.send("咖咩學學我啊")
        elif "幫" in message.content:
            await message.channel.send("油加你幫！")
        elif "a-z" in message.content:
            await message.channel.send("kMGTPEZY")
        elif "嗎" not in message.content and ("摸" in message.content or "喜歡" in message.content or "fire" in message.content or "water" in message.content):
            await message.channel.send("Fire" + "e" * random.randint(0, 10))
        elif "早" in message.content or "午" in message.content or "晚" in message.content:
            await message.channel.send(f"{random.choice(['早', '午', '晚'])}安")
        elif "主人" in message.content:
            await message.channel.send("天真天才")
        elif "抱" in message.content or ":people_hugging:" in message.content:
            await message.channel.send(f":people_hugging:")
        elif "bonk" in message.content:
            await message.channel.send("冷丸最乖了，咖咩才不乖")
        elif "我是誰" in message.content:
            await message.channel.send(f"聽說是 {message.author.name}")
        elif "咖咩" in message.content and ("翹班" in message.content or "不在" in message.content):
            await message.channel.send("@月嵐")
        elif ("會" in message.content and "嗎" in message.content) or "會不會" in message.content:
            await message.channel.send(random.choice(["會", "不會", "不知道"]))
        elif ("要" in message.content and "嗎" in message.content) or "要不要" in message.content:
            await message.channel.send(random.choice(["要", "不要", "不知道"]))
        elif ("有" in message.content and "嗎" in message.content) or "有沒有" in message.content:
            await message.channel.send(random.choice(["有", "沒有", "不知道"]))
        elif ("是" in message.content and "嗎" in message.content) or "是不是" in message.content:
            await message.channel.send(random.choice(["是", "不是", "不知道"]))
        elif ("在" in message.content and "嗎" in message.content) or "在不在" in message.content:
            await message.channel.send(random.choice(["在", "不在", "不在", "不在", "不在"]))
        elif ("好" in message.content and "嗎" in message.content) or "好不好" in message.content:
            await message.channel.send(random.choice(["好", "不好", "不知道"]))
        elif ("行" in message.content and "嗎" in message.content) or "行不行" in message.content:
            await message.channel.send(random.choice(["行", "不行", "不知道"]))
        elif ("買" in message.content and "嗎" in message.content) or "買不買" in message.content:
            await message.channel.send(random.choice(["買", "不買", "不知道"]))
        elif ("想" in message.content and "嗎" in message.content) or "想不想" in message.content:
            await message.channel.send(random.choice(["想", "不想", "不知道"]))
        elif ("愛" in message.content and "嗎" in message.content) or "愛不愛" in message.content:
            await message.channel.send(random.choice(["愛", "不愛", "不知道"]))
        elif ("吃" in message.content and "嗎" in message.content) or "吃不吃" in message.content:
            await message.channel.send(random.choice(["吃", "不吃", "不知道"]))
        elif ("該" in message.content and "嗎" in message.content) or "該不該" in message.content:
            await message.channel.send(random.choice(["該", "不該", "不知道"]))
        elif ("可" in message.content and "嗎" in message.content) or "可不可" in message.content:
            await message.channel.send(random.choice(["可以", "不可以", "不知道"]))
        elif "有幾個" in message.content:
            await message.channel.send(random.randint(-100, 200))
        elif "黑" in message.content and "嗎" in message.content:
            await message.channel.send(random.choice(["黑的", "白的"]))
        elif "哪" in message.content:
            await message.channel.send("地球的某一個角落")
        elif "嗎" in message.content or "嘛" in message.content or "?" in message.content or "？" in message.content:
            await message.channel.send(random.choice(["不知道", "你猜", "問咖咩", "問月嵐"]))
        elif "(" in message.content:
            await message.channel.send("(天才")
        elif "（" in message.content:
            await message.channel.send("（天才")
        else:
            await message.channel.send(random.choice(["chi~", "chi chi~", "chi chi chi~"]))
    
    async def get_message(self, channel, message_id):
        try:
            message = await channel.fetch_message(message_id)
        except:
            return False
        else:
            return message
    
    def get_author_name(self, message):
        if message.author.nick:
            return message.author.nick
        return message.author.name

