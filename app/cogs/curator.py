from core.helpers import (
    create_pending_arow,
    create_request_arow,
    message_to_embed,
)

from discord_slash import ComponentContext
from core.extension import Extension
from discord_slash import cog_ext
from discord.ext import commands
from datetime import datetime
import discord

from models.alternate import Alternate, AlternateType
from models.message import Message, MessageStatus
from models.special import Special, SpecialType
from models.user import User, Choice
from models.member import Member


class Curator(Extension):
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload) -> None:
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if (message.guild is not None) and str(payload.emoji) == '🔭':
            await self.curate(message, payload.member)

    async def curate(self, ogmsg, curator) -> None:
        ogmsg_doc = Message.record(ogmsg)
        curdoc = Member.record(curator)

        # Add curator to list of curators if not already there.
        if curdoc not in ogmsg_doc.curated_by:
            ogmsg_doc.curated_by.append(curdoc)
            ogmsg_doc.save()

        # Get the pending channel for the guild the message is in.
        pendchan = await Special.get(self.bot, ogmsg_doc.guild, SpecialType.PENDING)
        if ogmsg_doc.status != MessageStatus.CURATED:
            raise ValueError('Message is already curated: %s' % ogmsg.id)

        # Update fields on original message document.
        ogmsg_doc.status = MessageStatus.CURATED
        ogmsg_doc.curated_at = datetime.utcnow()
        ogmsg_doc.save()

        ogmsg_embed = message_to_embed(ogmsg)
        # ogmsg_embed.add_field(
        #     name='Note',
        #     value=(
        #         'If you want to request with a comment, reply to this'
        #         ' message before clicking the button.'
        #     ),
        # )

        self.bot.logger.info("Sending pending message for %s.", ogmsg)
        pendmsg = await pendchan.send(
            embed=ogmsg_embed,
            components=[create_pending_arow()],
        )

        # Associate the pending message with the original message.
        Alternate.set(ogmsg_doc, pendmsg, AlternateType.PENDING)

    @cog_ext.cog_component(components='request')
    async def on_request_pressed(self, ctx: ComponentContext) -> None:
        # Disable the buttons on the pending message.
        await ctx.edit_origin(components=[create_pending_arow(disabled=True)])

        # This message is a pending message, find its document.
        pendmsg_doc = Alternate.find(
            AlternateType.PENDING,
            ctx.origin_message_id,
        )

        # If the above does not throw an exception, then check it here.
        if not pendmsg_doc:
            raise ValueError('No alternate document (%d) with type %s.',
                             ctx.origin_message_id, AlternateType.PENDING)

        # Find the message the pending message is referring to.
        ogmsg_doc = pendmsg_doc.original
        ogmsg = await ogmsg_doc.fetch(self.bot)
        authdoc = User.record(ogmsg.author)

        # Handle the whole thing separately if the author is a bot.
        if ogmsg.author.bot:
            await self.on_message_approved(ogmsg, False)
            return

        # If the author hasn't decided, send a request message.
        if authdoc.choice == Choice.UNDECIDED:
            await self.on_request_permission(ogmsg_doc, ogmsg, ctx.author)
            return

    async def on_request_permission(self, ogmsg_doc, ogmsg, reqr) -> None:
        self.bot.logger.info("%s is requesting permission to curate %s from %s.",
                             reqr, ogmsg, ogmsg.author)

        # Change the status of the message document.
        ogmsg_doc.status = MessageStatus.REQUESTED
        ogmsg_doc.requested_at = datetime.utcnow()
        ogmsg_doc.requested_by = User.record(reqr)
        ogmsg_doc.save()

        # Send the request message to the author.
        reqmsg = await ogmsg.author.send(
            embed=message_to_embed(ogmsg),
            components=[create_request_arow()],
        )

        # Associate the request message with the original message.
        Alternate.set(ogmsg_doc, reqmsg, AlternateType.REQUEST)

    async def on_delete_pending_message(self, ogmsg_doc, ogmsg) -> None:
        self.bot.logger.info("Deleting pending message for %s.", ogmsg)

        # Find the alternate document corresponding to the pending message.
        pendmsg_doc = Alternate.find_by_original(
            ogmsg_doc,
            AlternateType.PENDING,
        )

        # Silently fail if the alternate document is not found.
        if not pendmsg_doc:
            return

        # Turn the pending message document into a message and delete it.
        pendmsg = await pendmsg_doc.fetch(self.bot)
        await pendmsg.delete()

        # Update the pending message document.
        pendmsg_doc.deleted = True
        pendmsg_doc.save()

    async def on_message_fulfilled(self, ogmsg, anonymous, ogmsg_doc=None) -> None:
        ogmsg_doc = ogmsg_doc or Message.record(ogmsg)
        ogmsg = ogmsg or await ogmsg_doc.fetch(self.bot)

        # Get the fulfilled channel for the guild the message is in.
        fulfilled_channel = await Special.get(
            self.bot,
            ogmsg_doc.guild,
            SpecialType.FULFILLED,
        )

        # Update fields on the document for the original message.
        ogmsg_doc.fulfilled_at = datetime.utcnow()
        ogmsg_doc.status = MessageStatus.ANONYMOUS
        if not anonymous:
            ogmsg_doc.author = Member.record(ogmsg.author)
            ogmsg_doc.status = MessageStatus.APPROVED
        ogmsg_doc.save()

        # Create a new message in the fulfilled channel.
        embed = message_to_embed(ogmsg, anonymous)
        fulfmsg = await fulfilled_channel.send(embed=embed)

        # Associate the fulfilled message with the original message.
        Alternate.set(ogmsg, fulfmsg, AlternateType.FULFILLED)

        # Delete the original pending message.
        await self.on_delete_pending_message(ogmsg_doc, ogmsg)

    @cog_ext.cog_component(components=['yes', 'anonymous'])
    async def on_fulfilled_pressed(self, ctx: ComponentContext) -> None:
        await ctx.edit_origin(components=[create_request_arow(disabled=True)])

        reqmsg_doc = Alternate.find(
            AlternateType.REQUEST,
            ctx.origin_message_id,
        )

        await self.on_message_fulfilled(
            None,
            ctx.custom_id == 'anonymous',
            reqmsg_doc.original,
        )

    @cog_ext.cog_component(components='no')
    async def on_no_pressed(self, ctx: ComponentContext) -> None:
        await ctx.edit_origin(components=[create_request_arow(disabled=True)])
        # ...

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
