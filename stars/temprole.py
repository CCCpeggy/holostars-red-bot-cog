"""
MIT License

Copyright (c) 2021 Obi-Wan3

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from time import sleep
import typing
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse as parse_time
from membership_role.errors import *

import discord
from redbot.core import checks, commands, Config
from redbot.core.utils.chat_formatting import humanize_list
from redbot.core.i18n import cog_i18n, Translator

_ = Translator("StarsStreams", __file__)
log = logging.getLogger("red.core.cogs.TempRole")

if typing.TYPE_CHECKING:
    TimeConverter = timedelta
else:
    TimeConverter = commands.converter.TimedeltaConverter(
        minimum=timedelta(seconds=1),
        allowed_units=["seconds", "minutes", "weeks", "days", "hours"],
        default_unit="days"
    )

OVERFLOW_ERROR = "The time set is way too high, consider setting something reasonable."


class TempRole(commands.Cog):
    """
    Assign Temporary Roles

    Give temporary roles to users, expiring after a set time.
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=14000605, force_registration=True)
        default_guild = {
            "log": None,
            "allowed": []
        }
        default_member = {
            "temp_roles": {}
        }
        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)
        
        from membership_role.membership_role import MembershipRoleManger
        self.membership_role: MembershipRoleManger = MembershipRoleManger(self.bot)

        self.tr_handler_task = self.bot.loop.create_task(self._tr_handler())

    def cog_unload(self):
        self.membership_role.cog_unload()
        self.tr_handler_task.cancel()

    @commands.guild_only()
    @commands.group(name="temprole")
    async def _temp_role(self, ctx: commands.Context):
        """TempRole Commands"""

    async def add(self, ctx: commands.Context, mod: discord.Member, cmd_channel: discord.TextChannel, user: discord.Member, role: discord.Role, time: TimeConverter):
        """
        Assign a temporary role to expire after a time.

        For the time, enter in terms of weeks (w), days (d), and/or hours (h).
        """
        # if role in user.roles:
        #     return await cmd_channel.send(f"That user already has {role.mention}!")

        if role >= ctx.guild.me.top_role or (role >= mod.top_role and ctx.author != ctx.guild.owner):
            return await cmd_channel.send("That role cannot be assigned due to the Discord role hierarchy!")

        async with self.config.member(user).temp_roles() as user_tr:
            # if user_tr.get(str(role.id)):
            #     return await cmd_channel.send(
            #         f"That is already an active TempRole for {user.mention}!",
            #         allowed_mentions=discord.AllowedMentions.none()
            #     )
            try:
                end_time = datetime.now() + time
            except OverflowError:
                return await cmd_channel.send(OVERFLOW_ERROR)
            user_tr[str(role.id)] = end_time.timestamp()

        if role < ctx.guild.me.top_role:
            if role not in user.roles:
                await user.add_roles(
                    role,
                    reason=f"TempRole: added by {ctx.author}, expires in {time.days}d {time.seconds//3600}h"
                )
        else:
            return await cmd_channel.send("I cannot assign this role!")

        message = f"TempRole {role.mention} for {user.mention} has been added. Expires in {time.days} days {time.seconds//3600} hours."
        await cmd_channel.send(
            message,
            allowed_mentions=discord.AllowedMentions.none()
        )

        await self._maybe_send_log(ctx.guild, message)
        await self._tr_timer(user, role, end_time.timestamp())


    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    @checks.mod_or_permissions(manage_channels=True)
    @_temp_role.command(name="add")
    async def _add(self, ctx: commands.Context, user: discord.Member, role: discord.Role, *, iso_time: str):
        """
        Assign a temporary role to expire after a time.

        For the time, time nees iso format
        """
        # if role in user.roles:
        #     return await ctx.send(f"That user already has {role.mention}!")
        iso_time = parse_time(iso_time).replace(tzinfo=timezone.utc)
        time = iso_time - datetime.now(timezone.utc)

        if time.total_seconds() <= 0:
            return await ctx.send("過去時間")

        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            if role >= ctx.author.top_role:
                log.info(2)
            if ctx.author != ctx.guild.owner:
                log.info(3)
            return await ctx.send("That role cannot be assigned due to the Discord role hierarchy!")

        async with self.config.member(user).temp_roles() as user_tr:
            try:
                end_time = datetime.now(timezone.utc) + time
            except OverflowError:
                return await ctx.send(OVERFLOW_ERROR)
            user_tr[str(role.id)] = end_time.timestamp()

        if role not in user.roles:
            await user.add_roles(
                role,
                reason=f"TempRole: added by {ctx.author}, expires in {time.days}d {time.seconds//3600}h"
            )

        message = f"TempRole {role.mention} for {user.mention} has been added. Expires in {time.days} days {time.seconds//3600} hours."
        await ctx.send(
            message,
            allowed_mentions=discord.AllowedMentions.none()
        )

        await self._maybe_send_log(ctx.guild, message)
        await self._tr_timer(user, role, end_time.timestamp())

    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    @checks.mod_or_permissions(manage_channels=True)
    @_temp_role.command(name="check")
    async def _check(self, ctx: commands.Context, role: discord.Role):
        """列出指令身分組但沒有暫時身分限制的名單."""
        non_temp_list = []
        for member in role.members:
            user_tr = await self.config.member(member).temp_roles()
            if str(role.id) not in user_tr or datetime.now(timezone.utc).timestamp() > user_tr[str(role.id)]:
                if len(non_temp_list) >= 50:
                    await ctx.send(f"名單：{', '.join(non_temp_list)}",
                    allowed_mentions=discord.AllowedMentions.none())
                    non_temp_list = []
                non_temp_list.append(member.mention)

        if len(non_temp_list) > 0:
            await ctx.send(f"名單：{', '.join(non_temp_list)}",
            allowed_mentions=discord.AllowedMentions.none())
        else:
            await ctx.send("所有人都有 temprole")

        

    @commands.bot_has_permissions(manage_roles=True)
    @commands.admin_or_permissions(manage_roles=True)
    @_temp_role.command(name="remove")
    async def _remove(self, ctx: commands.Context, user: discord.Member, role: discord.Role):
        """Cancel the timer & remove a TempRole from a user."""
        async with self.config.member(user).temp_roles() as user_tr:
            if not (user_tr.get(str(role.id))):
                return await ctx.send(
                    f"That is not an active TempRole for {user.mention}.",
                    allowed_mentions=discord.AllowedMentions.none()
                )
            del user_tr[str(role.id)]
        message = f"TempRole {role.mention} for {user.mention} has been removed."
        await ctx.send(
            message,
            allowed_mentions=discord.AllowedMentions.none()
        )
        await self._maybe_send_log(ctx.guild, message)
        await self._tr_end(user, role, admin=ctx.author)

    @commands.bot_has_permissions(manage_roles=True)
    @_temp_role.group(name="self")
    async def _self_role(self, ctx: commands.Context):
        """Self-TempRoles"""

    @commands.admin_or_permissions(manage_roles=True)
    @_self_role.command(name="allow")
    async def _allow(self, ctx: commands.Context, *roles: discord.Role):
        """Set the TempRoles all users are allowed to add to themselves (leave blank to remove)."""
        for role in roles:
            if role >= ctx.guild.me.top_role or (role >= ctx.author.top_role and ctx.author != ctx.guild.owner):
                return await ctx.send(f"{role.name} cannot be assigned due to the Discord role hierarchy!")
        await self.config.guild(ctx.guild).allowed.set([r.id for r in roles])
        return await ctx.tick()

    @_self_role.command(name="add")
    async def _self_add(self, ctx: commands.Context, role: discord.Role, *, time: TimeConverter):
        """Add a TempRole to yourself."""
        if role.id not in await self.config.guild(ctx.guild).allowed():
            return await ctx.send("That is not a valid self-TempRole!")

        async with self.config.member(ctx.author).temp_roles() as user_tr:
            if user_tr.get(str(role.id)):
                return await ctx.send(
                    f"That is already an active self-TempRole!",
                    allowed_mentions=discord.AllowedMentions.none()
                )
            try:
                end_time = datetime.now() + time
            except OverflowError:
                return await ctx.send(OVERFLOW_ERROR)
            user_tr[str(role.id)] = end_time.timestamp()

        if role < ctx.guild.me.top_role:
            if role not in ctx.author.roles:
                await ctx.author.add_roles(
                    role,
                    reason=f"TempRole: added by {ctx.author}, expires in {time.days}d {time.seconds//3600}h"
                )
            else:
                return await ctx.send("You already have this role!")
        else:
            return await ctx.send("I cannot assign this role!")

        message = f"Self-TempRole {role.mention} has been added. Expires in {time.days} days {time.seconds//3600} hours."
        await ctx.send(
            message,
            allowed_mentions=discord.AllowedMentions.none()
        )

        await self._maybe_send_log(ctx.guild, message)
        await self._tr_timer(ctx.author, role, end_time.timestamp())

    @_self_role.command(name="remove")
    async def _self_remove(self, ctx: commands.Context, role: discord.Role):
        """Cancel the timer & remove a self-TempRole."""
        async with self.config.member(ctx.author).temp_roles() as user_tr:
            if not (user_tr.get(str(role.id))):
                return await ctx.send(
                    f"That is not an active self-TempRole.",
                    allowed_mentions=discord.AllowedMentions.none()
                )
            del user_tr[str(role.id)]
        message = f"Self-TempRole {role.mention} has been removed."
        await ctx.send(
            message,
            allowed_mentions=discord.AllowedMentions.none()
        )
        await self._maybe_send_log(ctx.guild, message)
        await self._tr_end(ctx.author, role, admin=ctx.author)

    @_self_role.command(name="list")
    async def _self_list(self, ctx: commands.Context):
        """List the available TempRoles you can assign to yourself."""
        allowed = await self.config.guild(ctx.guild).allowed()
        roles = []
        for r in allowed:
            if role := ctx.guild.get_role(r):
                roles.append(role.name)
        if roles:
            return await ctx.send(f"Self-TempRoles for this server: {humanize_list(roles)}.")
        else:
            return await ctx.send("No self-TempRoles have been set up in this server yet.")

    @_temp_role.command(name="remaining")
    async def _remaining(self, ctx: commands.Context, role: discord.Role):
        """See the time remaining for your TempRole."""
        user = ctx.author
        async with self.config.member(user).temp_roles() as user_tr:
            if not (cur_tr := user_tr.get(str(role.id))):
                return await ctx.send(
                    f"That is not an active TempRole for {user.mention}.",
                    allowed_mentions=discord.AllowedMentions.none()
                )
            r_time = datetime.fromtimestamp(cur_tr) - datetime.now()
            return await ctx.maybe_send_embed(f"**Time remaining:** {r_time.days} days {round(r_time.seconds/3600, 1)} hours")

    @commands.bot_has_permissions(embed_links=True)
    @commands.admin_or_permissions(manage_roles=True)
    @_temp_role.command(name="list")
    async def _list(self, ctx: commands.Context, user: discord.Member = None):
        """List the active TempRoles for each user (or users with TempRoles in the server if user param is empty)."""
        desc = ""
        color = await ctx.embed_color()
        async def send(title, desc, color):
            return await ctx.send(embed=discord.Embed(
                title=title,
                description=desc,
                color=await ctx.embed_color()
            ))

        if not user:
            title = f"{ctx.guild.name} TempRoles"
            for member_id, temp_roles in (await self.config.all_members(ctx.guild)).items():
                member: discord.Member = ctx.guild.get_member(int(member_id))
                if member:
                    if roles := [ctx.guild.get_role(int(r)) for r in temp_roles["temp_roles"].keys()]:
                        desc += f"{member.mention}: {humanize_list([r.mention for r in roles])}\n"
                    else:
                        await self.config.member(member).clear()
                if len(desc) > 3900:
                    await send(title, desc, color)
                    desc = ""
        else:
            title = f"{user.display_name} TempRoles"
            async with self.config.member(user).temp_roles() as member_temp_roles:
                for temp_role, end_ts in member_temp_roles.items():
                    role: discord.Role = ctx.guild.get_role(int(temp_role))
                    if role:
                        r_time = datetime.fromtimestamp(end_ts) - datetime.now()
                        desc += f"{role.mention}: ends in {r_time.days}d {round(r_time.seconds/3600, 1)}h\n"
                    else:
                        del member_temp_roles[temp_role]
                    if len(desc) > 3900:
                        await send(title, desc, color)
                        desc = ""
        return await send(title, desc, color)

    @commands.admin_or_permissions(manage_roles=True)
    @_temp_role.command(name="logchannel")
    async def _log_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set the TempRole log channel for the server (leave blank to remove)."""
        if channel and not channel.permissions_for(ctx.guild.me).send_messages:
            return await ctx.send(f"I cannot send messages to {channel.mention}!")
        await self.config.guild(ctx.guild).log.set(channel.id if channel else None)
        return await ctx.tick()

    async def _maybe_send_log(self, guild: discord.Guild, message: str):
        log_channel = await self.config.guild(guild).log()
        if log_channel and (log_channel := guild.get_channel(log_channel)) and log_channel.permissions_for(guild.me).send_messages:
            await log_channel.send(
                message,
                allowed_mentions=discord.AllowedMentions.none()
            )

    async def _tr_handler(self):
        await self.bot.wait_until_red_ready()
        # try:
        #     tr_coros = []
        #     for guild_id, members in (await self.config.all_members()).items():
        #         guild: discord.Guild = self.bot.get_guild(int(guild_id))
        #         for member_id, temp_roles in members.items():
        #             member: discord.Member = guild.get_member(int(member_id))
        #             for tr, ts in temp_roles["temp_roles"].items():
        #                 role: discord.Role = guild.get_role(int(tr))
        #                 tr_coros.append(self._tr_timer(member, role, ts))
        #     await asyncio.gather(*tr_coros)
        # except Exception:
        #     pass

    async def _tr_timer(self, member: discord.Member, role: discord.Role, end_timestamp: float):
        seconds_left = (datetime.fromtimestamp(end_timestamp) - datetime.now()).total_seconds()
        if seconds_left > 0:
            await asyncio.sleep(seconds_left)
        user_tr = await self.config.member(member).temp_roles()
        # 更新會員資料
        member = self.bot.get_guild(member.guild.id).get_member(member.id)
        if member and role in member.roles and str(role.id) in user_tr:
            if (datetime.fromtimestamp(user_tr[str(role.id)]) - datetime.now()).total_seconds() <= 0:
                await self._tr_end(member, role)

    async def _tr_end(self, member: discord.Member, role: discord.Role, admin=None):
        async with self.config.member(member).temp_roles() as tr_entries:
            if tr_entries.get(str(role.id)):
                del tr_entries[str(role.id)]
                reason = "TempRole: timer ended" if not admin else f"TempRole: timer ended early by {admin}"
                if member.guild.me.guild_permissions.manage_roles and role < member.guild.me.top_role:
                    if role in member.roles:
                        await member.remove_roles(role, reason=reason)
                        await self._maybe_send_log(
                            member.guild,
                            f"TempRole {role.mention} for {member.mention} has been removed."
                        )
                    else:
                        await self._maybe_send_log(
                            member.guild,
                            f"TempRole {role.mention} for {member.mention} ended, but the role had already been removed."
                        )
                else:
                    await self._maybe_send_log(
                        member.guild,
                        f"TempRole {role.mention} for {member.mention} was unable to be removed due to a lack of permissions."
                    )
    
    @commands.admin_or_permissions(manage_roles=True)
    @_temp_role.command(name='convert')
    async def _convert_data(self, ctx: commands.GuildContext):
        """將目前會員資料轉存去新的 cog"""
        def to_datetime(time: str) -> datetime:
            from dateutil.parser import parse as parse_time
            try:
                time = parse_time(time)
                import pytz
                if time.tzinfo == None:
                    time = pytz.utc.localize(time)
                return time
            except:
                pass
        if self.membership_role == None:
            await ctx.send(f"未啟用 membership_role")
            return
        allowed = await self.config.guild(ctx.guild).allowed()
        role_to_member = {}
        role_to_type_name = {}
        for member_name, member in self.membership_role.members.items():
            for type_name, role_id in member.membership_type.items():
                role_to_member[role_id] = member
                role_to_type_name[role_id] = type_name
                
        count = 0
        for r in allowed:
            if role := ctx.guild.get_role(r):
                for member in role.members:
                    user_tr = await self.config.member(member).temp_roles()
                    try:
                        self.membership_role.add_user(member.id)
                    except AlreadyExists:
                        pass
                    except Exception as e:
                        log.error(e)
                        continue
                    if str(role.id) in user_tr or datetime.now(timezone.utc).timestamp() <= user_tr[str(role.id)]:
                        member_name = role_to_member[role.id]
                        type_name = role_to_type_name[role.id]
                        d = datetime.fromtimestamp(user_tr[str(role.id)])
                        d = to_datetime(f"{d.year}/{d.month}/{d.day}")
                        try:
                            user_role = self.membership_role.add_user_role(role.id, member_name, d, type_name)
                            user_role.valid()
                        except AlreadyExists:
                            pass
                        except Exception as e:
                            log.error(e)
                if count > 50:
                    count = 0
                    await self.membership_role.save_users()
        await self.membership_role.save_users()
        await ctx.send(f"結束")