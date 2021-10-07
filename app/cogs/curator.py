from urllib.request import urlopen
from discord.channel import TextChannel
from discord_slash import cog_ext
from discord.ext import commands
from datetime import datetime
from database import *
from helpers import *
import discord
import logging
import asyncio

logger = logging.getLogger(__name__)


def has_been_curated_before(message) -> bool:
    """Checks whether or not a message has been curated before.

    :param message: Any message.
    :type message: Union[discord.Message, database.Message]
    :return: Whether or not it has happened.
    :rtype: bool
    """
    return db.message(message).status is not None


class CuratorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(is_admin)
    async def quickconfig(self, ctx, pending: discord.TextChannel,
                          approved: discord.TextChannel, guild: discord.Guild = None):
        """Sets a guild's pending and approved channels. The guild defaults to
        the guild you send the command in."""
        if guild is None:
            guild = ctx.guild

        db.guild(guild).pending_channel = pending
        db.guild(guild).approved_channel = approved

        await ctx.message.add_reaction('👍')

    @commands.command()
    @commands.check(is_admin)
    async def viewconfig(self, ctx, guild: discord.Guild = None):
        """Checks a guild's pending and approved channels. The guild defaults to
        the guild you send the command in."""
        if guild is None:
            guild = ctx.guild

        pending = db.guild(guild).pending_channel
        if pending:
            pending = await pending.fetch(self.bot)

        approved = db.guild(guild).approved_channel
        if approved:
            approved = await approved.fetch(self.bot)

        pending_text = f'{pending.guild.name} - #{pending.name}' \
            if pending else 'Not set'
        approved_text = f'{approved.guild.name} - #{approved.name}' \
            if approved else 'Not set'

        await ctx.reply(content=f'''pending={pending_text}
approved={approved_text}     
''')

    @commands.Cog.listener()
    async def on_message(self, message):
        # Do not proceed if it is not a reply.
        if message.reference is None:
            return

        # Do not proceed if it is our own reply.
        if message.author == self.bot.user:
            return logger.debug('Ignoring our own reply %s/%s',
                                message.channel.id, message.id)

        hook = db.message(channel_id=message.reference.channel_id,
                          message_id=message.reference.message_id)

        # Do not proceed if the reference is not commentable.
        if not hook.is_comment_hook:
            return logger.debug('Message %s/%s is not commentable',
                                hook.channel_id, hook.message_id)

        hook.original_message.add_comment(message.author, message.content)
        await message.add_reaction('👍')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Do not proceed if it was our own reaction.
        reactor = await self.bot.fetch_user(payload.user_id)
        if reactor == self.bot.user:
            return logger.debug('Ignoring own reaction on %s/%s',
                                payload.channel_id, payload.message_id)

        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        # Delegate to other method.
        await self.on_emoji_add(message, str(payload.emoji), reactor)

    async def on_emoji_add(self, message, emoji, reactor):
        # Check if it is the required emoji to curate this message.
        if emoji != get_emoji(self.bot, message):
            return logger.debug('Emoji %s not correct for %s/%s, returning',
                                emoji, message.channel.id, message.id)

        # Ensure that we are not in direct messages.
        if not message.guild:
            return logger.debug('%s/%s is not from a server, returning',
                                message.channel.id, message.id)

        # Ensure message has not been curated before.
        if has_been_curated_before(message):
            return logger.debug('%s/%s has already been curated before',
                                message.channel.id, message.id)

        await self.start_curation(message, reactor)

    async def start_curation(self, message, reactor):
        # Get the pending channel for this server.
        channel = db.guild(message.guild).pending_channel
        if channel is None:
            return logger.debug('Pending channel for %s is not set',
                                message.guild.id)
        else:
            # Turn document into real channel.
            channel = await channel.fetch(self.bot)

        # Avoid curating this message again and add extra metadata.
        db.message(message).status = MessageStatus.CURATED
        db.message(message).add_metadata({
            'curated_by': {
                'name':          reactor.name,
                'discriminator': reactor.discriminator,
                'id':            reactor.id
            },
            'curated_at': datetime.utcnow().isoformat()
        })

        # Add whoever curated this message to the footer.
        embed = message_to_embed(message)
        embed.add_field(
            name='Curated By',
            value='{0.name}#{0.discriminator}'.format(reactor),
            inline=False,
        )

        # Send to the pending channel.
        pending = await channel.send(
            embed=embed,
            components=[make_pending_action_row()],
        )

        # Tie original and pending messages together.
        db.message(message).pending_message = pending

    @cog_ext.cog_component(components=[
        REQUEST_PERMISSION_CUSTOM_ID,
    ])
    async def on_request_permission_pressed(self, ctx):
        # Defer immediately to avoid 'This interaction failed'.
        await ctx.defer(ignore=True)

        # Ensure no one can click this button twice.
        original = db.message(ctx.origin_message).original_message
        if original.status != MessageStatus.CURATED:
            return logger.error('Observer %s tried to request permission'
                                ' twice for %s/%s', ctx.author.id, original.channel_id,
                                original.message_id)
        else:
            original.status = MessageStatus.REQUESTED

            # Add extra metadata.
            original.add_metadata({
                'requested_by': {
                    'name':          ctx.author.name,
                    'discriminator': ctx.author.discriminator,
                    'id':            ctx.author.id
                },
                'requested_at': datetime.utcnow().isoformat()
            })

            original = await original.fetch(self.bot)

        # Disable the buttons and make the actual request.
        await disable_pending_action_row(ctx.origin_message)
        await self.send_permission_request(original)

        # Send commentable message by default.
        await self.send_comment_hook(ctx.author, original)

    async def send_comment_hook(self, user, original):
        """Sends a message to `user` which quotes `original` and explains that,
        if `user` replies, a comment will be added to `original` in database."""
        embed = message_to_embed(original)
        add_commentable_message(embed)
        hook = await user.send(embed=embed)

        # Register the message that we just sent as commentable.
        db.message(original).add_comment_hook(hook)

    async def send_permission_request(self, message):
        # Send an introduction if we haven't met this person yet.
        # author = db.user(message.author)
        # if not author.have_met:
        # await send_introduction(message.author, message.guild)
        # author.have_met = True

        # Send the actual request.
        embed = message_to_embed(message)
        add_introduction_field(embed, message.guild)
        add_consent_message(embed)
        request = await message.author.send(
            embed=embed,
            components=[make_request_action_row()]
        )

        # Tie original and request messages together.
        db.message(message).request_message = request

    @cog_ext.cog_component(components=[
        YES_CUSTOM_ID,
        YES_ANONYMOUSLY_CUSTOM_ID,
        NO_CUSTOM_ID
    ])
    async def on_permission_request_fulfilled(self, ctx):
        # Avoids 'This interaction failed'.
        await ctx.defer(ignore=True)

        # Ensure button cannot be pressed twice.
        original = db.message(ctx.origin_message).original_message
        if db.message(original).status >= MessageStatus.APPROVED:

            # Only works because `MessageStatus.APPROVED` is integer-wise
            # less than the others.
            return logger.error('User %s tried to fulfill twice for %s/%s',
                                ctx.author.id, original.channel_id, original.message_id)

        # Add extra metadata.
        original.add_metadata({
            'fulfilled_at': datetime.utcnow().isoformat()
        })

        # Set the appropriate status and add to database.
        if ctx.custom_id == YES_CUSTOM_ID:
            original.status = MessageStatus.APPROVED
            await original.add_to_database(self.bot)
        elif ctx.custom_id == YES_ANONYMOUSLY_CUSTOM_ID:
            original.status = MessageStatus.ANONYMOUS
            await original.add_to_database(self.bot, anonymize=True)
        else:  # User denied permission.
            original.status = MessageStatus.DENIED

        # Disable the buttons and convert to an actual message.
        await disable_request_action_row(ctx.origin_message)
        original = await original.fetch(self.bot)

        # Send thanks based on response.
        if ctx.custom_id == YES_CUSTOM_ID or \
                ctx.custom_id == YES_ANONYMOUSLY_CUSTOM_ID:
            await send_thanks(original.author, True, original.guild)
        else:  # User denied permission.
            await send_thanks(original.author, False, original.guild)

        # Delete the pending message.
        pending = await db.message(original).pending_message.fetch(self.bot)
        await pending.delete()

        # Quit early if user denied permission.
        if ctx.custom_id == NO_CUSTOM_ID:
            return logger.info('User %s denied permission for %s/%s',
                               ctx.author.id, original.channel.id, original.id)

        # Send to the approved channel.
        anonymous = (ctx.custom_id == YES_ANONYMOUSLY_CUSTOM_ID)
        await self.send_to_approved(original, anonymous=anonymous)
        await self.send_to_bridge(original, anonymous=anonymous)

    async def send_to_approved(self, message, anonymous=False):
        # Get the approved channel for the originating guild.
        channel = db.guild(message.guild).approved_channel
        if channel is None:
            return logger.error('Approved channel for %s is not set',
                                message.guild.id)
        else:
            channel = await channel.fetch(self.bot)

        # Send to the approved channel.
        embed = message_to_embed(message, anonymize=anonymous)
        add_commentable_message(embed)
        approved = await channel.send(embed=embed)

        # Tie original and approved messages together and make it commentable.
        db.message(message).approved_message = approved
        db.message(approved).original_message.add_comment_hook(approved)

    async def send_to_bridge(self, message, anonymous=False):
        # Get the bridge channel for the originating guild.
        channel = db.guild(message.guild).bridge_channel
        if channel is None:
            return logger.error('Bridge channel for %s is not set',
                                message.guild.id)
        else:
            channel = await channel.fetch(self.bot)

        # Send to the bridge channel.
        embed = message_to_embed(message, anonymize=anonymous)
        await channel.send(embed=embed)


def setup(bot):
    cog = CuratorCog(bot)
    bot.add_cog(cog)
