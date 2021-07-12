import asyncio

import discord
from discord.ext import commands
import sys
import datetime
import os
import variables as _v
import random
#from .. import additional.cprint as cprint

class Utilities(commands.Cog):
    """
    Module that represents other functions, not connected to sessions.
    """
    def __init__(self, client: commands.Bot):
        """
        Instantiates bot object in class field. Called automatically.
        :param client: Filled automatically by setup function outside of class.
        Bot instance.
        """
        self.client = client

    @commands.command(aliases=["hoia"])
    async def howoldiam(self, ctx, usr: discord.Member = None):
        """
        Commands that shows how long particular player is on this server.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param usr: User to show information about. If None, then message author is passed.
        """
        if not usr:
            await ctx.send(f"You joined: {str(ctx.message.author.joined_at)[:10]} {ctx.message.author.mention} you're here  {(datetime.datetime.now() - ctx.message.author.joined_at).days} days already!")
        else:
            await ctx.send(f"***{usr.display_name}*** joined **{str(usr.joined_at)[:10]}** and is here **{(datetime.datetime.now() - usr.joined_at).days} days** already!")

    @commands.command()
    async def shuff(self, context: commands.context, *options: str):
        """
        Shuffles provided options and prints then on the chat.
        :param context: Filled automatically during command invoke. Context of the command.
        :param options: Options to shuffle
        """
        lis = list(options)
        random.shuffle(lis)

        msg = "["
        for i in lis:
            msg += i + ", "
        await context.send(msg[:-2]+"]")
        
    @commands.command()
    @commands.is_owner()
    async def logoutme(self, context: commands.context):
        """
        Logs out entire bot.
        :param context: Filled automatically during command invoke. Context of the command.
        """
        await context.send("**I'm going to sleep, fellaz. Goodbye and see you next time! :)**")
        await self.client.close()

def setup(client):
    """
    Sets up whole module.
    :param client: Filled automatically. Instance of a bot.
    """
    client.add_cog(Utilities(client))