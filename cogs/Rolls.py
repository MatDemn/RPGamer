

import discord
from discord.ext import commands
from random import randint
import datetime
import json
import os
from variables import Variables
import additional
import re
import DBManager
from sqlalchemy.sql import select


from Models.ServerSessionModel import ServerSessionModel
from Models.UserNameModel import UserNameModel
from Models.UserNameBackupModel import UserNameBackupModel
from Models.LanguageEnum import LanguageEnum
from Models.LanguageEnum import SoundReactionEnum
from Models.DiceResultModel import DiceResultModel


class Rolls(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="roll",
                      aliases=["r"]
                      )
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def rollthedice(self, ctx: commands.context, rangedice: additional.rollFormat = [1,100], gmMem: discord.Member = None):
        """
        Command used to roll the dice. By default it rolls 1d100.
        If player is in at least 1 session, rolls are saved.
        :param com: Dice format. KdN - K for number of rolls and N for dice sides.
        :param gmMem: If user provided, it sends roll as secret to this player
        instead of sending it to the chat.
        """

        # if there is `r {i} then I roll 1d{i}
        if len(rangedice) == 1:
            rangedice.append(rangedice[0])
            rangedice[0] = 1
        if rangedice[1] == 100:
            lowerbound = 5
            higherbound = 96
        else:
            # if there is a different dice than d100,
            # then I disable sound reaction for roll
            lowerbound = 0
            higherbound = rangedice[1] + 1

        # sum of rolls
        sum = 0
        # message to send
        msg = ""
        # trim number of dice rolls to 10 (may be changed later)
        if rangedice[0] > 10:
            rangedice[0] = 10
            await ctx.send("You can only roll 10 times in a row. I trimmed it, so no worries!")
        if rangedice[1] > 1000:
            rangedice[1] = 1000
            await ctx.send("You can only roll 1000 sided dice. I trimmed it, so no worries!")
        rand = 0
        # simulating dice rolls
        for i in range(rangedice[0]):
            # random number from 1 to argument-defined (both included)
            rand = randint(1, rangedice[1])
            # sum rolls (for further average calculating)
            sum += rand
            # compose message to send at the end
            msg += str(rand) + " "
        # average value for rolls
        average = sum / rangedice[0]

        # variable for sound reaction
        trigger = SoundReactionEnum.none

        # check if user is in the database
        with DBManager.dbmanager.Session() as session:
            result = session.query(UserNameBackupModel.SoundBoardSwitch)\
                .filter(UserNameBackupModel.ID_User == ctx.message.author.id)\
                .first()
            session.commit()
            # if this user is in a session
            if result:
                # if soundboardswitch is ON
                if result[0]:
                    if average <= lowerbound:
                        trigger = SoundReactionEnum.good  # wow
                    if average >= higherbound:
                        trigger = SoundReactionEnum.bad  # laugh

                    SB = self.client.get_cog('Soundboard')
                    if SB is None:
                        raise Exception("Error in Roll.SoundBoard: get_cog")
                    if trigger == SoundReactionEnum.good:
                        await SB.soundboard(ctx, name=Variables.goodSound)
                    elif trigger == SoundReactionEnum.bad:
                        await SB.soundboard(ctx, name=Variables.badSound)

                # look for database entries
                result = session.query(DiceResultModel.ID_DiceResults)\
                    .filter(DiceResultModel.ID_User == ctx.message.author.id,
                            DiceResultModel.DiceLabel == rangedice[1]).first()
                session.commit()
                # if there is and entry, change it
                if result:
                    session.query(DiceResultModel)\
                        .filter(DiceResultModel.ID_DiceResults == result[0])\
                        .update({DiceResultModel.AvgResults:
                                (DiceResultModel.AvgResults *
                                 DiceResultModel.NumberOfResults +
                                 sum)
                                 / (DiceResultModel.NumberOfResults + rangedice[0]),
                                 DiceResultModel.NumberOfResults:
                                 DiceResultModel.NumberOfResults + rangedice[0]})
                    session.commit()
                # otherwise, insert new value
                else:
                    userEntry = session.query(UserNameBackupModel)\
                        .filter(UserNameBackupModel.ID_User == ctx.message.author.id).first()
                    drm = DiceResultModel(rangedice[1], average, rangedice[0])
                    if not userEntry:
                        raise Exception("There is an error in Roll userEntry level...")
                    userEntry.DicesResults.append(drm)
                    session.add(drm)
                    session.commit()
                if gmMem:
                    dm = await gmMem.create_dm()
                    await dm.send(f"{sum} [{msg[0:-1]}] {ctx.message.author.display_name}")
                else:
                    await ctx.send(f"{sum} [{msg[0:-1]}] {ctx.message.author.mention}")
            else:
                await ctx.send(f"{sum} [{msg[0:-1]}] {ctx.message.author.mention}")

    @commands.command(aliases=["sr"])
    @commands.has_permissions(administrator=True)
    async def sumrolls(self, ctx: commands.context, sessionShort: str):
        """
        Sums up rolls for all players in particular session.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param sessionShort: Name of the session to fetch players from.
        """
        with DBManager.dbmanager.Session.begin() as session:
            sub = session.query(UserNameModel.ID_User)\
                .join(ServerSessionModel)\
                .filter(ServerSessionModel.SessionShort == sessionShort,
                        ServerSessionModel.ID_Server == ctx.guild.id).subquery()

            result = session.query(sub.c.ID_User,
                                DiceResultModel.DiceLabel,
                                DiceResultModel.AvgResults,
                                DiceResultModel.NumberOfResults) \
                .join(sub, sub.c.ID_User == DiceResultModel.ID_User).order_by().all()

        msg = ""
        prev_IDUSR = ""
        user_name = ""
        if result:
            msg += f"**Summing up today's session:**\n"
        for (ID_User, DiceLabel, AvgRes, NumberOfRes) in result:
            if prev_IDUSR != ID_User:
                user_name = (await ctx.guild.fetch_member(ID_User)).display_name
                prev_IDUSR = ID_User
                msg += f"{user_name}:\n"
            msg += f"\tD{DiceLabel}: {AvgRes} ({NumberOfRes})\n"
        if msg:
            await ctx.send(msg)
        else:
            await ctx.send("No rolls to sum up :(")

    @commands.command(aliases=["rr"])
    @commands.has_role("Admin")
    async def resetrolls(self, ctx: commands.context, sessionShort: str):
        """
        Reset rolls for all players in particular session.

        :param sessionShort: Name of the session to fetch players from.
        """
        with DBManager.dbmanager.Session.begin() as session:
            (result,) = session.query(ServerSessionModel.ID_GM)\
                .filter(ServerSessionModel.ID_Server == ctx.guild.id,
                        ServerSessionModel.SessionShort == sessionShort).first()
            if (result == ctx.message.author.id or
                    ctx.message.author.guild_permissions.administrator):
                subq = session.query(UserNameModel.ID_User)\
                    .join(ServerSessionModel) \
                    .filter(ServerSessionModel.SessionShort == sessionShort,
                            ServerSessionModel.ID_Server == ctx.guild.id)\
                    .group_by(UserNameModel.ID_User)\
                    .subquery()
                toDel = session.query(DiceResultModel)\
                    .filter(subq.c.ID_User == DiceResultModel.ID_User)\
                    .all()
                for elem in toDel:
                    session.delete(elem)
                await ctx.send(f"I deleted all rolls for session {sessionShort}")
            else:
                raise commands.MissingPermissions(["administrator"])

def setup(client):
    client.add_cog(Rolls(client))