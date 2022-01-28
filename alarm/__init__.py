from .alarm import Alarm

def setup(bot):
    bot.add_cog(Alarm(bot))
