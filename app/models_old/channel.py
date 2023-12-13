from mongoengine.fields import (
    ReferenceField,
    DateTimeField,
    BooleanField,
    StringField,
    IntField,
)

from mongoengine.document import Document
from mongoengine import CASCADE
from datetime import datetime
import discord
import logging

from .mirror import Mirror
from .guild import Guild

# To keep proper indentation-level.
revcas = {'reverse_delete_rule': CASCADE}
logger = logging.getLogger(__name__)


class Channel(Document, Mirror):
    id          = IntField(primary_key=True)
    name        = StringField(required=True)

    # The following are not required.
    guild       = ReferenceField(Guild, default=None, **revcas)
    topic       = StringField(default=None)
    group       = StringField(default=None)
    updated_at  = DateTimeField(default=datetime.utcnow)
    deleted     = BooleanField(default=False)

    @classmethod
    def record(cls, channel, guild: Guild = None) -> None:
        """
        :type channel: discord.TextChannel
        :type guild:   Union[discord.Guild, Guild] | None
        """
        if not isinstance(guild, Guild):
            # Retrieve ``Guild`` from database if not already provided.
            guild = Guild.record(guild or channel.guild)

        # TODO: Investigate solution that includes ``default`` from above.
        return cls.objects(id=channel.id).modify(
            upsert=True,
            new=True,

            set__topic=channel.topic,
            set__updated_at=datetime.utcnow(),
            set__name=channel.name,

            # These are only updated at the beginning.
            set_on_insert__id=channel.id,
            set_on_insert__guild=guild,
            set_on_insert__group=None,
            set_on_insert__deleted=False,
        )

    async def fetch(self, bot) -> discord.TextChannel:
        try:
            return await bot.fetch_channel(self.id)
        except Exception as exception:
            logger.warning('Channel (%d) no longer exists!', self.id)

            # Mark the channel as deleted if it is not found.
            self.deleted = True
            self.save()

            raise exception
