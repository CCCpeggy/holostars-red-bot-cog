from .talk import Talk

def setup(bot):
    bot.add_cog(Talk(bot))
