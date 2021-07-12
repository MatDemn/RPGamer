import discord
from discord.ext import commands
from random import randint
import datetime
import json
import os
import BotExceptions

from Models.DiceResultModel import DiceResultModel
from variables import Variables
from additional import dumplog
import re
import DBManager
from sqlalchemy import func, select

from Models.ServerSessionModel import ServerSessionModel
from Models.UserNameModel import UserNameModel
from Models.UserNameBackupModel import UserNameBackupModel
from Models.LanguageEnum import LanguageEnum


class Session(commands.Cog):
    """
    Module that provides functions for session management.
    You can make sessions, delete them and basically do everything
    what you want with them. Useful for nick changing (one player may
    have different names, depend on the session), mute players and move them
    between channels. This is a fundamental structure for other modules to work.

    I refer to the session name and backup name here. Let's explain it with an
    example. We have a session 'Waterfall' which has players John (Murdock the Dwarf)
    and Jane (Harper the Rogue). Their backup names are John and Jane and session
    names are 'Murdock the Dwarf' and 'Harper the Rogue'.

    Regular workflow for this module:
    1. Every player that should be in a session should change his/hers/its
    server nick to corresponding session name.
    2. Invoke command makesession to create session with this players.
    3. Every player should now change his/hers/its server nick to regular
    nickname that should be a backup nick.
    4. Invoke command updatenicksbackups to finish configuring session structure.
    """
    def __init__(self, client):
        """
        Instantiates bot object in class field. Called automatically.
        :param client: Filled automatically by setup function outside of class.
        Bot instance.
        """
        self.client = client

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sessionuphero(self, ctx: commands.context, sessionShort: str):
        """
        This command is used to update hero names for particular session.
        All players for this session must have their respective names (session names)
        and then you can run this command.
        It reads current nicknames and changes them in a database.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param sessionShort: Name for session. Short is more practical if you ask me.
        """
        with DBManager.dbmanager.Session.begin() as session:
            # check if session exists
            results = session.query(UserNameModel.ID_UserName, UserNameModel.ID_User) \
                .join(ServerSessionModel) \
                .filter(ServerSessionModel.ID_Server == ctx.guild.id,
                        ServerSessionModel.SessionShort == sessionShort) \
                .all()
            if not results:
                raise BotExceptions.WrongArgument
            members = []
            for (ID_UserName, IDUser,) in results:
                members.append(
                    {'ID_UserName': ID_UserName, 'HeroName': (await ctx.guild.fetch_member(IDUser)).display_name})
            session.bulk_update_mappings(UserNameModel, members)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sessionupbackup(self, ctx: commands.context, sessionShort : str):
        """
        This command is used to update players backup names for particular session.
        All players for this session must have their respective names (backup names)
        and then you can run this command.
        It reads current nicknames and changes them in a database.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param sessionShort: Name for session. Short is more practical if you ask me.
        """
        with DBManager.dbmanager.Session.begin() as session:
            # check if session exists
            results = session.query(UserNameBackupModel.ID_User) \
                .join(UserNameModel).join(ServerSessionModel) \
                .filter(ServerSessionModel.ID_Server == ctx.guild.id,
                        ServerSessionModel.SessionShort == sessionShort) \
                .all()
            if not results:
                raise BotExceptions.WrongArgument
            members = []
            for (IDUser,) in results:
                members.append({'ID_User': IDUser, 'NickBackup': (await ctx.guild.fetch_member(IDUser)).display_name})
            session.bulk_update_mappings(UserNameBackupModel, members)

    @commands.command(name="sessionnicks",
                      desc="",
                      brief="Changes nicks of particular users for their respective names in particular session")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sessionnicks(self, ctx: commands.context, sessionShort: str, clear: bool = 0):
        """
        This command changes nicks of all players in session.
        If clear is True, then it changes nicks to backup nicks.
        Otherwise, changes nicks to session nicks.
        Besides, when nicks are cleared, dice rolls are also cleared.
        Every single session is 'fresh' in rolls at the start because of that.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param sessionShort: Name of the session to fetch players from.
        :param clear: Nicks should be cleared or changed to session names?
        :return:
        """
        with DBManager.dbmanager.Session.begin() as session:
            results = session.query(UserNameModel.ID_User, UserNameModel.HeroName,
                                    UserNameBackupModel.NickBackup,
                                    ServerSessionModel.SoundBoardSwitch) \
                .join(ServerSessionModel).join(UserNameBackupModel)\
                .filter(ServerSessionModel.ID_Server == ctx.guild.id,
                        ServerSessionModel.SessionShort == sessionShort)\
                .all()

            if not results:
                raise Exception("No session with this name")

            if clear is True:
                for (IDUser, HeroName, NickBack, SoundBoard) in results:
                    await (await ctx.guild.fetch_member(int(IDUser))).edit(nick=NickBack)
                    session.query(UserNameBackupModel)\
                        .filter(UserNameBackupModel.ID_User == IDUser)\
                        .update({UserNameBackupModel.SoundBoardSwitch: False})

                subq = session.query(UserNameModel.ID_User)\
                    .join(ServerSessionModel)\
                    .filter(ServerSessionModel.SessionShort == sessionShort,
                            ServerSessionModel.ID_Server == ctx.guild.id).subquery()
                toDel = session.query(DiceResultModel).filter(DiceResultModel.ID_User == subq.c.ID_User).all()
                for elem in toDel:
                    session.delete(elem)
                await ctx.send("I cleared nicks...")
            else:
                for (IDUser, HeroName, NickBack, SoundBoard) in results:
                    await (await ctx.guild.fetch_member(int(IDUser))).edit(nick=HeroName)
                    session.query(UserNameBackupModel) \
                        .filter(UserNameBackupModel.ID_User == IDUser) \
                        .update({UserNameBackupModel.SoundBoardSwitch: SoundBoard})
                await ctx.send(f"I changed nicks to {sessionShort}")


    async def sessionmakesilent(self, ctx: commands.context, sessionShort: str, soundBoard: bool,
                                *sessionMembers: discord.Member):
        """
        This is a helper method for makesession command.
        In case makesession couldn't do the job by itself,
        it calls this method to finish the job.
        It's just another makesession call, but without too many print messages.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param sessionShort: Name of the new session to create.
        :param soundBoard: Should the bot react to very good and very bad rolls?
        When the roll is 1-5 then roll is very good, roll 96-100 is very bad.
        Bot plays appropriate sound then (laughs at you or praise you).
        This functionality is implemented only on d100.
        Some sessions may want to turn it off to not ruin the atmosphere.
        :param sessionMembers: List of players that should be included in this session.
        """
        finalString = f"I created a new session **{sessionShort}**:\n"
        membersAdded = []

        with DBManager.dbmanager.Session.begin() as session:
            ssm = ServerSessionModel(ctx.guild.id, sessionShort,
                                     ctx.message.author.id, soundBoard)
            session.add(ssm)
            for mem in sessionMembers:
                # user exists in the database
                unm = UserNameModel(mem.display_name)
                session.add(unm)
                ssm.UsersNames.append(unm)
                unbm = session.query(UserNameBackupModel) \
                    .filter(UserNameBackupModel.ID_User == mem.id) \
                    .first()
                if unbm is None:
                    if mem is not None:
                        newMember = UserNameBackupModel(mem.id, mem.name, False)
                        session.add(newMember)
                        newMember.UsersNames.append(unm)
                else:
                    unbm.UsersNames.append(unm)
                membersAdded.append(mem.display_name)
            # sort people for adding
            membersAdded.sort()
            for elem in membersAdded:
                finalString += f"\t-{elem}\n"
            await ctx.send(finalString)

    async def sessiondelsilent(self, ctx: commands.context, sessionShort: str):
        """
        This command deletes certain session structure. Silent version,
        invoked only by makesession when it can't finish it's job.
        Without too many unnecessary messages and checking permissions.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param sessionShort: Name of the session to delete.
        """
        # check if session exists and user can delete this session (is admin or gm)
        with DBManager.dbmanager.Session.begin() as session:
            delRes = session.query(ServerSessionModel)\
                .filter(ServerSessionModel.ID_Server == ctx.guild.id,
                        ServerSessionModel.SessionShort == sessionShort).first()
            session.delete(delRes)
            usersDel = session.query(UserNameBackupModel).join(UserNameModel, isouter=True) \
                .filter(UserNameModel.ID_User == None).all()
            for user in usersDel:
                session.delete(user)

    @commands.command()
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sessionmake(self, ctx: commands.context, sessionShort : str, soundBoard : bool, *sessionMembers: discord.Member):
        """
        Main command to make session with.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param sessionShort: Name of the new session to create.
        :param soundBoard: Should the bot react to very good and very bad rolls?
        When the roll is 1-5 then roll is very good, roll 96-100 is very bad.
        Bot plays appropriate sound then (laughs at you or praise you).
        This functionality is implemented only on d100.
        Some sessions may want to turn it off to not ruin the atmosphere.
        :param sessionMembers: List of players that should be included in this session.
        """
        finalString = f"I created a new session **{sessionShort}**:\n"
        membersAdded = []
        if len(sessionMembers) > Variables.sessionMembers or len(sessionMembers) < 1:
            raise BotExceptions.WrongArgument
        await ctx.send("Making session...", delete_after=5.0)

        with DBManager.dbmanager.Session.begin() as session:

            # number of sessions on the server
            numberOfSessions = session.query(func.count(ServerSessionModel.SessionShort))\
                .filter(ServerSessionModel.ID_Server == ctx.guild.id).first()

            if numberOfSessions[0] > Variables.sessionLimit:
                raise BotExceptions.WrongArgument(f"Too many sessions defined on the server. "
                                                  f"Limit of {Variables.sessionLimit} reached already...")

            # if session exists, return ID_GM
            ssm = session.query(ServerSessionModel.ID_GM)\
                .filter(ServerSessionModel.ID_Server == ctx.guild.id,
                        ServerSessionModel.SessionShort == sessionShort).first()

            # if the record of that session already exists
            if ssm:
                try:
                    # if I found gm of this session
                    gm_ref = await ctx.guild.fetch_member(ssm[0])
                    raise BotExceptions.WrongArgument(f"Session with name **{sessionShort}** already exists. "
                                                      f"Ask GM:**{gm_ref.display_name}**")
                except Exception:
                    # if not, then I should delete this session (GM doesn't exists)
                    await self.sessiondelsilent(ctx, sessionShort)
                    self.client.loop.create_task(self.sessionmakesilent(ctx, sessionShort, soundBoard, *sessionMembers))

            # if not exists, I can make one
            else:
                ssm = ServerSessionModel(ctx.guild.id, sessionShort,
                                         ctx.message.author.id, soundBoard)
                session.add(ssm)
                for mem in sessionMembers:
                    # user exists in the database
                    unm = UserNameModel(mem.display_name)
                    session.add(unm)
                    ssm.UsersNames.append(unm)
                    unbm = session.query(UserNameBackupModel) \
                                  .filter(UserNameBackupModel.ID_User == mem.id) \
                                  .first()
                    if unbm is None:
                        if mem is not None:
                            newMember = UserNameBackupModel(mem.id, mem.name, False)
                            session.add(newMember)
                            newMember.UsersNames.append(unm)
                    else:
                        unbm.UsersNames.append(unm)
                    membersAdded.append(mem.display_name)
                # sort people for adding
                membersAdded.sort()
                for elem in membersAdded:
                    finalString += f"\t-{elem}\n"
                await ctx.send(finalString)

    @commands.command()
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sessiondel(self, ctx: commands.context, sessionShort: str):
        """
        This command deletes certain session structure. You have to be session GM
        or administrator to do this.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param sessionShort: Name of the session to delete.
        """
        # check if session exists and user can delete this session (is admin or gm)
        with DBManager.dbmanager.Session.begin() as session:
            res = session.query(ServerSessionModel.ID_GM) \
                         .filter(ServerSessionModel.ID_Server == ctx.guild.id,
                                 ServerSessionModel.SessionShort == sessionShort).first()

            # unpacking results or exit if no results
            if res:
                (res,) = res
            else:
                await ctx.send("No session with this name...")
                return

            # if author is admin or gm of the session, session might be deleted
            if(res == ctx.message.author.id or
                    ctx.message.author.guild_permissions.administrator):
                delRes = session.query(ServerSessionModel)\
                    .filter(ServerSessionModel.ID_Server == ctx.guild.id,
                            ServerSessionModel.SessionShort == sessionShort).first()
                session.delete(delRes)

                await ctx.send(f"I deleted session **{sessionShort}**")
            else:
                raise BotExceptions.GMOrAdmin

    @commands.command()
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sessionlist(self, ctx: commands.context):
        """
        Shows names of sessions that the player invoking command plays.
        Just a simple list, nothing else.
        :param ctx: Filled automatically during command invoke. Context of the command.
        """
        with DBManager.dbmanager.Session.begin() as session:
            results = session.query(ServerSessionModel.SessionShort)\
                    .join(UserNameModel)\
                    .filter(UserNameModel.ID_User == ctx.message.author.id)\
                    .order_by(ServerSessionModel.SessionShort)\
                    .all()

        sendMess = "There are your sessions, sire...\n"
        if not results:
            sendMess = "No sessions found... \n"
            await ctx.send(sendMess)
        else:
            for (sessionShort,) in results:
                    sendMess += f"{sessionShort}, "
            await ctx.send(sendMess[:-2])

    @commands.command()
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sessionlistgm(self, ctx: commands.context):
        """
        Shows names of sessions that the player invoking command plays as GM.
        Just a simple list, nothing else.
        :param ctx: Filled automatically during command invoke. Context of the command.
        """
        with DBManager.dbmanager.Session.begin() as session:
            results = session.query(ServerSessionModel.SessionShort) \
                .filter(ServerSessionModel.ID_GM == ctx.message.author.id) \
                .order_by(ServerSessionModel.SessionShort) \
                .all()

        sendMess = "There are your GM sessions, sire...\n"
        if not results:
            sendMess = "No sessions found... \n"
            await ctx.send(sendMess)
        else:
            for (sessionShort,) in results:
                sendMess += f"{sessionShort}, "
            await ctx.send(sendMess[:-2])

    @commands.command(aliases=['sessiondetails'])
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sessiondetail(self, ctx: commands.context, sessionShort: str):
        """
        More detailed information about particular session.
        Shows players and their session names.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param sessionShort: Name of the session that you want to fetch information from.
        """
        with DBManager.dbmanager.Session.begin() as session:
            result = session.query(UserNameModel.HeroName,
                                   UserNameBackupModel.NickBackup)\
                            .join(ServerSessionModel)\
                            .join(UserNameBackupModel)\
                            .filter(ServerSessionModel.SessionShort == sessionShort)\
                            .all()
        if not result:
            await ctx.send("No session with this name...")
            return
        sendMess = f"Session **{sessionShort}** has those players:\n"
        for (heroName, nickBack) in result:
            sendMess += f"\t{heroName} ({nickBack})\n"
        await ctx.send(sendMess)

    @commands.command()
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sessionaddmem(self, ctx: commands.context, sessionShort: str, *members: discord.Member):
        """
        Command that is used to add players to existing session.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param sessionShort: Name of the session to fetch information from.
        :param members: List of players to add to the session.
        """
        with DBManager.dbmanager.Session.begin() as session:
            if len(members) > Variables.sessionMembers or len(members) < 1:
                raise BotExceptions.WrongArgument

            result = session.query(ServerSessionModel.ID_ServerSession, ServerSessionModel.ID_GM, UserNameModel.ID_User)\
                .join(UserNameModel)\
                .filter(ServerSessionModel.ID_Server == ctx.guild.id,
                        ServerSessionModel.SessionShort == sessionShort).all()
            if not result:
                raise BotExceptions.WrongArgument(f"There is no session with name {sessionShort}")

            result = [result[0][0], result[0][1], set([a[2] for a in result])]

            if (result[2] != ctx.message.author.id and
                    not ctx.message.author.guild_permissions.administrator):
                raise BotExceptions.GMOrAdmin

            if len(result[2]) + len(members) > Variables.sessionMembers:
                raise BotExceptions.WrongArgument(f"Too much people in session")
            for mem in members:
                # check if this user is in this session
                # if yes, omit this user
                if mem.id in result[2]:
                    continue
                # if no, add to database
                # make object and merge it with session (if exists, update
                # otherwise: insert)
                unbm = UserNameBackupModel(mem.id, mem.name, False)
                unm = UserNameModel(mem.display_name)
                unm.ID_ServerSession = result[0]
                unm.ID_User = mem.id
                session.merge(unbm)
                session.add(unm)
        await ctx.send(f"I added those users to session {sessionShort}")

    @commands.command()
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sessiondelmem(self, ctx: commands.context, sessionShort: str, *members: discord.Member):
        """
        Command to delete people from certain session.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param sessionShort: Name of the session to focus on.
        :param members: List of players to delete from session.
        """
        with DBManager.dbmanager.Session.begin() as session:
            if len(members) > Variables.sessionMembers or len(members) < 1:
                raise BotExceptions.WrongArgument

            result = session.query(ServerSessionModel.ID_ServerSession, ServerSessionModel.ID_GM, UserNameModel.ID_User) \
                .join(UserNameModel) \
                .filter(ServerSessionModel.ID_Server == ctx.guild.id,
                        ServerSessionModel.SessionShort == sessionShort).all()
            if not result:
                raise BotExceptions.WrongArgument(f"There is no session with name {sessionShort}")

            result = [result[0][0], result[0][1], set([a[2] for a in result])]

            if (result[1] != ctx.message.author.id and
                    not ctx.message.author.guild_permissions.administrator):
                raise BotExceptions.GMOrAdmin

            stmnt = select(UserNameModel.ID_UserName).join(ServerSessionModel)\
                .where(ServerSessionModel.SessionShort == sessionShort,
                       ServerSessionModel.ID_Server == ctx.guild.id,
                       UserNameModel.ID_User.in_(result[2]))

            delete_q = UserNameModel.__table__.delete() \
                .where(UserNameModel.ID_UserName.in_(stmnt))
            if session.execute(delete_q).rowcount == len(result[2]):
                # then delete session as well
                delete_q = ServerSessionModel.__table__.delete() \
                    .where(ServerSessionModel.ID_ServerSession == result[0])
                session.execute(delete_q)
        await ctx.send(f"I removed those users from session {sessionShort}")

    @commands.command()
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sessionmute(self, ctx: commands.context, sessionshort: str):
        """
        Mutes/unmutes all players from particular session
        (if not muted - mute, if muted - unmute).
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param sessionshort: Name of the session to fetch players from.
        """
        with DBManager.dbmanager.Session.begin() as session:
            result = session.query(UserNameModel.ID_User, ServerSessionModel.ID_GM)\
                .join(ServerSessionModel) \
                .filter(ServerSessionModel.ID_Server == ctx.guild.id,
                        ServerSessionModel.SessionShort == sessionshort).all()
        if not result:
            await ctx.send("There is no such session, sorry.")
            return

        result = [result[0][1], [a[0] for a in result]]

        if (result[0] != ctx.message.author.id and
                not ctx.message.author.guild_permissions.administrator):
            raise BotExceptions.GMOrAdmin

        for mem in result[1]:
            try:
                mem = await ctx.guild.fetch_member(mem)
            except Exception:
                continue
            if mem.voice is not None:
                state = not bool(mem.voice.deaf)
                await mem.edit(deafen=state, mute=state)
        await ctx.send("Mics and headphones switched to opposite.")

    @commands.command()
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sessionmove(self, ctx: commands.context, sessionshort: str, channel: discord.VoiceChannel):
        """
        Moves all session players from current channel to another.
        May not be very useful if session has only a few players.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param sessionshort: Name of the session to fetch players from.
        :param channel: Channel ID (or anything else that
        can be converted to channel) to move players to.
        """
        with DBManager.dbmanager.Session.begin() as session:
            result = session.query(UserNameModel.ID_User, ServerSessionModel.ID_GM) \
                .join(ServerSessionModel) \
                .filter(ServerSessionModel.ID_Server == ctx.guild.id,
                        ServerSessionModel.SessionShort == sessionshort).all()
        if not result:
            await ctx.send("There is no such session, sorry.")
            return

        result = [result[0][1], [a[0] for a in result]]

        if (result[0] != ctx.message.author.id and
                not ctx.message.author.guild_permissions.administrator):
            raise BotExceptions.GMOrAdmin

        for mem in result[1]:
            try:
                mem = await ctx.guild.fetch_member(mem)
            except Exception:
                continue
            if mem.voice is not None:
                await mem.move_to(channel)
        await ctx.send(f"Session moved to channel **{channel.name}**.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sessionSplit(self, context, sessionNr, nameOfSession):
        """
        This command is used to send separator between sessions.
        Rolls and messages from previous session can be separated from new session.
        :param context: Filled automatically during command invoke. Context of the command.
        :param sessionNr: Number of session. Is it first, third of maybe fifteenth session?
        :param nameOfSession: Title of the session/scenario.
        """
        sendstring = f"**{20 * '-'}SESSION {sessionNr}: {nameOfSession}{20 * '-'}**"
        await context.send(sendstring)


def setup(client):
    """
    Sets up whole module.
    :param client: Filled automatically. Instance of a bot.
    """
    client.add_cog(Session(client))
