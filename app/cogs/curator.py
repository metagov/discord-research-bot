# from typing import Text
# from discord.embeds import EmbedProxy, EmptyEmbed
# from discord.reaction import Reaction
# from discord.utils import get
# from discord.ext import commands
# from config import config
# from discord import Guild, TextChannel, RawReactionActionEvent, Message, Member
# from discord_slash.context import ComponentContext, SlashContext
# from discord_slash.model import ButtonStyle
# from discord_slash.utils import manage_components
# from discord_slash import cog_ext
# from utils import message_to_embed
# from datetime import datetime
# from discord import utils
# from tinydb import TinyDB
# import discord
# import re

# def build_database_entry(user: discord.User, content: str, timestamp: datetime,
#     guild: discord.Guild, channel: discord.TextChannel):
#     '''Returns a dictionary to be inserted into the database.'''
#     entry = {
#         'content': content,
#         'timestamp': timestamp.isoformat(),
#         'guild': {
#             '_id': guild.id,
#             'name': guild.name
#         },
#         'channel': {
#             '_id': channel.id,
#             'name': channel.name
#         }
#     }

#     # Handle the non-anonymous case.
#     if user:
#         entry['author'] = {
#             '_id': user.id,
#             'name': user.name
#         }
    
#     return entry

# def build_permission_action_row(disabled=False):
#     # Builds the action row for the permission message.
#     return manage_components.create_actionrow(
#         manage_components.create_button(
#             custom_id='accept',
#             style=ButtonStyle.green,
#             disabled=disabled,
#             label='yes'
#         ),

#         manage_components.create_button(
#             custom_id='anon',
#             style=ButtonStyle.blue,
#             disabled=disabled,
#             label='yes, anonymously'
#         ),

#         manage_components.create_button(
#             custom_id='decline',
#             style=ButtonStyle.red,
#             disabled=disabled,
#             label='no'
#         ),

#         manage_components.create_button(
#             style=ButtonStyle.URL,
#             label='join our server',
#             url='https://discord.com'
#         )
#     )

# class CuratorCog(commands.Cog):
#     def __init__(self, bot: commands.Bot):
#         print('Loaded', self.__class__.__name__)
#         self.bot = bot

#     @commands.command()
#     @commands.has_role('Curator') # TODO: Make this work in DMs.
#     async def curate(self, ctx: commands.Context, msg: discord.Message):
#         # Manually start curation process.
#         await self.send_to_pending(msg)

#     @commands.Cog.listener()
#     async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
#         # Triggered when a reaction is added to any message.
#         ch: TextChannel = await self.bot.fetch_channel(payload.channel_id)

#         # Ensure we are not in a DM.
#         if not ch.guild:
#             return

#         message: Message = await ch.fetch_message(payload.message_id)

#         # Only propagate when the reaction count is now 1.
#         reaction: Reaction = get(message.reactions, emoji=payload.emoji.name)
#         if reaction.count != 1:
#             return

#         reactor: Member = await ch.guild.fetch_member(payload.user_id)

#         # Check for the appropriate emoji.
#         if str(payload.emoji) == '🔭':
#             # Check for the appropriate role.
#             if utils.get(reactor.roles, name='Curator'): # TODO: Same as above.
#                 await self.send_to_pending(message)

#     async def send_to_pending(self, msg: discord.Message):
#         if 'pending_id' not in config:
#             print('pending_id is not set in the config!')
#             return

#         ch: TextChannel = await self.bot.fetch_channel(config['pending_id'])

#         # Create "ask for permission" button.
#         action_row = manage_components.create_actionrow(
#             manage_components.create_button(
#                 custom_id=f'ask-{msg.author.id}',
#                 style=ButtonStyle.green,
#                 label='request permission'
#             )
#         )

#         await ch.send(embed=message_to_embed(msg), components=[action_row])
#         # Go to on_component for the next step.

#     @commands.Cog.listener()
#     async def on_component(self, ctx: ComponentContext):
#         # Triggered on any component interaction.
#         if 'ask-' in ctx.custom_id:
#             embed: discord.Embed = ctx.origin_message.embeds[0]
#             await ctx.origin_message.delete()

#             # Ask user for permission.
#             askee_id = int(ctx.custom_id[4:])
#             askee: discord.User = await self.bot.fetch_user(askee_id)

#             embed.add_field(
#                 name='Consent Message',
#                 value=
#                     """We're asking for permission to quote you in our research.
#                     • Yes you may quote my post and attribute it to my Discord Handle
#                     • You may quote my post anonymously, do not use my Discord Handle or any other identifying information
#                     • No, you may not quote my post in your research
#                     Thanks for helping us understand the future of governance!"""
#             )

#             action_row = build_permission_action_row()
#             await askee.send(embed=embed, components=[action_row])
        
