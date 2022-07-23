# redbot
import os
import logging
import subprocess
from redbot.core.i18n import Translator
from redbot.core import checks, commands, Config
from redbot.core.bot import Red

_ = Translator("StarStreams", __file__)
log = logging.getLogger("red.core.cogs.Update")

class Update(commands.Cog):
    def __init__(self, bot: Red, **kwargs):
        super().__init__()
        self.bot = bot
    
    @commands.command(name="update")
    @checks.is_owner()
    async def _stars_update(self, ctx: commands.Context, command_type: str="bash"):
        """ 將程式碼更新
        需求：電腦需要安裝 git bash，且這個 cog 是 git 的資料夾
        更新完畢後，需要重新 reload 這個 cog
        """
        file_path = os.path.dirname(os.path.abspath(__file__))
        if command_type == "bash":
            cmd = f"cd {file_path} ; git pull origin master"
        elif command_type == "cmd":
            cmd = f"{file_path[0]}: & cd {file_path} & git pull origin dev_star_version_2"
        else:
            await ctx.send(f"未知的 shell")
        # f = os.popen(cmd, "r")
        # message = f.read()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        log.info(f"run: {cmd}")
        output = output.decode("utf-8") 
        error = error.decode("utf-8") 
        log.info(f"{output}{error}")
        await ctx.send(f"{output}{error}")
        try:
            if "Aborting" in error:
                raise Exception
            elif "fatal" in error:
                raise Exception
            elif "changed" in output:
                await ctx.send(f"更新到 origin master 的最新版本，請使用 reload 重新載入程式。")
            elif "Already up to date" in output:
                await ctx.send(f"你就已經最新了，不用更新好嗎？(月嵐 ver.)")
            else:
                raise Exception
        except:
            await ctx.send(f"沒有更新成功，可能 `git` 設定錯誤或其他原因，詳情請確認 log 的錯誤訊息。")
        # f.close()