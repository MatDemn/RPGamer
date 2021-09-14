import discord
from discord.ext import commands
from random import randint
import datetime
import json
import os
from variables import Variables
from additional import dumplog
import re
import DBManager
from sqlalchemy.sql import select

from Models.ServerSessionModel import ServerSessionModel
from Models.UserNameModel import UserNameModel
from Models.UserNameBackupModel import UserNameBackupModel
from Models.LanguageEnum import LanguageEnum

class Poll(commands.Cog):
    """
    Module that provides various functions to cope with
    polls. You can make poll, sum it up and mention those
    players that didn't vote. Pretty useful to establish
    proper date for session.

    Typical workflow for this module is:
    1.   Enter command to make session poll.
    2.   Wait for players (they must be players of at least 1 session,
    otherwise the algorithm won't count them) to vote.
    Couple of days should do the job.
    2.5. Enter command to mention lazy players who didn't vote (make them vote or
    exclude them from session poll results).
    3.   Sum up the poll to see which session is playable.

        For future releases:
    This may be a good idea to make some special role for this players
    to mark them for bot. Session polls could ping them if the poll is made
    or if the results come out of it.
    """
    def __init__(self, client: commands.Bot):
        """
        Instantiates bot object in class field. Called automatically.
        :param client: Filled automatically by setup function outside of class.
        Bot instance.
        """
        self.client = client

    @commands.command()
    @commands.has_any_role(Variables.rpgamerRole)
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sessionpoll(self, context: commands.context, startday: str):
        """
        This command makes poll for players to vote.
        They can choose witch date among 7 possible is best
        for them by clicking reactions below message.
        :param startday: Date in format dd.mm.yy. This is a start date
        of the 7 consecutive days to choose from in poll.
        """

        iterate = 7
        sendstring = f"**What time do you want to play session?**\n"

        startday = datetime.datetime.strptime(startday, "%d.%m.%y")

        for i in range(0, iterate):
            tempday = startday + datetime.timedelta(days=i)
            sendstring += Variables.emojiarray[i % 7] + str(" " + tempday.strftime("%A")) + str(
                " (" + tempday.strftime("%d") + "." + tempday.strftime("%m") + ")") + "\n"

        sendstring += Variables.notsureEmoji + str(" Not sure yet") + "\n"
        sendstring += Variables.noneEmoji + str(" None of the above") + "\n"

        msg = await context.send(sendstring)

        for i in range(0, iterate):
            await msg.add_reaction(Variables.emojiarray[i % 7])
        await msg.add_reaction(Variables.notsureEmoji)
        await msg.add_reaction(Variables.noneEmoji)

    @commands.command()
    @commands.has_any_role(Variables.rpgamerRole)
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def sumpoll(self, ctx: commands.context, message: discord.Message, *ignored: discord.Member):
        """
        This command is used to sum up previously
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param message: Message to fetch votes from. E.g. ID of the message.
        :param ignored: You can specify which players should be excluded
        from summing up a poll. This is useful for example to make a simulation
        'What if Luis and Jane could play on Friday night? Can everybody play then?
        Exclude then from summing up and see what happens.'
        """
        # Temporary message for response calculating
        tempMess = await ctx.send("**Calculating...**", delete_after=5.0)

        # extract all poll options into the array from message content
        savedSonda = re.split(r'[\n\r]+', message.content)[1:-2]

        # make ignored set (ignore this people in results)
        ignoredSet = set()
        for a in ignored:
            ignoredSet.add(a.id)

        # extract all players id on current server from database and make it into set
        with DBManager.dbmanager.Session.begin() as session:
            playersList = session.query(UserNameModel.ID_User)\
                                 .join(ServerSessionModel)\
                                 .filter(ServerSessionModel.ID_Server == ctx.guild.id)\
                                 .group_by(UserNameModel.ID_User)\
                                 .all()
        playersList = set([a for (a,) in playersList])

        # result message
        msg = "**Poll results:**"

        # iterate through reactions and calculate them
        # reac - message.reactions[i]
        # reacdata - savedSonda rows (message rows)
        for reac, reacdata in zip(message.reactions, savedSonda):
            # make set of users for particular message
            reacUsers = set([x.id for x in await reac.users().flatten()])\
                        .intersection(playersList)
            goodDate = False
            msg += f"\n**{reacdata}**"

            with DBManager.dbmanager.Session.begin() as session:

                sessionList = session.query(ServerSessionModel.SessionShort)\
                                     .filter(ServerSessionModel.ID_Server == ctx.guild.id).all()

                for (sess,) in sessionList:  # Iterate through sessions on the server

                    memList = set(
                        [a for (a,) in session.query(UserNameModel.ID_User)
                                              .join(ServerSessionModel)
                                              .filter(ServerSessionModel.ID_Server == ctx.guild.id,
                                                      ServerSessionModel.SessionShort == sess)
                                              .all()])

                    if memList.difference(
                            reacUsers.union(ignoredSet)) == set():
                        if goodDate:
                            msg += f", {sess}"
                        else:
                            msg += f"\n\t\t:white_check_mark: {sess}"
                            goodDate = True

                if not goodDate:
                    msg += f"\n\t\t:x: Bad date. Votes: {len(reacUsers)}/{len(playersList)}"
        notSureSet = sorted(set([x.id for x in await message.reactions[-2].users().flatten()]).intersection(playersList))
        msg += f"\n{Variables.notsureEmoji}**Not sure:** "
        for i in notSureSet:
            msg += f"<@!{i}>, "
        if notSureSet:
            await ctx.send(msg[:-2])
            return
        await cts.xend(msg)

    @commands.command()
    @commands.has_any_role(Variables.rpgamerRole)
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def mentionLazies(self, ctx: commands.context, message: discord.Message):
        """
        Not every player will vote straight away. Sometimes you have to remind,
        force, convince them to do this. This command may help you do this.
        Every player that is in at least 1 session and didn't vote will be marked.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param message: Message to fetch result from (poll that have to be used to calculate
        results). Anything that can be converted to message. For example message ID.
        """
        with DBManager.dbmanager.Session.begin() as session:
            # number of players
            playersList = set([ a for (a,) in session.query(UserNameModel.ID_User) \
                .join(ServerSessionModel) \
                .filter(ServerSessionModel.ID_Server == ctx.guild.id) \
                .group_by(UserNameModel.ID_User) \
                .all()])

        ALLMEMLEN = len(playersList)
        msg = ""

        tempMess = await ctx.send("**Obliczam...**")
        for reac in message.reactions:  # Iterate through reactions

            reacUsers = set([x.id for x in await reac.users().flatten()])

            playersList -= reacUsers  # Usuwam ze zbioru tych ludzi, ktorzy dali reakcje (bo zaglosowali)

        if playersList:  # Czyli jeśli istnieje osoba, ktora nie oddala glosu
            msg += f"\n**Users didn't vote: ({len(playersList)}/{ALLMEMLEN}):** \n"
            for i in playersList:
                user = await ctx.guild.fetch_member(i)
                if user:
                    msg += f"{user.mention}, "
            await ctx.send(msg[:-2])
        else:
            await ctx.send("**All people voted.**")
        await tempMess.delete()


def setup(client):
    """
    Sets up whole module.
    :param client: Filled automatically. Instance of a bot.
    """
    client.add_cog(Poll(client))
