import discord
from discord.ext import commands
from variables import Variables
from additional import dumplog
import DBManager

class Misc(commands.Cog):
    """
    Module that provides miscellaneous functions
    that are not connected to anything in particular.
    Just some useful stuff.
    """
    def __init__(self, client: commands.Bot):
        """
        Instantiates bot object in class field. Called automatically.
        :param client: Filled automatically by setup function outside of class.
        Bot instance.
        """
        self.client = client

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def makePoll(self, ctx: commands.context, *args: str):
        """
        Makes simple poll. That's it. Similar to session poll, but without
        session functions. Just for choosing the best options.
        Reactions under message tells you what choice others chose.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param args: Options for your poll. You can make 7-elements poll at max.
        """
        sendString = "**Here's your poll, sire...**\n";
        loopLimit = 0;
        if(len(Variables.emojiarray)-1 < len(args)):
            await ctx.send("There is only **7** choices at max in poll...")
            loopLimit = len(Variables.emojiarray)-1
        else:
            loopLimit = len(args)
            
        for i in range(loopLimit):
            sendString += Variables.emojiarray[i] + " " + args[i] + "\n"
         
        msg = await ctx.send(sendString)
        
        for i in range(loopLimit):
            await msg.add_reaction(Variables.emojiarray[i%7])

    #async def automaticSessionPoolCheckAndSend(self, ctx: commands.context):
    #    with DBManager.dbmanager.Session.begin() as session:
    #        result = session.query()


def setup(client):
    """
    Sets up whole module.
    :param client: Filled automatically. Instance of a bot.
    """
    client.add_cog(Misc(client))


