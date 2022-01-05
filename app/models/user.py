from mongoengine.fields import (
    DateTimeField,
    StringField,
    EnumField,
    IntField,
)

from mongoengine.document import Document
from core.helpers import user_to_hash
from datetime import datetime
from enum import Enum

from .mirror import Mirror


class Choice(Enum):
    UNDECIDED       = 'undecided'
    YES             = 'yes'
    ANONYMOUS       = 'anonymous'
    NO              = 'no'


class User(Document, Mirror):
    id              = IntField(primary_key=True)
    hash            = StringField(required=True)
    name            = StringField(required=True)
    discriminator   = StringField(required=True)
    created_at      = DateTimeField(required=True)
    avatar_url      = StringField(required=True)

    # The following are not required.
    choice          = EnumField(Choice, default=Choice.UNDECIDED)
    updated_at      = DateTimeField(default=datetime.utcnow)

    @classmethod
    def record(cls, user) -> 'User':
        # TODO: Investigate solution that includes ``default`` from above.
        return cls.objects(id=user.id).modify(
            upsert=True,
            new=True,

            set__name=user.name,
            set__discriminator=user.discriminator,
            set__avatar_url=str(user.avatar_url),
            set__updated_at=datetime.utcnow(),

            # These are only updated at the beginning.
            set_on_insert__id=user.id,
            set_on_insert__hash=user_to_hash(user),
            set_on_insert__choice=Choice.UNDECIDED,
            set_on_insert__created_at=user.created_at,
        )
