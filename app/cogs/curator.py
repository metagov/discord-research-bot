from datetime import datetime
from inspect import indentsize
from discord.ext.commands.errors import BadArgument, MissingRequiredArgument
from discord.message import Message
from discord.raw_models import RawReactionActionEvent
from discord.user import User
from discord_slash import cog_ext
from tinydb import TinyDB, where
from discord_slash.context import ComponentContext
from discord.ext import commands
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import (
    create_actionrow, 
    create_button
)
from utils import embed2message, message2embed, is_admin, user_hash
from typing import List
from discord import utils
from config import config
import discord

class CuratorCog(commands.Cog):
    """Allows curation and recording of interesting messages, ethically."""

    def __init__(self, bot):
        self.bot = bot
        self.db = TinyDB(config['db_fname'], indent=4)
    
    @commands.command()
    @commands.check(is_admin)
    async def setup(self, ctx: commands.Context, guild: discord.Guild,
        pending: discord.TextChannel, approved: discord.TextChannel):
        """Configures a channel for the curation process."""

        # Delegate to helper method.
        self._setup(guild.id, pending.id, approved.id)

        await pending.send(f'Pending messages from **{guild.name}** will now'
            ' now come here.')
        
        await approved.send(f'Approved messages from **{guild.name}** will'
            ' end up here.')

        await ctx.reply(f'Gotcha, {ctx.author.mention}. It should be working'
            ' upon the next reload or restart.')
        
    def _setup(self, guild_id, pending_id, approved_id):
        """Configures a guild to use a certain pending and approved channels."""
        config['guild_configs'][guild_id] = {
            'pending_id': pending_id,
            'approved_id': approved_id
        }

        config.save() # Need to manually save.

    @setup.error
    async def _setup_error(self, ctx: commands.Context, error):
        if isinstance(error, MissingRequiredArgument) or \
            isinstance(error, BadArgument):

            await ctx.reply(f'{ctx.author.mention}, it looks like there was'
                ' an error parsing your request. Make sure your parameters are'
                ' correct.')
        else:
            # Propagate upwards.
            raise error
    
    @commands.Cog.listener()
    async def on_component(self, ctx: ComponentContext):
        if not isinstance(ctx.custom_id, str):
            return # Let the interaction fail, this shouldn't happen.

        if ctx.custom_id.startswith('ask-'):
            await self.on_request_permission_clicked(ctx)
        
        elif ctx.custom_id == 'accept':
            await self.on_permission_granted(ctx)

        elif ctx.custom_id == 'reject':
            await self.on_permission_denied(ctx)
        
        elif ctx.custom_id == 'anonymous':
            await self.on_permission_granted(ctx, anonymous=True)
        
        elif ctx.custom_id == 'observer_comment':
            await self.on_add_observer_comment(ctx)

        # Have to respond in some way to preserve the interaction.
        await ctx.send('Ok!', delete_after=5)

    async def on_add_observer_comment(self, ctx: ComponentContext):
        """Observer just hit the 'Add comment' button."""
        embed = ctx.origin_message.embeds[0]
        message = await embed2message(self.bot, embed)
        await self.request_comment(message, ctx.author, is_curator=False)

    async def add_to_database(self, message, anonymous=False):
        """Add a message to the database."""
        curators = await self.get_curating_reactors(message)

        entry = {
            'user_hash': user_hash(message.author),
            'message_id': message.id,
            'guild': {
                'id': message.guild.id,
                'name': message.guild.name
            },
            'channel': {
                'id': message.channel.id,
                'name': message.channel.name
            },
            'curators': [],
            'date_added': datetime.utcnow().isoformat()
        }

        # Populate 'curators' list.
        for curator in curators:
            entry['curators'].append({
                'id': curator.id,
                'name': curator.name,
                'discriminator': curator.discriminator
            })

        if not anonymous:
            entry['user'] = {
                'id': message.author.id,
                'name': message.author.name,
                'discriminator': message.author.discriminator
            }

        # Add to database.
        self.db.table('messages').insert(entry)

    async def send_to_approved(self, message, anonymous=False):
        """We are given the embed without the consent message and just need
        to relay it to the corresponding approved channel."""
        guild_config = config['guild_configs'][str(message.guild.id)]
        channel = await self.bot.fetch_channel(guild_config['approved_id'])

        embed = message2embed(message)
        if anonymous:
            self.make_embed_anonymous(message.author, embed)
            
        # Add 'Add comment' button.
        action_row = create_actionrow(
            create_button(
                style=ButtonStyle.green,
                label='Add comment',
                custom_id='observer_comment'
            )
        )

        await channel.send(embed=embed, components=[action_row])

    async def request_comment(self, message, user, is_curator=True):
        """Asks `user` for a comment on why they reacted to or requested
        permission for a given message. Toggle `is_curator` to switch between
        curator and observer perspectives."""
        embed = message2embed(message)

        if is_curator:
            embed.add_field(
                name='Request for Comment',
                value=f'Hey, {user.mention}. It looks like you just curated '
f'a message from **{message.guild.name}** (see above). To add a comment, your '
'**next message in this DM will be used**. If you do not wish to add a comment'
' then please ignore this message.'
            )

            config['comment_status'][str(user.id)] = {
                'is_curator': True,
                'message_id': message.id,
                'channel': {
                    'id_': message.channel.id,
                    'name': message.channel.name
                }
            }
        else:
            # Is an observer.
            embed.add_field(
                name='Request for Comment',
                value=f'Hey, {user.mention}. It looks like you are trying to '
f'add a comment to a message from **{message.guild.name}** (see above). To add '
'a comment, your **next message in this DM will be used**. If you do not wish'
' to add a comment, then please ignore this message.'
            )

            config['comment_status'][str(user.id)] = {
                'is_curator': False,
                'message_id': message.id,
                'channel': {
                    'id_': message.channel.id,
                    'name': message.channel.name
                }
            }
        
        config.save() # Does not automatically happen.

        await user.send(embed=embed)

    def make_embed_anonymous(self, author, embed):
        """Anonymizes an embed."""
        embed.set_author(
            name=user_hash(author),
            url=embed.author.url,
            icon_url='https://i.imgur.com/qbkZFWO.png'
        )

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        # If not DM or we're not waiting for a comment from them.
        if message.guild or \
            str(message.author.id) not in config['comment_status']:
            return
        
        # They are adding a comment!
        await message.reply('Gotcha, I\'ll add that to the database.')
        data = config['comment_status'][str(message.author.id)]

        # Add to comment table.
        self.db.table('comments').insert({
            'is_curator': data['is_curator'],
            'message_id': data['message_id'],
            'channel': data['channel'],
            'comment': message.content
        })

        # Ensure no repeats.
        del config['comment_status'][str(message.author.id)]
        config.save() # Does not happen automatically.

    async def on_permission_granted(self, ctx, anonymous=False):
        """The askee just hit the 'Yes' or 'Yes, anonymously' buttons so we
        we will now both relay that message to the associated approved channel
        and add it to the database."""

        # Disable the buttons.
        row = self.make_permission_action_row(disabled=True)
        await ctx.edit_origin(components=[row])

        # Add to database and send to approved channel.
        message = await embed2message(self.bot, ctx.origin_message.embeds[0])
        await self.add_to_database(message, anonymous=anonymous)
        await self.send_to_approved(message, anonymous=anonymous)
    
    async def on_permission_denied(self, ctx):
        """The askee just hit the 'No' button, so we will simply disable the
        buttons and forget about it."""
        row = self.make_permission_action_row(disabled=True)
        await ctx.edit_origin(components=[row])

    def make_permission_action_row(self, disabled=False):
        """Makes the components for the """
        return create_actionrow(
            create_button(
                style=ButtonStyle.green,
                label='Yes',
                custom_id='accept',
                disabled=disabled
            ),
            create_button(
                style=ButtonStyle.blue,
                label='Yes, anonymously',
                custom_id='anonymous',
                disabled=disabled
            ),
            create_button(
                style=ButtonStyle.red,
                label='No',
                custom_id='reject',
                disabled=disabled
            ),
            create_button(
                style=ButtonStyle.URL,
                label='Join our server',
                url='https://discord.com/'
            )
        )

    async def on_request_permission_clicked(self, ctx: ComponentContext):
        """An observer has just hit the 'Request permission' button in the
        associated pending channel"""
        await ctx.origin_message.delete()

        # Recover author of original message.
        askee_id = int(ctx.custom_id[4:])
        askee = await self.bot.fetch_user(askee_id)

        # Recover original embed.
        embed = ctx.origin_message.embeds[0]
        row = self.make_permission_action_row()

        # Add consent message.
        embed.add_field(
            name='Consent Message',
            value='''We're asking for permission to quote you in our research.
• Yes you may quote my post and attribute it to my Discord Handle.
• You may quote my post anonymously, do not use my Discord Handle or any other identifying information.
• No, you may not quote my post in your research.
Thanks for helping us understand the future of governance!'''
        )

        await askee.send(embed=embed, components=[row])


    async def start_curation(self, message, triggerer):
        """A message has just been marked for curation, start the process of
        getting permission."""
        if str(message.guild.id) not in config['guild_configs']:
            return await triggerer.send(f'{triggerer.mention}, it looks like'
                f' you tried to curate a message in **{message.guild.name}**'
                ' but a bot administrator has not properly configured that'
                ' guild to support curation. Please ask a bot administrator'
                f' to configure **{message.guild.name}** properly and you will'
                ' then be able to curate messages there.')
        
        guild_config = config['guild_configs'][str(message.guild.id)]
        channel = await self.bot.fetch_channel(guild_config['pending_id'])

        # Add 'Request permission' button.
        action_row = create_actionrow(
            create_button(
                style=ButtonStyle.blue,
                label='Request permission',
                # Encode original message author.
                custom_id=f'ask-{message.author.id}'
            )
        )

        await channel.send(
            embed=message2embed(message),
            components=[action_row]
        )


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if str(payload.emoji) != config['emoji']:
            return
        
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if await self.get_curator_reaction_count(message) != 1:
            return # First curator to react starts process.
        
        member = await message.guild.fetch_member(payload.user_id)
        if not utils.get(member.roles, name=config['role_name']):
            return # Requires specific role.
        
        if not message.guild:
            return # We are in a DM.
        
        await self.request_comment(message, member, is_curator=True)
        await self.start_curation(message, member)

    async def get_curator_reaction_count(self, message) -> int:
        """Returns the number of curators that reacted with the correct emoji
        to this message."""
        curators = await self.get_curating_reactors(message)
        return len(curators)
    
    async def get_curating_reactors(self, message) -> List[discord.User]:
        """Returns the curators who reacted with the correct emoji to this
        message."""
        result = []
        reaction = utils.get(message.reactions, emoji=config['emoji'])
        async for user in reaction.users():
            member = await message.guild.fetch_member(user.id)
            if utils.get(member.roles, name=config['role_name']):
                result.append(user)
        return result
    
def setup(bot):
    cog = CuratorCog(bot)
    bot.add_cog(cog)