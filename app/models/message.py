from mongoengine.fields import (
    DateTimeField,
    EnumField,
    IntField,
    ReferenceField,
    ListField,
    StringField,
)

from mongoengine import CASCADE, PULL, NULLIFY
from mongoengine.document import Document
from core.helpers import user_to_hash
from datetime import datetime
from enum import Enum
import discord
import logging

from .channel import Channel
from .member import Member
from .mirror import Mirror
from .guild import Guild
from .user import User


# To keep proper indentation-level.
C = {'reverse_delete_rule': CASCADE}
N = {'reverse_delete_rule': NULLIFY}
P = {'reverse_delete_rule': PULL}
logger = logging.getLogger(__name__)


class MessageStatus(Enum):
    DEFAULT         = 'default'
    PENDING         = 'pending'
    REQUESTED       = 'requested'
    APPROVED        = 'approved'
    ANONYMOUS       = 'anonymous'
    REJECTED        = 'rejected'


class Message(Document, Mirror):
    id              = IntField(primary_key=True)
    channel         = ReferenceField(Channel, required=True, **C)
    guild           = ReferenceField(Guild, required=True, **C)
    content         = StringField(required=True)
    attachment_urls = ListField(StringField(), default=list)
    created_at      = DateTimeField(required=True)
    author_hash     = StringField(required=True)

    # The following are not required.
    edited_at       = DateTimeField(default=None)
    curated_by      = ListField(ReferenceField(Member, **P), default=list)
    curated_at      = DateTimeField(default=datetime.utcnow)
    requested_by    = ReferenceField(User, default=None, **N)
    requested_at    = DateTimeField(default=None)
    fulfilled_at    = DateTimeField(default=None)
    author          = ReferenceField(Member, default=None, **C)
    status          = EnumField(MessageStatus, default=MessageStatus.DEFAULT)

    @classmethod
    def record(cls, message, guild=None, channel=None) -> 'Message':
        """Get the document for a given message.

        :type message:  discord.Message
        :type guild:    Optional[Union[discord.Guild, Guild]]
        :type channel:  Optional[Union[discord.TextChannel, Channel]]
        :rtype:         Message
        """
        
        assert message.guild, "Cannot record direct messages!"

        if not isinstance(guild, Guild):
            guild = Guild.record(guild or message.guild)
        
        if not isinstance(channel, Channel):
            channel = Channel.record(channel or message.channel, guild=guild)

        attachment_urls = [str(x) for x in message.attachments]

        # TODO: Investigate solution that includes ``default`` from above.
        return cls.objects(id=message.id).modify(
            upsert=True,
            new=True,

            set_on_insert__id=message.id,
            set_on_insert__channel=channel,
            set_on_insert__guild=guild,
            set_on_insert__content=message.content,
            set_on_insert__attachment_urls=attachment_urls,
            set_on_insert__created_at=message.created_at,
            set_on_insert__edited_at=message.edited_at,
            set_on_insert__author_hash=user_to_hash(message.author),

            # These are defaults that we have to specify.
            set_on_insert__curated_by=[],
            set_on_insert__curated_at=datetime.utcnow(),
            set_on_insert__requested_by=None,
            set_on_insert__requested_at=None,
            set_on_insert__fulfilled_at=None,
            set_on_insert__author=None,
            set_on_insert__status=MessageStatus.DEFAULT,
        )

    async def fetch(self, bot) -> discord.Message:
        channel = await self.channel.fetch(bot)

        try:
            return await channel.fetch_message(self.id)
        except Exception as exception:
            logger.warning('Message %d no longer exists!', self.id)
            self.delete()
            raise exception