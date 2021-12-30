from core.helpers import create_pending_arow, message_to_embed
from discord_slash import ComponentContext
from core.extension import Extension
from discord_slash import cog_ext
from discord.ext import commands
from datetime import datetime
import discord

from models.alternate import Alternate, AlternateType
from models.message import Message, MessageStatus
from models.special import Special, SpecialType
from models.member import Member
from models.user import User


class Curator(Extension):
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload) -> None:
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        # Notice that bot messages can be curated.
        checks = [
            message.guild is not None,
            str(payload.emoji) == '🔭',
        ]

        if all(checks):
            await self.curate(message, payload.member)

    async def curate(self, message, curator) -> None:
        original_document = Message.record(message)
        curator_document = Member.record(curator)

        # Add curator to list of curators if not already there.
        if curator_document not in original_document.curated_by:
            original_document.curated_by.append(curator_document)
            original_document.save()

        # Get the pending channel for the guild the message is in.
        pending_channel = await Special.get(
            self.bot,
            original_document.guild,
            SpecialType.PENDING,
        )

        if original_document.status != MessageStatus.DEFAULT:
            raise ValueError('Message is already curated: %s' % message.id)

        # Ensure the message cannot be curated more than once.
        original_document.status = MessageStatus.CURATED
        original_document.curated_at = datetime.utcnow()
        original_document.save()

        embed = message_to_embed(message)
        embed.add_field(
            name='Note',
            value=(
                'If you want to request with a comment, reply to this'
                ' message before clicking the button.'
            ),
        )

        self.bot.logger.info('Sending pending message for 0x%x', message.id)
        pending_message = await pending_channel.send(
            embed=embed,
            components=[create_pending_arow()],
        )

        # Associate the pending message with the original message, so we can
        # recover it when a researcher clicks the button.
        Alternate.set(
            message,
            pending_message,
            AlternateType.PENDING,
        )

    @cog_ext.cog_component(components='request')
    async def on_request_pressed(self, ctx: ComponentContext) -> None:
        alternate_document = Alternate.find(
            AlternateType.PENDING,
            ctx.origin_message_id,
        )

        # If the above does not throw an exception, then check it here.
        if not alternate_document:
            raise ValueError('No alternate document %d with type %s.',
                             ctx.origin_message_id, AlternateType.PENDING)

        original_document = alternate_document.original
        original_message = await original_document.fetch(self.bot)

        # Handle the whole thing separately if the author is a bot.
        if original_message.bot:
            await self.on_message_approved(original_message, False)
            return

    async def on_message_fulfilled(self, original_message, anonymous) -> None:
        original_document = Message.record(original_message)

        # Get the fulfilled channel for the guild the message is in.
        fulfilled_channel = await Special.get(
            self.bot,
            original_document.guild,
            SpecialType.FULFILLED,
        )

        # Update fields on the document for the original message.
        original_document.fulfilled_at = datetime.utcnow()
        original_document.status = MessageStatus.ANONYMOUS

        if not anonymous:
            original_document.author = Member.record(original_message.author)
            original_document.status = MessageStatus.APPROVED

        original_document.save()

        # Create a new message in the fulfilled channel.
        embed = message_to_embed(original_message, anonymous)
        fulfilled_message = await fulfilled_channel.send(embed=embed)

        # Associate the fulfilled message with the original message.
        Alternate.set(
            original_message,
            fulfilled_message,
            AlternateType.FULFILLED,
        )

    # Commands
    # ========

    @commands.command(name='spending')
    @commands.is_owner()
    async def spending(self, ctx, guild: discord.Guild) -> None:
        Special.set(guild, SpecialType.PENDING, ctx.channel)
        await ctx.send('Done!')

    @commands.command(name='sfulfilled')
    @commands.is_owner()
    async def sfulfilled(self, ctx, guild: discord.Guild) -> None:
        Special.set(guild, SpecialType.FULFILLED, ctx.channel)
        await ctx.send('Done!')


def setup(bot) -> None:
    cog = Curator(bot)
    bot.add_cog(cog)
