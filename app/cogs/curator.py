from traceback import print_exc
from discord_slash.utils.manage_components import *
from discord import RawReactionActionEvent
from discord.ext.commands.errors import *
from discord_slash import cog_ext
from discord.ext import commands
from discord_slash import *
from helpers import *
from models import *
import discord


def get_pending_actionrow(disabled: bool = False) -> dict:
    # Create the button(s) for a pending message.
    return create_actionrow(
        create_button(
            style=ButtonStyle.blue,
            label='Request permission',
            custom_id='request',
            disabled=disabled
        ),
    )


def get_request_actionrow(disabled: bool = False) -> dict:
    # Create the button(s) for a request message.
    return create_actionrow(
        create_button(
            style=ButtonStyle.green,
            label='Yes',
            custom_id='approve',
            disabled=disabled,
        ),
        create_button(
            style=ButtonStyle.gray,
            label='Yes, anonymously',
            custom_id='anonymous',
            disabled=disabled,
        ),
        create_button(
            style=ButtonStyle.red,
            label='No',
            custom_id='deny',
            disabled=disabled,
        ),
    )


class CuratorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        checks = [
            not message.author.bot,
            message.guild is not None,
            str(payload.emoji) == '🔭',
        ]

        if all(checks):
            await self.curate(message, payload.member)

    async def curate(self, message: discord.Message, curator: discord.User):
        if not message.guild:
            raise ValueError('Private messages cannot be curated')

        # Get document and add curator to list of curators.
        mdocument = Message.get(message.id)
        mdocument.channel_id = message.channel.id
        mdocument.guild_id = message.guild.id
        mdocument.curator_ids.append(curator.id)
        mdocument.save()

        if mdocument.status != Message.Status.DEFAULT:
            raise ValueError('Message already curated')

        gdocument = Guild.get(message.guild.id)
        if not gdocument.pending_id:
            raise ValueError('Pending channel not set')

        pchannel = await self.bot.fetch_channel(gdocument.pending_id)
        if not pchannel:
            raise ChannelNotFound(gdocument.pending_id)

        mdocument.status = Message.Status.CURATED
        mdocument.content = message.content
        mdocument.curated_at = datetime.utcnow()
        mdocument.save()

        # Send to this guild's pending channel and associate the two messages.
        pmessage = await pchannel.send(
            embed=message_to_embed(message),
            components=[get_pending_actionrow()]
        )

        amessage = Alternate.get(pmessage.id)
        amessage.channel_id = pmessage.channel.id
        amessage.guild_id = pmessage.guild.id
        amessage.type = Alternate.Type.PENDING
        amessage.original = mdocument
        amessage.save()

    @cog_ext.cog_component(components='request')
    async def on_request(self, ctx: ComponentContext):
        await ctx.defer(ignore=True)

        # Disable the button(s) immediately.
        disabled_actionrow = get_pending_actionrow(disabled=True)
        await ctx.origin_message.edit(components=[disabled_actionrow])

        amessage = Alternate.objects.with_id(ctx.origin_message_id)
        if not amessage:
            # TODO: Rewind the entire curation process, maybe?
            raise ValueError(ctx.origin_message_id)

        if amessage.original.status != Message.Status.CURATED:
            # TODO: Better error handling.
            raise ValueError('Message already requested')

        amessage.original.requester_id = ctx.author_id
        amessage.original.requested_at = datetime.utcnow()
        amessage.original.status = Message.Status.REQUESTED
        amessage.original.save()

        message = await amessage.original.fetch(self.bot)
        if not message:
            # TODO: Same as above, the message no longer exists.
            raise ValueError(amessage.original.id)

        # Issue the request and associate the two messages.
        rmessage = await message.author.send(
            embed=message_to_embed(message),
            components=[get_request_actionrow()]
        )

        zmessage = Alternate.get(rmessage.id)
        zmessage.channel_id = rmessage.channel.id
        zmessage.type = Alternate.Type.REQUEST
        zmessage.original = amessage.original
        zmessage.save()

    @cog_ext.cog_component(components=['approve', 'anonymous'])
    async def on_fulfill(self, ctx: ComponentContext):
        await ctx.defer(ignore=True)

        # Disable the button(s) immediately.
        disabled_actionrow = get_request_actionrow(disabled=True)
        await ctx.origin_message.edit(components=[disabled_actionrow])

        amessage = Alternate.objects.with_id(ctx.origin_message_id)
        if not amessage:
            # TODO: Rewind the entire curation process, maybe?
            raise ValueError(ctx.origin_message_id)

        if amessage.original.status != Message.Status.REQUESTED:
            # TODO: Better error handling.
            raise ValueError('Message already fulfilled')

        message = await amessage.original.fetch(self.bot)
        if not message:
            # We know it was the message's fault since we have the channel.
            raise MessageNotFound(amessage.id)
        await self.delete_pending(message)

        # Update the document details.
        anon = (ctx.custom_id == 'anonymous')
        amessage.original.author_id = (message.author.id if anon else 0)
        amessage.original.status = Message.Status.ANONYMOUS \
            if anon else Message.Status.APPROVED
        amessage.original.fulfilled_at = datetime.utcnow()
        amessage.original.save()

        # Send thanks to original message author.
        logger.info('%d/%d curated', message.channel.id, message.id)
        await self.send_thanks(message, True)
        await self.send_to_fulfilled(message, anon)
        await self.send_to_bridge(message, anon)

    async def send_to_fulfilled(self, message: discord.Message, anon: bool):
        gdocument = Guild.get(message.guild.id)
        if not gdocument.fulfilled_id:
            # TODO: Maybe un-disable the buttons?
            raise ValueError('Fulfilled channel not set')

        fchannel = await self.bot.fetch_channel(gdocument.fulfilled_id)
        if not fchannel:
            raise ChannelNotFound(gdocument.fulfilled_id)

        fembed = message_to_embed(message, anon)
        fmessage = await fchannel.send(embed=fembed)

        # Associate this message with the original.
        zmessage = Alternate.get(fmessage.id)
        zmessage.channel_id = fmessage.channel.id
        zmessage.guild_id = fmessage.guild.id
        zmessage.type = Alternate.Type.FULFILLED
        zmessage.original = Message.objects.with_id(message.id)
        zmessage.save()

    async def send_to_bridge(self, message: discord.Message, anon: bool):
        gdocument = Guild.get(message.guild.id)
        if not gdocument.fulfilled_id:
            # TODO: Maybe un-disable the buttons?
            raise ValueError('Fulfilled channel not set')

        bchannel = await self.bot.fetch_channel(gdocument.bridge_id)
        if not bchannel:
            raise ChannelNotFound(gdocument.bridge_id)

        fembed = message_to_embed(message, anon)
        fembed.add_field(
            name='👋 I\'m an approved message!',
            value=('My original author gave the people over at the'
                   ' Crypto-Governance Observatory permission to use me in'
                   ' their research!')
        )

        # Send the message to the bridge channel.
        bmessage = await bchannel.send(embed=fembed)

        # Associate this message with the original.
        zmessage = Alternate.get(bmessage.id)
        zmessage.channel_id = bmessage.channel.id
        zmessage.guild_id = bmessage.guild.id
        zmessage.type = Alternate.Type.BRIDGE
        zmessage.original = Message.objects.with_id(message.id)
        zmessage.save()

    @cog_ext.cog_component(components='deny')
    async def on_deny(self, ctx: ComponentContext):
        # TODO: There is repeated logic here, any solution?
        await ctx.defer(ignore=True)

        # Disable the button(s) immediately.
        disabled_actionrow = get_request_actionrow(disabled=True)
        await ctx.origin_message.edit(components=[disabled_actionrow])

        amessage = Alternate.objects.with_id(ctx.origin_message_id)
        if not amessage:
            # TODO: Rewind the entire curation process, maybe?
            raise ValueError(ctx.origin_message_id)

        if amessage.original.status != Message.Status.REQUESTED:
            # TODO: Better error handling.
            raise ValueError('Message already fulfilled')

        message = await amessage.original.fetch(self.bot)
        if not message:
            # TODO: Better error handling?
            raise MessageNotFound(amessage.id)
        await self.delete_pending(message)

        # Update the document details.
        amessage.original.status = Message.Status.DENIED
        amessage.original.fulfilled_at = datetime.utcnow()
        amessage.original.save()
        await self.send_thanks(message, False)

    async def send_thanks(self, message: discord.Message, said_yes: bool):
        # Thank the author even if they denied the request.
        text_yes = (
            'Thanks! Your post will help us to understand the future of'
            ' governance. If you want to get more involved in The Observatory,'
            ' we have some awesome NFTs available for participants. Just join'
            f' the "Cryto-Governance Channel" in the **{message.guild.name}** server.'
        )

        text_no = (
            'No problem. Thanks anyway and please head over to our channel'
            ' if you\'d like to learn more about what we do.'
        )

        await message.author.send(content=text_yes if said_yes else text_no)

    async def delete_pending(self, original: discord.Message):
        # Deletes the pending message associated with this message.
        try:
            mdocument = Message.objects.with_id(original.id)

            # TODO: Delete this document after we delete the message.
            pdocument = Alternate.objects(
                type=Alternate.Type.PENDING,
                original=mdocument,
            ).first()

            pmessage = await pdocument.original.fetch(self.bot)
            await pmessage.delete()
            logger.debug('Pending message for %d deleted', original.id)
        except:
            # TODO: Better error handling.
            print_exc()


def setup(bot):
    cog = CuratorCog(bot)
    bot.add_cog(cog)
