from datetime import datetime
from core.helpers import create_pending_arow, message_to_embed
from models.alternate import Alternate, AlternateType
from models.message import Message, MessageStatus
from models.special import Special, SpecialType
from discord_slash import ComponentContext
from core.extension import Extension
from discord_slash import cog_ext
from discord.ext import commands
from models.member import Member
import discord


class Curator(Extension):
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload) -> None:
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        checks = [
            message.guild is not None,
            str(payload.emoji) == '🔭',
        ]

        if all(checks):
            await self.curate(message, payload.member)

    async def curate(self, message, curator) -> None:
        original_document   = Message.record(message)
        curator_document    = Member.record(curator)

        if curator_document not in original_document.curated_by:
            original_document.curated_by.append(curator_document)
            original_document.save()

        pending_channel = await Special.get(
            self.bot,
            original_document.guild,
            SpecialType.PENDING,
        )

        if original_document.status != MessageStatus.DEFAULT:
            raise ValueError('Message is already curated: %s' % message.id)

        original_document.status        = MessageStatus.CURATED
        original_document.curated_at    = datetime.utcnow()
        original_document.save()

        embed = message_to_embed(message)
        embed.add_field(
            name='Note',
            value=(
                'If you want to request with a comment, reply to this'
                ' message before clicking the button.'
            ),
        )

        self.bot.logger.info('Pending message sent for %d', message.id)
        pending_message = await pending_channel.send(
            embed=embed,
            components=[create_pending_arow()],
        )

        Alternate.set(message, pending_message, AlternateType.PENDING)

    @cog_ext.cog_component(components='request')
    async def on_request_pressed(self, ctx: ComponentContext) -> None:
        # TODO: Better syntax.
        alternate_document = Alternate.objects(
            message_id=ctx.origin_message_id,
            atype=AlternateType.PENDING,
        ).first()

        if not alternate_document:
            raise ValueError('No alternate document %d with type %s',
                             ctx.origin_message_id, AlternateType.PENDING)

        original_document   = alternate_document.original
        original_message    = await original_document.fetch(self.bot)
        print(original_message)
        # TODO: Bruh.

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