#         if 'accept' == ctx.custom_id:
#             embed: discord.Embed = ctx.origin_message.embeds[0]
#             embed.remove_field(0) # removing consent message

#             action_row = build_permission_action_row(disabled=True)
#             await ctx.origin_message.edit(components=[action_row])
#             await self.send_to_approved(embed)
            
#         if 'anon' == ctx.custom_id:
#             embed: discord.Embed = ctx.origin_message.embeds[0]
#             embed.remove_field(0) # removing consent message
#             embed.set_author(
#                 name=f'anonymous',
#                 url=embed.author.url,
#                 icon_url='https://i.imgur.com/qbkZFWO.png'
#             )

#             # Propagate the anonymized message.
#             action_row = build_permission_action_row(disabled=True)
#             await ctx.origin_message.edit(components=[action_row])
#             await self.send_to_approved(embed)
        
#         if 'decline' == ctx.custom_id:
#             action_row = build_permission_action_row(disabled=True)
#             await ctx.origin_message.edit(components=[action_row])
#             # Do nothing else, they have declined.
        
#         await ctx.send('Done!', delete_after=5)
    
#     async def send_to_approved(self, embed: discord.Embed):
#         print('Sending to approved!')

#         text = embed.author.url
#         parts = text.split('/')
#         guild_id = int(parts[4])
#         channel_id = int(parts[5])
#         msg_id = int(parts[6])

#         # Attempting to retrieve the message link.
#         message: discord.Message = None
#         guild = await self.bot.fetch_guild(guild_id)
#         if guild:
#             channel = await self.bot.fetch_channel(channel_id)                    
#             if channel:
#                 try:
#                     message = await channel.fetch_message(msg_id)
#                 except discord.errors.Forbidden as e:
#                     if e.code == 50001:
#                         print("I couldn't access that channel")
#             else:
#                 print("Channel may have been deleted")
#         else:
#             print("I couldn't access that server")

#         # Insert into database.
#         d = TinyDB('messages.json', indent=4)
#         entry = build_database_entry(
#             user=None if embed.author.name == 'anonymous' else message.author,
#             content=message.content,
#             timestamp=message.edited_at or message.created_at,
#             guild=message.guild,
#             channel=message.channel
#         )
#         d.insert(entry)

#         ch: TextChannel = await self.bot.fetch_channel(config['approved_id'])
#         await ch.send(embed=embed)
        
        
#     async def message_approved(self, embed: discord.Embed):
#         '''Called when a message should be sent to the approved channel.'''
#         # gd: Guild = await self.bot.fetch_guild(config['guild_id'])
#         ch: TextChannel = await self.bot.fetch_channel(config['approved_id'])
#         # embed.set_footer(text=EmptyEmbed)
#         await self.on_message_approved(embed)
#         await ch.send(embed=embed)

#     '''Commands to manipulate pending and approved channels.'''

#     @cog_ext.cog_subcommand(base='set', name='approved',
#         guild_ids=config['guild_ids'])
#     async def _set_approved(self, ctx: SlashContext):
#         config['approved_id'] = ctx.channel.id
#         await ctx.send('Done!')

#     @cog_ext.cog_subcommand(base='set', name='pending',
#         guild_ids=config['guild_ids'])
#     async def _set_pending(self, ctx: SlashContext):
#         config['pending_id'] = ctx.channel.id
#         await ctx.send('Done!')

# def setup(bot: commands.Bot):
#     cog = CuratorCog(bot)
#     bot.add_cog(cog)

import sys
from discord.ext import commands
from discord.ext.commands.converter import MessageConverter
from discord.raw_models import RawReactionActionEvent
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option
from discord import utils
from config import config

EMOJI = '🔭'

class CuratorCog(commands.Cog):
    '''Enables the curation of interesting messages.'''

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        channel = await self.bot.get_or_fetch_channel(payload.channel_id)
        if not channel.guild: # If we are in a DM.
            return
        
        message = await channel.fetch_message(payload.message_id)
        reaction = utils.get(message.reactions, emoji=payload.emoji.name)
        if reaction.count == 1 and str(payload.emoji) == EMOJI:
            # 1. Ensure message is not repeated if multiple curators try to
            #    curate the same message.
            # 2. Check for the appropriate emoji.
            reactor = await channel.guild.fetch_member(payload.user_id)
            if utils.get(reactor.roles, name='Curator'):
                await self.step_one(reactor, channel, message)
    
    async def step_one(self, reactor, channel, message):
        # In step one, we are given the original message and need to send it to
        # the pending messages channel. We need to attach a button that, when
        # pressed, proceeds to step two (asking the author of the original
        # message for permission). We take the the reactor and the channel so
        # we can raise an error if anything goes wrong.
        if 'pending_id' not in config:
            sys.stderr.write('\'pending_id\' is not set in the config!')

def setup(bot):
    bot.add_cog(CuratorCog(bot))