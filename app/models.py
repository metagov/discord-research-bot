from mongoengine.document import *
from mongoengine.fields import *
from mongoengine import CASCADE
from datetime import datetime
from enum import Enum
import discord


class Channel(Document):
    id = IntField(required=True)
    group = StringField(default='default')


class Message(Document):
    id = IntField(primary_key=True)
    channel_id = IntField(required=True)
    guild_id = IntField(default=0)

    class Status(Enum):
        DEFAULT = 'default'
        CURATED = 'curated'
        REQUESTED = 'requested'
        APPROVED = 'approved'
        ANONYMOUS = 'anonymous'
        DENIED = 'denied'

    author_id = IntField(default=0)
    content = StringField(default='')  # Snapshot at beginning.
    status = EnumField(Status, default=Status.DEFAULT)

    @classmethod
    def get(cls, id) -> 'Message':
        return cls.objects.with_id(id) or cls(id=id)

    async def fetch(self, bot) -> discord.Message:
        # Returns `None` if either channel or message could not be found.
        channel = await bot.fetch_channel(self.channel_id)
        return None if not channel else await channel.fetch_message(self.id)

    # ... Metadata
    curated_at = DateTimeField(default=datetime.utcnow)
    requested_at = DateTimeField(default=datetime.utcnow)
    fulfilled_at = DateTimeField(default=datetime.utcnow)

    curator_ids = ListField(IntField(), default=list)
    requester_id = IntField(default=0)


class Guild(Document):
    id = IntField(primary_key=True)
    pending_id = IntField(default=0)
    fulfilled_id = IntField(default=0)
    bridge_id = IntField(default=0)

    @classmethod
    def get(cls, id) -> 'Guild':
        return cls.objects.with_id(id) or cls(id=id)


class Alternate(Document):
    # An alternate is a pointer to a message.
    id = IntField(primary_key=True)
    channel_id = IntField(required=True)
    guild_id = IntField(default=0)

    class Type(Enum):
        BRIDGE = 'bridge'
        PENDING = 'pending'
        REQUEST = 'request'
        FULFILLED = 'fulfilled'
        COMMENTABLE = 'commentable'

    type = EnumField(Type, required=True)
    original = ReferenceField(Message, required=True,
                              reverse_delete_rule=CASCADE)

    @classmethod
    def get(cls, id) -> 'Alternate':
        return cls.objects.with_id(id) or cls(id=id)
