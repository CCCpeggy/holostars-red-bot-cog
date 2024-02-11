from .main import MembershipRoleManger
from redbot.core.bot import Red

async def setup(bot: Red) -> None:
    await bot.add_cog(MembershipRoleManger(bot))
