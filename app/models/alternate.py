from mongoengine.fields import (
    ReferenceField,
    BooleanField,
    EnumField,
    IntField,
)

from mongoengine.document import Document
from mongoengine import CASCADE
from enum import Enum
import discord
import logging

from .message import Message

# To keep proper indentation-level.
C = {'reverse_delete_rule': CASCADE}
logger = logging.getLogger(__name__)


class AlternateType(Enum):
    PENDING     = 'pending'
    REQUEST     = 'request'
    FULFILLED   = 'fulfilled'
    BRIDGE      = 'bridge'


class Alternate(Document):
    original    = ReferenceField(Message, required=True, unique_with='atype', **C)
    atype       = EnumField(AlternateType, required=True)
    message_id  = IntField(required=True)
    channel_id  = IntField(required=True)

    # The following are not required.
    deleted = BooleanField(default=False)

    @classmethod
    def set(cls, original, alternate, atype) -> 'Alternate':
        """Set an alternate message for an original message.

        :type original:     Union[discord.Message, Message]
        :type alternate:    Union[discord.Message, Message]
        :type atype:        AlternateType
        """
        # If the alternate message is a ``discord.Message``, convert it to a
        # ``Message`` so that it can be referenced.
        if isinstance(original, discord.Message):
            original = Message.record(original)

        return cls.objects(original=original, atype=atype).modify(
            upsert=True,
            new=True,

            set__message_id=alternate.id,
            set__channel_id=alternate.channel.id,

            # These are only updated at the beginning.
            set_on_insert__original=original,
            set_on_insert__atype=atype,
            set_on_insert__deleted=False,
        )

    @classmethod
    def find(cls, atype, message_id) -> 'Alternate':
        """Given the ``discord.Message`` representation of an alternate message,
        find the corresponding ``Alternate`` document.

        :type atype:        AlternateType
        :type message_id:   int
        """
        return cls.objects(
            atype=atype,
            message_id=message_id,
        ).first()

    @classmethod
    def find_by_original(cls, original, atype) -> 'Alternate':
        """Given the original document or message, find its ``Alternate`` with
        the specified ``AlternateType``.

        :type original:     Union[discord.Message, Message]
        :type atype:        AlternateType
        """
        # If the original message is a ``discord.Message``, convert it to a
        # ``Message`` so that it can be referenced.
        if isinstance(original, discord.Message):
            original = Message.record(original)

        return cls.objects(
            original=original,
            atype=atype,
        ).first()

    async def fetch(self, bot) -> discord.Message:
        try:
            channel = await bot.fetch_channel(self.channel_id)
            return await channel.fetch_message(self.message_id)
        except Exception as exception:
            logger.warning("Alternate (%d/%d) no longer exists!",
                           self.channel_id, self.message_id)

            # Mark this message document as deleted and save it.
            self.deleted = True
            self.save()

            raise Exception
