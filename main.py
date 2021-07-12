"""
Main file, launching the whole application.
"""

import json

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

if os.path.exists("config.cfg"):
    #print("Config file not found, exiting...")
    raise Exception("Config file not found")
    
    with open("config.cfg", "r") as cfgfile:
        botCfg = json.load(cfgfile)   
else:
    botCfg = {'botPrefix' : os.environ["botPrefix"], 'owner_id' : os.environ["ownerId"], 'botToken' : os.environ["botToken"]}

client = Bot(command_prefix=botCfg["botPrefix"], owner_id=botCfg["ownerId"], case_insensitive=True)

# build all models in database
DBManager.dbmanager.Base.metadata.create_all(bind=DBManager.dbmanager.engine)

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")

'''client.load_extension(f"cogs.BotSetup")
client.load_extension(f"cogs.Session")'''

client.run(botCfg["botToken"])
