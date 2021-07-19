"""
Main file, launching the whole application.
"""

import json
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import os
import sys
from sqlalchemy import select
import DBManager
from Models.ServerSessionModel import ServerSessionModel
from Models.LanguageEnum import LanguageEnum
from Models.UserNameModel import UserNameModel
from Models.UserNameBackupModel import UserNameBackupModel
from Models.QueueModel import QueueModel

#from discord_slash import SlashCommand, SlashContext

# in case it is a local copy
if os.path.exists("config.cfg"):
    with open("config.cfg", "r") as cfgfile:
        botCfg = json.load(cfgfile)
# in case it is web copy
else:
    # we try to make config dict, but if it fails, then config is missing
    try:
        botCfg = {'botPrefix' : os.environ["botPrefix"], 'ownerId' : os.environ["ownerId"], 'botToken' : os.environ["botToken"]}
    except Exception as e:
        raise Exception("Config not found")

client = Bot(command_prefix=botCfg["botPrefix"], owner_id=botCfg["ownerId"], case_insensitive=True,
             intents=discord.Intents.default())
#slash = SlashCommand(client, sync_commands=True)

# build all models in database
DBManager.dbmanager.Base.metadata.create_all(bind=DBManager.dbmanager.engine)

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")

'''client.load_extension(f"cogs.BotSetup")
client.load_extension(f"cogs.Session")'''
#client.load_extension(f"cogs.Indev")

guild_ids=[759383031332339734]

#this one works properly
'''
@slash.slash(name="exampleSlash", description="blabla", guild_ids=guild_ids)
async def exampleSlash(ctx):
    await ctx.send("blah!")
'''

client.run(botCfg["botToken"])
