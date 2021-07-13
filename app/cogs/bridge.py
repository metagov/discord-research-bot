import discord
from discord.embeds import Embed
from discord.ext import commands
from discord import TextChannel
from discord.ext.commands import Context
import shelve

from discord.message import Message
from discord.user import User

BRIDGES_FN = 'bridges.db'

# Relays messages between channels.
class BridgeCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        print('Loaded Bridge Cog')
        self.bot = bot

    def cog_unload(self):
        print('Unloaded Bridge Cog')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Do not respond to our own messages!
        if message.author == self.bot.user:
            return
        
        # This does not work in DMs!
        if not message.guild:
            return
        
        # Open the persistent dictionary.
        with shelve.open(BRIDGES_FN) as db:
            if str(message.channel.id) in db:
                dest_id = int(db[str(message.channel.id)])
                channel: TextChannel = await self.bot.fetch_channel(dest_id)
                await self.relay_message(message, channel)
    
    async def relay_message(self, message: Message, channel: TextChannel):
        # Relays a message to a given channel.
        author: User = message.author

        def user_to_color(user: User):
            # Maps discord discriminator to a hex color value.
            return int(int(user.discriminator) / 9999 * 0xffffff)
        
        embed = Embed(
            description=message.content,
            color=user_to_color(author)
        )

        embed.set_author(
            name=f"{author.display_name}#{author.discriminator}", 
            url=f"https://discord.com/users/{author.id}",
            icon_url=author.avatar_url
        )

        await channel.send(embed=embed)
    
    @commands.command()
    @commands.is_owner()
    async def add_bridge(self, ctx: Context, origin: TextChannel,
        dest: TextChannel):
        # Open the persistent dictionary.
        with shelve.open(BRIDGES_FN) as db:
            db[str(origin.id)] = str(dest.id)
        
        # Notify the executor.
        msg: Message = ctx.message
        await msg.add_reaction('👍')
    
    @commands.command()
    @commands.is_owner()
    async def remove_bridge(self, ctx: Context, origin: TextChannel):
        # Open the persistent dictionary.
        with shelve.open(BRIDGES_FN) as db:
            if str(origin) in db:
                del db[str(origin)]
        
        # Notify the executor.
        msg: Message = ctx.message
        await msg.add_reaction('👍')

def setup(bot):
    bot.add_cog(BridgeCog(bot))