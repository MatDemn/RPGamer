import discord
from discord.ext import commands
from discord.utils import get
import asyncio
import datetime
import os
import re
import youtube_dl
from sqlalchemy import func, select

from variables import Variables
import BotExceptions
import DBManager
from Models.QueueModel import QueueModel
from mutagen.mp3 import MP3

youtube_dl.utils.bug_reports_message = lambda: ""


class MusicSource(discord.FFmpegPCMAudio):
    """
    Class used to encapsulate music source. Along with basic source fields,
    it has some information about music.
    Music player can easily fetch title and other stuff from it.
    """
    def __init__(self, source, data,  **before_options):
        """
        Contructor that initiates all fields for object.
        Used by music player.
        :param source: Source to fetch music bytes from.
        :param data: Music information.
        :param before_options: FFMPEG additional options. Reconnecting with server etc.
        """
        super().__init__(source, before_options=before_options)

        self.title = data.get('title')
        self.duration = data.get('duration')
        self.id = data.get('id')
        self.lastTimestamp = 0
        self.lastTimeStopped = datetime.datetime.now()


class Soundboard(commands.Cog):
    """
    Module representing music player and its methods.
    Users can play and search youtube videos as well as play local files.
    Functions very similar to many famous bots among discord users.
    """
    def __init__(self, client):
        """
        Instantiates bot object in class field. Called automatically.
        :param client: Filled automatically by setup function outside of class.
        Bot instance.
        """
        self.client = client

        # field may be used in future build or deleted, not sure yet
        self.timeoutDisconnect = {}

    @commands.command()
    @commands.has_any_role(f"{Variables.djRole}")
    async def join(self, ctx: commands.context):
        """
        Command used to connect bot to the voice channel that you are on.
        :param ctx: Filled automatically during command invoke. Context of the command.
        """
        if ctx.voice_client and ctx.voice_client.is_connected():
            await ctx.voice_client.move_to(ctx.message.author.voice.channel)
        else:
            try:
                await ctx.message.author.voice.channel.connect()
            except AttributeError:
                raise BotExceptions.NoVoiceChannel

    @commands.command()
    @commands.has_any_role(f"{Variables.djRole}")
    async def leave(self, ctx: commands.context):
        """
        Command used to kick the bot out of the voice channel.
        :param ctx: Filled automatically during command invoke. Context of the command.
        """
        await ctx.voice_client.disconnect()

    def correctTime(self, source: MusicSource):
        """
        This method corrects timestamp of music source
        and last time it was stopped. Used when player is paused or resumed.
        :param source: Source of sounds that the bot plays.
        """
        nowTime = datetime.datetime.now()
        source.lastTimestamp = (source.lastTimestamp + (nowTime - source.lastTimeStopped).seconds)
        source.lastTimeStopped = nowTime

    def correctStopped(self, source: MusicSource):
        """
        This method corrects only last time the player was stopped.
        Without correcting timestamp like in correctTime method.
        :param source: Source of sounds that the bot plays.
        """
        nowTime = datetime.datetime.now()
        source.lastTimeStopped = nowTime

    @commands.command()
    @commands.has_any_role(f"{Variables.djRole}")
    async def pause(self, ctx: commands.context):
        """
        Pauses the player. That's it.
        :param ctx: Filled automatically during command invoke. Context of the command.
        """
        await self.join(ctx)
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            self.correctTime(ctx.voice_client.source)
            await ctx.send("Player paused...")
        else:
            await ctx.send("Not playing anything...")

    @commands.command()
    @commands.has_any_role(f"{Variables.djRole}")
    async def resume(self, ctx: commands.context):
        """
        Resumes the paused player.
        :param ctx: Filled automatically during command invoke. Context of the command.
        """
        await self.join(ctx)
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            self.correctStopped(ctx.voice_client.source)
            await ctx.send("Player resumed...")
        elif ctx.voice_client.is_playing():
            await ctx.send("Already resumed...")
        else:
            with DBManager.dbmanager.Session.begin() as session:
                result = session.query(QueueModel.Entry) \
                    .filter(QueueModel.ID_Server == ctx.message.guild.id).first()
                # if it exists, play it along :)
                if result:
                    await self.silentplay(ctx, result[0])
                else:
                    await ctx.send("No music on pause...")

    @commands.command(aliases=["sb"])
    @commands.has_any_role(f"{Variables.djRole}")
    async def soundboard(self, ctx, *, name):
        """
        Plays short sounds from local files.
        Interrupts music player when music is played
        and resumes it when soundboard finish its job.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param name: Name of the file to play.
        """
        await self.join(ctx)
        filepath = f"Sounds/{name}.mp3"

        if not os.path.exists(filepath):
            await ctx.send(f"No sound with name '{name}', sorry...")
            return
        audio = MP3(filepath)
        audiolen = int(audio.info.length)
        srcInfo = {'title': f"{name}", 'id': "localFile", 'duration': audiolen}
        if ctx.voice_client and (ctx.voice_client.is_paused() or ctx.voice_client.is_playing()):
            vsource = ctx.voice_client.source
            ctx.voice_client.source = MusicSource(filepath, srcInfo, **Variables.FFMPEG_OPTIONS)
            await asyncio.sleep(audiolen)
            ctx.voice_client.source = vsource
        else:
            srcInfo = {'title': f"{name}", 'id': "localFile", 'duration': audiolen}
            ctx.voice_client.play(MusicSource(f"Sounds/{name}.mp3", srcInfo, **Variables.FFMPEG_OPTIONS), after=lambda e: self.check_queue(ctx))

    @commands.command(name="queue")
    @commands.has_any_role(f"{Variables.djRole}")
    async def queue(self, ctx):
        """
        Prints current music queue for server. Only 10 top records.
        :param ctx: Filled automatically during command invoke. Context of the command.
        """
        with DBManager.dbmanager.Session.begin() as session:
            result = session.query(QueueModel.FullName)\
                .filter(QueueModel.ID_Server == ctx.guild.id)\
                .limit(10).all()

        index = 1
        if not result:
            await ctx.send("Queue is empty...")
            return
        msgSend = "**Playing queue:**\n"
        for elem in result:
            msgSend += f"**{index}.**{elem[0]}\n"
            index += 1
        await ctx.send(msgSend)

    @commands.command(name="search")
    @commands.has_any_role(f"{Variables.djRole}")
    async def search(self, ctx: commands.context, *, url):
        """
        Command used to search music on YouTube directly using discord chat.
        Bot shows choices for user if there are more results.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param url: Url or name of video to search.
        """
        ytdl_opts = dict(
            Variables.YTDL_OPTS,
            **{'default_search': 'ytsearch5',
               'extract_flat': 'in_playlist'})

        async with ctx.typing():
            ytdl = youtube_dl.YoutubeDL(ytdl_opts)
            result = await self.client.loop.run_in_executor(None, lambda: ytdl.extract_info(url))
            if 'entries' in result:
                sendmess = "**Choose which one:**\n"
                choices = []
                index = 1
                for elem in result['entries']:
                    try:
                        timearr = datetime.timedelta(seconds=elem['duration'])
                    except TypeError:
                        timearr = 'LIVE'
                    sendmess += f"**{index}.**{elem['title']} ({timearr})\n"
                    choices.append(elem['id'])
                    index += 1
                await ctx.send(sendmess)
                try:
                    response = await self.client.wait_for('message', timeout=60.0, check=lambda m: ctx.message.author == m.author)
                except asyncio.exceptions.TimeoutError:
                    await ctx.send("No response provided...")
                else:
                    if response.content == 'cancel':
                        await ctx.send("Canceled...")
                        return
                    parsedInpt = int(response.content)
                    if 0 < parsedInpt <= len(choices):
                        await self.play(ctx, url=choices[parsedInpt-1])
                    else:
                        raise BotExceptions.WrongArgument
            else:
                await self.play(ctx, url=url)

    async def disconnectIfPresent(self, ctx: commands.context):
        """
        This method is not used currently.
        IT was made for disconnecting bot from channel
        if bot is idle for too long.
        :param ctx: Filled automatically during command invoke. Context of the command.
        """
        if ctx.voice_client and not ctx.voice_client.is_playing():
            await asyncio.sleep(15)
            await ctx.voice_client.disconnect()
            self.timeoutDisconnect.pop(ctx.guild.id)

    def check_queue(self, ctx):
        """
        This method checks music queue and fetches next song to play.
        May be changed in future (there is no need to have currently played music in queue,
        the music source has it anyway).
        :param ctx: Filled automatically during command invoke. Context of the command.
        """
        with DBManager.dbmanager.Session.begin() as session:
            # delete current playing song
            toDel = session.query(QueueModel)\
                .filter(QueueModel.ID_Server == ctx.guild.id).first()
            if toDel:
                session.delete(toDel)

            # fetch next song
            result = session.query(QueueModel.Entry)\
                .filter(QueueModel.ID_Server == ctx.message.guild.id).first()

        # if it exists, play it along :)
        if result:
            self.client.loop.create_task(self.silentplay(ctx, result[0]))

    async def silentplay(self, ctx: commands.context, url: str):
        """
        This method plays song without announcement on the text channel.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param url: Url for song to play.
        """
        voice = get(self.client.voice_clients, guild=ctx.guild)

        ytdl_opts = dict(
            Variables.YTDL_OPTS,
            **{'extract_flat': True})

        with youtube_dl.YoutubeDL(ytdl_opts) as ytdl:
            result = ytdl.extract_info(url)

        voice.play(MusicSource(result['formats'][0]['url'], result,
                                          **Variables.FFMPEG_OPTIONS),
                   after=lambda e: self.check_queue(ctx))

    @commands.command()
    @commands.has_any_role(f"{Variables.djRole}")
    async def play(self, ctx: commands.context, *, url):
        """
        Main command to play music. It does not search for music,
        just plays the url.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param url: Url for song to play.
        """
        await self.join(ctx)
        with DBManager.dbmanager.Session.begin() as session:
            # check if limit is not reached
            countQueue = session.query(func.count(QueueModel.ID_Server)) \
                .filter(QueueModel.ID_Server == ctx.guild.id).first()

            if countQueue[0] >= Variables.queueLimit:
                raise BotExceptions.QueueFull

            ytdl_opts = dict(
                Variables.YTDL_OPTS,
                **{'extract_flat': 'in_playlist',
                   'playlistend': Variables.queueLimit - countQueue[0]
                   })

            # add to queue:
            ytdl = youtube_dl.YoutubeDL(ytdl_opts)
            result = await self.client.loop.run_in_executor(None, lambda: ytdl.extract_info(url))

            # case of a playlist
            if 'entries' in result:
                objs = []
                for elem in result['entries']:
                    if elem['duration'] > 10800:
                        continue
                    objs.append(QueueModel(ctx.guild.id, elem['id'], elem['title'][:30]))
                session.bulk_save_objects(objs)

                await ctx.send(f"Entries added to queue...")

                # if it's not occupied, play along :)
                if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                    ctx.voice_client.play(MusicSource(objs[0].Entry, result['entries'][0],
                                                      **Variables.FFMPEG_OPTIONS),
                               after=lambda e: self.check_queue(ctx))

            else:
                if result['duration'] > 10800:
                    await ctx.send("Can't play video longer than 3 hours...")
                    return
                qm = QueueModel(ctx.guild.id, result['id'], result['title'][:50])
                session.add(qm)

                await ctx.send(f"{result['title'][:50]} added to queue...")
                # if it's not occupied, play along :)
                print("xoxo")
                print(f"{re.sub('https:\/\/(.*)\.googlevideo.com\/', 'https://redirector.googlevideo.com/', result['formats'][0]['url'], 1)}")
                ctx.voice_client.play(MusicSource(re.sub('https:\/\/(.*)\.googlevideo.com\/', 'https://redirector.googlevideo.com/', result['formats'][0]['url'], 1), result,**Variables.FFMPEG_OPTIONS))
                if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                    ctx.voice_client.play(MusicSource(re.sub('https:\/\/(.*)\.googlevideo.com\/', 'https://redirector.googlevideo.com/', result['formats'][0]['url'], 1), result,**Variables.FFMPEG_OPTIONS),
                               after=lambda e: self.check_queue(ctx))

    @commands.command()
    @commands.has_any_role(f"{Variables.djRole}")
    async def skip(self, ctx: commands.context, amount: int = 1):
        """
        Used to skip some entries in the queue.
        :param ctx: Filled automatically during command invoke. Context of the command.
        :param amount: Amount of entries to skip (by default it skips only current song).
        """
        with DBManager.dbmanager.Session.begin() as session:
            if amount < 1 or amount > 10:
                raise BotExceptions.WrongArgument

            if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
                # because .stop generated .check_queue and it deletes one record
                amount = amount - 1

            stmnt = select(QueueModel.ID_Queue) \
                .where(QueueModel.ID_Server == ctx.guild.id) \
                .limit(amount)

            delete_q = QueueModel.__table__.delete() \
                .where(QueueModel.ID_Server == ctx.guild.id,
                       QueueModel.ID_Queue.in_(stmnt))
            session.execute(delete_q)

            if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
                ctx.voice_client.stop()

    @commands.command(aliases=["np"])
    @commands.has_any_role(f"{Variables.djRole}")
    async def nowplaying(self, ctx: commands.context):
        """
        Shows currently played song and information about it.
        :param ctx: Filled automatically during command invoke. Context of the command.
        """
        if ctx.voice_client and ctx.voice_client.source:
            # calculate time of this sound
            # if it's playing
            music = ctx.voice_client.source
            if ctx.voice_client.is_playing():
                timepassed = music.lastTimestamp + (datetime.datetime.now() - music.lastTimeStopped).seconds
            else:
                timepassed = music.lastTimestamp
            await ctx.send(f"Now playing: \n"
                           f"**{ctx.voice_client.source.title}**\n"
                           f"{ f'https://youtu.be/{ctx.voice_client.source.id}' if ctx.voice_client.source.id != 'localFile' else ctx.voice_client.source.id}\n"
                           f"{datetime.timedelta(seconds=timepassed)}/{datetime.timedelta(seconds=ctx.voice_client.source.duration)}")
        else:
            await ctx.send("Not playing anything currently...")

    
def setup(client):
    client.add_cog(Soundboard(client))
