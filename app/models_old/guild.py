from mongoengine.fields import DateTimeField, IntField, StringField
from mongoengine.document import Document
from datetime import datetime

from .mirror import Mirror


class Guild(Document, Mirror):
    id          = IntField(primary_key=True)
    name        = StringField(required=True)
    created_at  = DateTimeField(required=True)

    # The following are not required.
    updated_at  = DateTimeField(default=datetime.utcnow)
    description = StringField(default=None)

    @classmethod
    def record(cls, guild) -> 'Guild':
        # TODO: Investigate solution that includes ``default`` from above.
        return cls.objects(id=guild.id).modify(
            upsert=True,
            new=True,

            set__name=guild.name,
            set__updated_at=datetime.utcnow(),
            set__description=guild.description,

            # These are only updated at the beginning.
            set_on_insert__id=guild.id,
            set_on_insert__created_at=guild.created_at,
        )
