from dataclasses import dataclass
from datetime import datetime, timedelta
from email import message
from typing import Optional, Union
from traceback import print_exc

from core.extension import Extension
from core.helpers import (
    create_delete_arow,
    create_pending_arow,
    create_request_arow,
    message_to_embed,
)

from core.responses import responses

from discord_slash import cog_ext, ComponentContext
from discord_slash import ComponentMessage
from discord.ext import commands
import discord

from models.alternate import Alternate, AlternateType
from models.message import Message, MessageStatus
from models.special import Special, SpecialType
from models.user import User, Choice
from models.comment import Comment
from models.member import Member


@dataclass
class CurationContext:
    message_document:   Message
    message:            discord.Message
    alternate_document: Optional[Alternate]
    alternate:          Optional[discord.Message]
    interactor:         Optional[discord.User]

    def add_curator_document(self, curator) -> None:
        curator_document = User.record(curator)
        if curator_document not in self.message_document.curated_by:
            self.message_document.curated_by.append(curator_document)
            self.message_document.save()

    @classmethod
    async def from_component_context(cls, bot, context, atype) -> "CurationContext":
        # 1. Context is on pending message.
        # 2. Context is on request message.
        document = Alternate.find(atype, context.origin_message_id)
        if document is None:
            
            try:
                broken_message_url = context.origin_message.embeds[0].author.url
                print("Broken message detected, original url:", broken_message_url)
            except Exception as error:
                print("Failed to repair broken pending message!")
                print_exc()
            
            raise ValueError("No `Alternate` found for %s.", context)

        return cls(
            message_document=document.original,
            message=await document.original.fetch(bot),
            alternate_document=document,
            alternate=context.origin_message,
            interactor=context.author,
        )

    async def disable_components(self, factory) -> None:
        await self.alternate.edit(components=[factory(disabled=True)])

    def remember_decision(self, bot, user: Union[discord.User, User], choice) -> None:
        bot.logger.info("Remembering decision (%s) for %s.", choice, user)

        # Convert to a `User` so we can manipulate it.
        if not isinstance(user, User):
            user = User.record(user)

        # Update the fields on the `User` document.
        user.choice = choice
        user.save()

    async def on_message_curated(self, bot, curator) -> None:
        pending_channel = await Special.get(
            bot,
            self.message_document.guild,
            SpecialType.PENDING,
        )

        # Check if message has already been curated.
        if self.message_document.status != MessageStatus.CURATED:
            raise ValueError("%s is already curated.", self.message)

        # Update fields on original message document.
        self.message_document.status = MessageStatus.CURATED
        self.message_document.curated_at = datetime.utcnow()
        self.message_document.save()

        await self.on_message_pending(bot, pending_channel, curator)

    async def on_message_pending(self, bot, pending_channel, curator) -> None:
        bot.logger.info("Sending pending message for %s.", self.message)

        embed = message_to_embed(self.message)
        embed.add_field(
            name='Curated By',
            value='{0.name}#{0.discriminator}'.format(curator),
            inline=False
        )

        # Send pending message to pending channel.
        pending_message = await pending_channel.send(
            embed=embed,
            components=[create_pending_arow()],
        )

        # Associate pending message with original message.
        Alternate.set(
            self.message_document,
            pending_message,
            AlternateType.PENDING,
        )

    async def on_message_request(self, bot) -> None:
        # assert isinstance(self.message.author, discord.User)
        author_document = User.record(self.message.author)

        if author_document.choice == Choice.UNDECIDED:
            bot.logger.info("UNDECIDED")
            return await self.on_request_permission(bot)
        elif author_document.choice in [Choice.YES, Choice.ANONYMOUS]:
            bot.logger.info("YES or ANONYMOUS")
            anonymous = (author_document.choice == Choice.ANONYMOUS)
            return await self.on_message_fulfilled(bot, anonymous)
        else:
            # The author has decided to opt-out of the process.
            bot.logger.info("%s has been auto declined.", self.message)
            await self.on_delete_pending(bot)

    def create_request_preview(self) -> discord.Embed:
        embed = message_to_embed(self.message)
        embed.add_field(
            name="Introduction",
            inline=False,
            value=(responses.introduction_message),
        )

        embed.add_field(
            name="Permission",
            inline=False,
            value=(responses.permission_message),
        )

        embed.add_field(
            name="Consent Message",
            inline=False,
            value=(responses.consent_message)
        )

        embed.add_field(
            name="Get Involved",
            inline=False,
            value=(responses.get_involved_message)
        )

        return embed

    def is_older_than(self, days) -> bool:
        return self.message_document.fulfilled_at + \
            timedelta(days) < datetime.utcnow()

    def create_delete_preview(self, bot) -> discord.Embed:
        author_document = User.record(self.message.author)
        opt_in_status = ""

        if author_document.choice not in [Choice.YES, Choice.ANONYMOUS]:
            bot.logger.warning("Choice of %s was unexpected!", author_document)
        else:
            opt_in_status = "You are currently opted-in"
            opt_in_status += "." if author_document.choice == Choice.YES else ", anonymously."

        embed = message_to_embed(self.message)
        embed.add_field(
            name="Removal",
            value=(responses.prompt_delete_message.format(opt_in_status)),
        )

        return embed

    async def on_send_delete(self, bot) -> None:
        bot.logger.info("Sending delete message for %s.", self.message)
        delete_message = await self.message.author.send(
            embed=self.create_delete_preview(bot),
            components=[create_delete_arow()],
        )

        # Associate delete message with original message.
        Alternate.set(
            self.message_document,
            delete_message,
            AlternateType.DELETE,
        )

    async def on_request_permission(self, bot) -> None:
        bot.logger.info("Requesting permission for %s.", self.message)
        await self.disable_components(create_pending_arow)

        # Update the fields on the original message document.
        self.message_document.status = MessageStatus.REQUESTED
        self.message_document.requested_at = datetime.utcnow()
        self.message_document.requested_by = User.record(self.interactor)
        self.message_document.save()

        # Send the request message to the author.
        request_message = await self.message.author.send(
            embed=self.create_request_preview(),
            components=[create_request_arow()],
        )

        # Send the latest comment from a researcher as well.
        comment_doc = Comment.objects(original=self.message_document).first()
        if comment_doc:
            await request_message.reply(
                "A researcher has also left the following comment:"
                f" '{comment_doc.content}'"
            )

        # Associate request message with original message.
        Alternate.set(
            self.message_document,
            request_message,
            AlternateType.REQUEST,
        )

    async def on_message_fulfilled(self, bot, anonymous) -> None:
        bot.logger.info("Sending fulfilled message for %s.", self.message)

        fulfilled_channel = await Special.get(
            bot,
            self.message_document.guild,
            SpecialType.FULFILLED,
        )

        # Update fields on original message document.
        self.message_document.fulfilled_at = datetime.utcnow()
        self.message_document.status = MessageStatus.ANONYMOUS
        if not anonymous:
            self.message_document.author = User.record(self.message.author)
            self.message_document.status = MessageStatus.APPROVED
        self.message_document.save()

        embed = embed = message_to_embed(self.message, anonymous)
        fulfilled_message = await fulfilled_channel.send(embed=embed)

        # Associate fulfilled message with original message.
        Alternate.set(
            self.message_document,
            fulfilled_message,
            AlternateType.FULFILLED,
        )

        # Insert the original message document into the Airtable queue.
        airtable_cog = bot.get_cog("Air")
        airtable_cog.insert(self.message_document)

        await self.on_delete_pending(bot)
        await self.on_send_delete(bot)
        await self.on_bridge_repeat(bot)

    async def on_delete_pending(self, bot) -> None:
        # `Alternate` could be pending message if user has opted-in or out.
        assert self.alternate_document and self.alternate
        bot.logger.info("Deleting pending message for %s.", self.message)

        pending_document = Alternate.find_by_original(
            self.message_document,
            AlternateType.PENDING,
        )

        # Silently fail if pending message is not found.
        if not pending_document:
            return

        pending_message = await pending_document.fetch(bot)
        await pending_message.delete()

        # Update fields on pending message document.
        pending_document.deleted = True
        pending_document.save()

    async def on_bridge_repeat(self, bot) -> None:
        try:
            # Encapsulated in a try-except block.
            bridge_channel = await Special.get(
                bot,
                self.message_document.guild,
                SpecialType.BRIDGE,
            )
        except Exception as exception:
            return bot.logger.warning("on_bridge_repeat(%s) failed!",
                                      self.message_document)

        # Create a `discord.Embed` to send in the bridge channel.
        author_document = User.record(self.message.author)
        anonymous = (author_document.choice == Choice.ANONYMOUS)
        embed = message_to_embed(self.message, anonymous)
        embed.add_field(
            name="Curated",
            value=(responses.on_curation_message),
        )

        bridge_message = await bridge_channel.send(embed=embed)

        # Associate the bridge message with the original message.
        Alternate.set(
            self.message,
            bridge_message,
            AlternateType.BRIDGE,
        )

    def on_message_deleted(self, bot) -> None:
        bot.logger.info("Removing %s from database.", self.message_document)
        airtable_cog = bot.get_cog("Air")
        airtable_cog.delete(self.message_document)


