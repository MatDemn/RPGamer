import discord
from discord.ext import commands
import discord.utils
import datetime
from variables import Variables


class Indev(commands.Cog):
    """
    Module that is used to test new functionalities.
    Not crucial for session management, may be deleted without any concern.
    """
    def __init__(self, client: commands.Bot):
        """
        Instantiates bot object in class field. Called automatically.
        :param client: Filled automatically by setup function outside of class. Bot instance.
        """
        self.client = client

    @commands.command()
    async def helloworld(self, ctx: commands.context):
        """
        Prints "Hello, world!" on chat. That's it.
        Nothing more or less, just this.
        :param ctx: Filled automatically during command invoke. Context of the command.
        """
        await ctx.send("Hello, world!")

    @commands.command()
    async def embedprint(self, ctx: commands.context):
        """
        Example of embed sending.
        :param ctx: Filled automatically during command invoke. Context of the command.
        """
        embed = discord.Embed(title="Tytuł wiadomości", url="http://www.example.pl", description="Przykładowy opis",
                              color=0x0212a2)
        embed.set_author(name="Nick autora", url="http://www.linkautora.pl",
                         icon_url="https://cdn3.iconfinder.com/data/icons/logos-and-brands-adobe/512/267_Python-512.png")
        embed.set_thumbnail(url="https://cdn.iconscout.com/icon/free/png-512/discord-3-569463.png")
        embed.add_field(name="Pole 1", value="wartość 1", inline=True)
        embed.add_field(name="Pole 2", value="wartość 2", inline=True)
        embed.set_footer(text="Treść stopki")
        await ctx.send(embed=embed)


def setup(client):
    """
    Sets up whole module.
    :param client: Filled automatically. Instance of a bot.
    """
    client.add_cog(Indev(client))
