from mongoengine.fields import (
    EmbeddedDocumentListField,
    ReferenceField,
    DateTimeField,
    StringField,
)

from mongoengine.document import Document
from mongoengine import CASCADE
from datetime import datetime

from .mirror import Mirror
from .guild import Guild
from .user import User
from .role import Role

# To keep proper indentation-level.
revcas = {'reverse_delete_rule': CASCADE}


class Member(Document, Mirror):
    guild       = ReferenceField(Guild, required=True, **revcas)
    user        = ReferenceField(User, required=True, **revcas)
    joined_at   = DateTimeField(required=True)
    roles       = EmbeddedDocumentListField(Role, default=list)

    # The following are not required.
    updated_at  = DateTimeField(default=datetime.utcnow)
    nick        = StringField(default=None)

    @classmethod
    def record(cls, member, guild=None, user=None) -> 'Member':
        """
        :type member:   Union[discord.Member, User]
        :type guild:    Union[discord.Guild, Guild] | None
        :type user:     User | None
        """
        if (user is not None) and not isinstance(user, User):
            raise TypeError(f'Expected `User`, got `{type(user).__name__}`.')

        if (guild is not None) and not isinstance(guild, Guild):
            raise TypeError(f'Expected `Guild`, got `{type(guild).__name__}`.')

        # TODO: Investigate solution that includes ``default`` from above.
        return cls.objects(guild=guild, user=user).modify(
            upsert=True,
            new=True,

            set__joined_at=member.joined_at,
            set__roles=[Role(id=x.id, name=x.name) for x in member.roles],
            set__updated_at=datetime.utcnow(),
            set__nick=member.nick,

            # These are only updated at the beginning.
            set_on_insert__guild=guild or Guild.record(member.guild),
            set_on_insert__user=user or User.record(member),
        )