class Curator(Extension):
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.reference is not None:
            # Interpret the reference message as an `Alternate`.
            alternate = Alternate.objects(
                message_id=message.reference.message_id,
                atype__in=[AlternateType.PENDING, AlternateType.FULFILLED],
            ).first()

            if alternate:
                # Save this message as a comment of original message.
                Comment.save(alternate.original, message)
                await message.reply("Comment added! 👍")
                self.bot.logger.info("Added comment %s for %s.",
                                     message, alternate.original)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload) -> None:
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message.guild is not None and str(payload.emoji) == "🔭":
            await self.on_message_reacted(message, payload.member)

    async def on_message_reacted(self, message, curator) -> None:
        curation_context = CurationContext(
            message_document=Message.record(message),
            message=message,
            alternate_document=None,
            alternate=None,
            interactor=None,
        )

        curation_context.add_curator_document(curator)
        await curation_context.on_message_curated(self.bot, curator)

    @cog_ext.cog_component(components="request")
    async def on_request_pressed(self, context: ComponentContext) -> None:
        await context.edit_origin()

        curation_context = await CurationContext.from_component_context(
            self.bot,
            context,
            AlternateType.PENDING,
        )

        # Ask author for permission if they have not opted-in or out.
        await curation_context.on_message_request(self.bot)

    @cog_ext.cog_component(components=["yes", "anonymous"])
    async def on_fulfilled_pressed(self, context: ComponentContext) -> None:
        await context.edit_origin()

        curation_context = await CurationContext.from_component_context(
            self.bot,
            context,
            AlternateType.REQUEST,
        )

        # Opt-in the author if they have not opted-in or out.
        anonymous = (context.custom_id == "anonymous")
        choice = Choice.YES if not anonymous else Choice.ANONYMOUS
        curation_context.remember_decision(self.bot, context.author, choice)

        await curation_context.disable_components(create_request_arow)
        await curation_context.on_message_fulfilled(self.bot, anonymous)

    @cog_ext.cog_component(components="no")
    async def on_no_pressed(self, context: ComponentContext) -> None:
        await context.edit_origin()

        curation_context = await CurationContext.from_component_context(
            self.bot,
            context,
            AlternateType.REQUEST,
        )

        curation_context.remember_decision(self.bot, context.author, Choice.NO)
        await curation_context.disable_components(create_request_arow)

    @cog_ext.cog_component(components="delete")
    async def on_delete_pressed(self, context: ComponentContext) -> None:
        await context.edit_origin()

        curation_context = await CurationContext.from_component_context(
            self.bot,
            context,
            AlternateType.DELETE,
        )

        # Disable the components so they cannot be interacted with again.
        await curation_context.disable_components(create_delete_arow)

        # Check if the time limit for this message has been exceeded.
        days_limit = 10
        if curation_context.is_older_than(days=days_limit):
            return await context.reply(responses.on_delete_fail_message.format(days_limit))

        curation_context.on_message_deleted(self.bot)
        await context.reply(responses.on_delete_success_message)

    # Commands
    # ========

    @commands.command(name='spending')
    @commands.is_owner()
    async def spending(self, ctx, guild: discord.Guild) -> None:
        Special.set(guild, SpecialType.PENDING, ctx.channel)
        await ctx.message.add_reaction("👍")

    @commands.command(name='sfulfilled')
    @commands.is_owner()
    async def sfulfilled(self, ctx, guild: discord.Guild) -> None:
        Special.set(guild, SpecialType.FULFILLED, ctx.channel)
        await ctx.message.add_reaction("👍")

    @commands.command(name="sforget")
    @commands.is_owner()
    async def sforget(self, ctx) -> None:
        user_document = User.record(ctx.author)
        user_document.choice = Choice.UNDECIDED
        user_document.save()
        await ctx.message.add_reaction("👍")


def setup(bot) -> None:
    cog = Curator(bot)
    bot.add_cog(cog)
