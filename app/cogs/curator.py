from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from core.extension import Extension
from core.helpers import (
    create_pending_arow,
    create_request_arow,
    message_to_embed,
)

from discord_slash import cog_ext, ComponentContext
from discord.ext import commands
import discord

from models.alternate import Alternate, AlternateType
from models.message import Message, MessageStatus
from models.special import Special, SpecialType
from models.user import User, Choice
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

    async def on_message_curated(self, bot) -> None:
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

        await self.on_message_pending(bot, pending_channel)

    async def on_message_pending(self, bot, pending_channel) -> None:
        bot.logger.info("Sending pending message for %s.", self.message)

        # Send pending message to pending channel.
        pending_message = await pending_channel.send(
            embed=message_to_embed(self.message),
            components=[create_pending_arow()],
        )

        # Associate pending message with original message.
        Alternate.set(
            self.message_document,
            pending_message,
            AlternateType.PENDING,
        )

    async def on_message_request(self, bot) -> None:
        assert isinstance(self.message.author, discord.User)
        author_document = User.record(self.message.author)

        if author_document.choice == Choice.UNDECIDED:
            return await self.on_request_permission(bot)
        elif author_document.choice in [Choice.YES, Choice.ANONYMOUS]:
            anonymous = (author_document.choice == Choice.ANONYMOUS)
            return await self.on_message_fulfilled(bot, anonymous)
        else:
            # The author has decided to opt-out of the process.
            bot.logger.info("%s has been auto. declined.", self.message)

    def create_request_preview(self) -> discord.Embed:
        link = "https://rmit.edu.au/research/centres-collaborations/derc/" + \
            "cooperation-through-code/crypto-governance-observatory"

        embed = message_to_embed(self.message)
        embed.add_field(
            name="Introduction",
            inline=False,
            value=(
                "Hello from your Crypto-Governance Observatory! We're a team of"
                " researchers interested in the power of community governance."
                f" Find out more about us [here]({link}). Your post was"
                " highlighted by another use who thought it was interesting and"
                " we would like to use it in our research."
            ),
        )

        embed.add_field(
            name="Permission",
            inline=False,
            value=(
                "We're asking for permission to quote you in our research. If"
                " you agree, other posts that you have made in this Discord"
                " server may also be flagged and quoted in our research. Those"
                " posts will be included in our dataset, but you will receive a"
                " direct message every time one of your posts is flagged giving"
                " you the option to have that post removed from our data."
                " You may also withdraw your consent entirely at any time, in"
                " which case none of your posts will be quoted in any research"
                " publications."
            ),
        )

        embed.add_field(
            name="Consent Message",
            inline=False,
            value=(
                "Do you consent to participate in the research and have your"
                " your posts that are relevant to the research topic included"
                " in our data?\n"
                " • Yes, you may quote my posts and attribute them to my"
                " Discord handle.\n"
                " • Yes, you may quote my posts anonymously, do not use my"
                " Discord handle or any other identifying information.\n"
                " • No, you may not quote my posts in your research.\n"
            )
        )

        embed.add_field(
            name="Get Involved",
            inline=False,
            value=(
                " If you want to get more involved in The Observatory, we have"
                " awesome NFTs available for participants. Just join the"
                " #Observatory Channel in the Discord server. Thanks for"
                " helping us to understand the future of governance."
            )
        )

        return embed

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

        # Delete the pending message for the original message.
        await self.on_delete_pending(bot)

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


class Curator(Extension):
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload) -> None:
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message.guild is not None and str(payload.emoji) == "🔭":
            await self.on_message_reacted(message, payload.member)

    async def on_message_reacted(self, message, curator) -> None:
        curation_context = await CurationContext(
            message_document=Message.record(message),
            message=message,
            alternate_document=None,
            alternate=None,
            interactor=None,
        )
        
        curation_context.add_curator_document(curator)
        await curation_context.on_message_curated(self.bot)

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
