from mongoengine.fields import DateTimeField, EnumField, ReferenceField
from mongoengine.document import Document
from mongoengine import CASCADE
from datetime import datetime
from enum import Enum
import discord

from .channel import Channel
from .guild import Guild

# To keep proper indentation-level.
C = {'reverse_delete_rule': CASCADE}


class SpecialType(Enum):
    PENDING     = 'pending'
    FULFILLED   = 'fulfilled'
    BRIDGE      = 'bridge'


class Special(Document):
    guild       = ReferenceField(Guild, unique_with='stype', required=True, **C)
    channel     = ReferenceField(Channel, required=True, **C)
    stype       = EnumField(SpecialType, required=True)

    # The following are not required.
    updated_at  = DateTimeField(default=datetime.utcnow)

    @classmethod
    async def get(cls, bot, guild, stype) -> discord.TextChannel:
        """Get configured channel with type for guild.

        :type bot:          commands.Bot
        :type guild:        Union[discord.Guild, Guild]
        :type stype:        SpecialType
        :raises ValueError: Channel with type is not configured for guild.
        :rtype:             discord.TextChannel
        """
        special = cls.objects(guild=guild, stype=stype).first()

        if not special:
            # Throw an exception, we can't do anything without a special.
            raise ValueError(f'No special found for {guild.name} and {stype}.')

        try:
            # We need to turn this document into an actual channel.
            channel = await bot.fetch_channel(special.channel.id)
        except:
            bot.logger.warning(f'{special.channel.id} not longer exists!')
            special.delete()

            # This will throw an exception the next time around.
            return await cls.get(bot, guild, stype)

        return channel

    @classmethod
    def set(cls, guild, stype, channel) -> 'Special':
        """Get configured channel with type for guild.

        :type bot:          commands.Bot
        :type guild:        Union[discord.Guild, Guild]
        :type stype:        SpecialType
        :raises ValueError: Channel with type is not configured for guild.
        :rtype:             discord.TextChannel
        """
        if isinstance(guild, discord.Guild):
            guild = Guild.record(guild)

        if isinstance(channel, discord.TextChannel):
            channel = Channel.record(channel, guild=guild)

        return cls.objects(guild=guild, stype=stype).modify(
            upsert=True,
            new=True,

            set__channel=channel,
            set__updated_at=datetime.utcnow(),

            # These are only updated at the beginning.
            set_on_insert__guild=guild,
            set_on_insert__stype=stype,
        )
