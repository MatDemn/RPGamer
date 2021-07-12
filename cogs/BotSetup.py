import discord
from discord.ext import commands
import datetime
import youtube_dl
import os
import sys
import BotExceptions
import traceback
from additional import dumplog


class BotSetup(commands.Cog):
    """
    Module represents basic bot setup functions.
    """
    def __init__(self, client: commands.Bot):
        """
        Instantiates bot object in class field.
        :param client: Filled automatically by setup function outside of class. Bot instance.
        """
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Function that starts after the bot finished launching. Changes presence on server to "Rolling dices"
        and prints information in terminal. If it's called, then everything runs properly and applications
        is ready to make actions.
        """
        await self.client.change_presence(activity=discord.Game("Rolling dices (1.0.0)"))
        print("Application has started properly.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.context, error: Exception):
        """
        Command that handles exceptions and prints information on the chat.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param error: Exception to handle.
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please pass all the required arguments...")
        if isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.send(f"You are on cooldown, {int(error.retry_after)}seconds left.")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send("I don't know this command, sorry. :(")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You can't do that, pal. Ask for some higher permissions.")
        elif isinstance(error, commands.errors.MemberNotFound):
            await ctx.send(f"One or more users not found on a server...")
        elif isinstance(error, discord.InvalidArgument):
            await ctx.send(f"There is a problem with one or more arguments...")
        elif isinstance(error, commands.errors.CommandInvokeError):
            await ctx.send(error.original)
        elif isinstance(error, discord.ext.commands.errors.MissingAnyRole):
            await ctx.send(f"You don't have required role: {error.missing_roles[0]}")
        elif isinstance(error, youtube_dl.utils.DownloadError):
            await ctx.send(f"Player error. Might be technical problems on the line.")
        elif isinstance(error, commands.errors.NotOwner):
            await ctx.send(f"You are not the owner of me.")
        else:
            print(f"{datetime.datetime.now()} [{type(error)}]: \"{error}\"")
            dumplog(f"{datetime.datetime.now()} [{type(error)}]: \"{error}\"")
            await ctx.send("Unknown error occurred. Contact my maker, please.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx: commands.context, extension: str):
        """
        Command that handles loading module into the bot.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param extension: Name of the module to load.
        """
        try:
            self.client.load_extension(f"cogs.{extension}")
        except Exception as e:
            print(f"Error ocurred: {e}")
            await ctx.send("Error ocurred. Check console log.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx: commands.context, extension: str):
        """
        Command that handles unloading module from the bot.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param extension: Name of the module to unload.
        """
        try:
            self.client.unload_extension(f"cogs.{extension}")
        except:
            e = sys.exc_info()[0]
            print(f"Error ocurred: {e}")
            await ctx.send("Error ocurred. Check console log.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx: commands.context, extension: str):
        """
        Command that handles reloading module in the bot.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param extension: Name of the module to reload.
        """
        try:
            await self.unload(ctx, extension)
        except:
            print("Error_reload1")
        try:
            await self.load(ctx, extension)
        except:
            print("Error_reload2")


def setup(client: commands.Bot):
    """
    Sets up whole module.
    :param client: Filled automatically. Instance of a bot.
    """
    client.add_cog(BotSetup(client))
