from discord.channel import TextChannel
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option
import discord

GUILD_IDS = [860079798616457227]

def to_embed(msg: discord.Message) -> discord.Embed:
    '''Turns a message into an embed(ded).'''
    embed = discord.Embed(
        description=msg.content,
        color=discord.Color.blue(),
    )

    author: discord.User = msg.author

    embed.set_author(
        name=f"{author.display_name}#{author.discriminator}", 
        url=f"https://discord.com/users/{author.id}",
        icon_url=author.avatar_url
    )

    embed.set_footer(text=f'{msg.guild.name} - #{msg.channel.name}')

    return embed

class BridgeCog(commands.Cog):
    '''Transports messages across guild boundaries.'''
    
    def __init__(self, bot: commands.Bot):
        print('Loaded', self.__class__.__name__)
        self.channels = {} # Channel -> List[Tag].
        self.tags = {}     # Tag -> List[Channel].
        self.bot = bot

    @cog_ext.cog_subcommand(
        base='bridge',
        name='add',
        description='Adds a tag to a list associated with this channel. ' + \
           'Messages are replicated via common tags.',
        guild_ids=GUILD_IDS,
        options=[
            create_option(
                name='tag',
                description='Any string.',
                option_type=3, # 3 means string.
                required=True
            )
        ])
    async def _bridge_add(self, ctx: SlashContext, tag: str):
        if ctx.channel_id not in self.channels:
            self.channels[ctx.channel_id] = []
        self.channels[ctx.channel_id].append(tag)
        if tag not in self.tags:
            self.tags[tag] = []
        self.tags[tag].append(ctx.channel_id)
        await ctx.send('Done!')
        print(self.channels)
        print(self.tags)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        # Ensure it wasn't sent by us and is in an interesting channel.
        if msg.author == self.bot.user or msg.channel.id not in self.channels:
            print('Quitting early!')
            return
        
        sent = set()
        embed = to_embed(msg)
        for tag in self.channels[msg.channel.id]:
            for _id in self.tags[tag]:
                if _id == msg.channel.id or _id in sent:
                    continue
                channel: TextChannel = await self.bot.fetch_channel(_id)
                await channel.send(embed=embed)
                sent.add(_id)

def setup(bot: commands.Bot):
    cog = BridgeCog(bot)
    bot.add_cog(cog)

# import discord
# from discord.embeds import Embed
# from discord.ext import commands
# from discord import TextChannel
# from discord.ext.commands import Context
# import shelve

# from discord.message import Message
# from discord.user import User

# BRIDGES_FN = 'bridges.db'

# # Relays messages between channels.
# class BridgeCog(commands.Cog):

#     def __init__(self, bot: commands.Bot):
#         print('Loaded Bridge Cog')
#         self.bot = bot

#     def cog_unload(self):
#         print('Unloaded Bridge Cog')

#     @commands.Cog.listener()
#     async def on_message(self, message: discord.Message):
#         # Do not respond to our own messages!
#         if message.author == self.bot.user:
#             return
        
#         # This does not work in DMs!
#         if not message.guild:
#             return
        
#         # Open the persistent dictionary.
#         with shelve.open(BRIDGES_FN) as db:
#             if str(message.channel.id) in db:
#                 dest_id = int(db[str(message.channel.id)])
#                 channel: TextChannel = await self.bot.fetch_channel(dest_id)
#                 await self.relay_message(message, channel)
    
#     async def relay_message(self, message: Message, channel: TextChannel):
#         # Relays a message to a given channel.
#         author: User = message.author

#         def user_to_color(user: User):
#             # Maps discord discriminator to a hex color value.
#             return int(int(user.discriminator) / 9999 * 0xffffff)
        
#         embed = Embed(
#             description=message.content,
#             color=user_to_color(author)
#         )

#         embed.set_author(
#             name=f"{author.display_name}#{author.discriminator}", 
#             url=f"https://discord.com/users/{author.id}",
#             icon_url=author.avatar_url
#         )

#         await channel.send(embed=embed)
    
#     @commands.command()
#     @commands.is_owner()
#     async def add_bridge(self, ctx: Context, origin: TextChannel,
#         dest: TextChannel):
#         # Open the persistent dictionary.
#         with shelve.open(BRIDGES_FN) as db:
#             db[str(origin.id)] = str(dest.id)
        
#         # Notify the executor.
#         msg: Message = ctx.message
#         await msg.add_reaction('👍')
    
#     @commands.command()
#     @commands.is_owner()
#     async def remove_bridge(self, ctx: Context, origin: TextChannel):
#         # Open the persistent dictionary.
#         with shelve.open(BRIDGES_FN) as db:
#             if str(origin) in db:
#                 del db[str(origin)]
        
#         # Notify the executor.
#         msg: Message = ctx.message
#         await msg.add_reaction('👍')

# def setup(bot):
#     bot.add_cog(BridgeCog(bot))