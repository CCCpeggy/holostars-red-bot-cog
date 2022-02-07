from .membership_role import MembershipRoleManger

def setup(bot):
    bot.add_cog(MembershipRoleManger(bot))
