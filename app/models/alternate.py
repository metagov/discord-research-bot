from mongoengine.fields import IntField, ReferenceField, EnumField
from mongoengine.document import Document
from mongoengine import CASCADE
from enum import Enum
import discord

from .message import Message


# To keep proper indentation-level.
C = {'reverse_delete_rule': CASCADE}


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

    @classmethod
    def set(cls, original, alternate, atype) -> 'Alternate':
        """
        :type original:     Union[discord.Message, Message]
        :type alternate:    Union[discord.Message, Message]
        """
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
        )
