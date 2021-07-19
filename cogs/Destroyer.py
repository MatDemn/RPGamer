import discord
from discord.ext import commands
import discord.utils
import datetime
from variables import Variables


class Destroyer(commands.Cog):
    """
    Module represents functions that marks and kicks inactive users.
    Not crucial for session management, but helps sometimes.
    May be separated from this application in future because of the impact on performance.

    Here I reference to 2 specific roles:
    1. Bot's special role (bot uses it to mark people that are inactive for some time after joining the server,
        didn't verified their profile) [BSR].
    2. Server's special role (server uses this role to mark people that are not verified
        since they joined the server) [SSR].

    Preferable use of this module is:
    1. Mark inactive users with BSR (command `markInactive).
    2. Wait for some time (e.g. 7 days), send people message somehow that they going to be kicked
        if they will not verify their profiles within this time.
    3. Kick inactive users.
    """
    def __init__(self, client: commands.Bot):
        """
        Instantiates bot object in class field. Called automatically.
        :param client: Filled automatically by setup function outside of class. Bot instance.
        """
        self.client = client

    #@cog_ext.cog_slash(name="markInactive", guild_ids=[759383031332339734])
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def markInactive(self, ctx: SlashContext, freshmanrole: discord.Role, howmuchdays : int = 7):
        """
        Marks inactive users.
        If user joined <howMuchDays> ago and still has <freshmanrole> (SSR),
        then we consider this user inactive (because no verification was done to clear this role).
        Bot assigns BSR to mark that this user is going to be kicked.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param freshmanrole: Role to check for (SSR).
        :param howmuchdays: How much days of protection is tolerated before marking inactive.
        """
        toAddRole = discord.utils.get(ctx.guild.roles, name=Variables.inactiveRole)
        if not toAddRole:
            await ctx.send(f"You have to make a role'{Variables.inactiveRole}' for command to work.")
            return

        markState = None
        iter = 1
        timeNow = datetime.datetime.now()

        await ctx.send("Starting marking users...")

        async for mem in ctx.guild.fetch_members():
            if (discord.utils.get(mem.roles, name=freshmanrole) is not None) and ((timeNow - mem.joined_at).days > howmuchdays):
                await mem.add_roles(toAddRole)
            if iter%50 == 0:
                if markState:
                    await markState.delete()
                markState = await ctx.send(f"{iter}/{ctx.guild.member_count}")
            iter += 1

        if markState:
            await markState.delete()
        await ctx.send("Finished marking")

    #@cog_ext.cog_slash(name="unmarkInactive", guild_ids=[759383031332339734])
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unmarkInactive(self, ctx: SlashContext):
        """
        Unmarks inactive users. Opposite of markInactive command. If user has BSR,
        then this command clears it. Mainly used to rollback role assignment.
        :param ctx: Filled automatically during command invoke. Context of the command.
        """
        toAddRole = discord.utils.get(ctx.guild.roles, name=Variables.inactiveRole)

        if not toAddRole:
            await ctx.send(f"There is no '{Variables.inactiveRole}' role.")
            return

        await ctx.send("Starting unmarking users...")

        markState = None
        iter = 1
        async for mem in ctx.guild.fetch_members():
            await mem.remove_roles(toAddRole)
            if iter%50 == 0:
                if markState:
                    await markState.delete()
                markState = await ctx.send(f"{iter}/{ctx.guild.member_count}")
            iter += 1

        if markState:
            await markState.delete()
        await ctx.send("Finished unmarking")

    #@cog_ext.cog_slash(name="kickInactive", description="blabla", options=)
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def kickInactive(self, ctx: SlashContext, freshManRole: discord.Role, msg: str = "Your time for verification has expired. :("):
        """
        Command that kicks users with BSR if they have SSR.
        If user has BSR, but doesn't have SSR (verified after BSR assignment),
        bot just clears BSR and leave user without any other action taken.

        BE CAREFUL WITH THIS COMMAND. IF NOT USED CAREFULLY,
        MAY KICK SOMEONE YOU DON'T WANT TO KICK BY MISTAKE!

        :param ctx: Filled automatically during command invoke. Context of the command.
        :param freshManRole: Role to check for (SSR).
        :param msg: Message that you want to send to people when they are kicked.
        """
        deletedmem = 0
        weryfiedmem = 0

        memberListLen = ctx.guild.member_count

        await ctx.send(f"Starting user exterminating...")

        iter = 1

        async for mem in ctx.guild.fetch_members():
            if discord.utils.get(mem.roles, name=f"{Variables.inactiveRole}") is not None:
                if discord.utils.get(mem.roles, name=freshManRole) is not None:
                    deletedmem += 1
                    dm = await mem.create_dm()
                    await dm.send(content=msg)
                    await ctx.guild.kick(mem, reason="Time for verification has expired.")
                else:
                    weryfiedmem += 1
            if iter % 2 == 0:
                await ctx.send(f"{str(iter)} \ {memberListLen}")
        await ctx.send(f"I deleted **{deletedmem}** unverified users. We forced to verify **{weryfiedmem}** users.\n \
This is {(weryfiedmem/(weryfiedmem+deletedmem))*100 if weryfiedmem+deletedmem != 0 else 0}% of previous inactive users.")


def setup(client):
    """
    Sets up whole module.
    :param client: Filled automatically. Instance of a bot.
    """
    client.add_cog(Destroyer(client))