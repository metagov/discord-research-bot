from mongoengine.fields import (
    EmbeddedDocumentListField,
    ReferenceField,
    StringField,
    DateTimeField,
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


class Member(Document):
    guild       = ReferenceField(Guild, required=True, **revcas)
    user        = ReferenceField(User, required=True, **revcas)
    joined_at   = DateTimeField(required=True)
    roles       = EmbeddedDocumentListField(Role, default=list)

    # The following are not required.
    updated_at  = DateTimeField(default=datetime.utcnow)
    nick        = StringField(default=None)

    @classmethod
    def record(cls, member, guild, user=None) -> 'Member':
        """
        :type member:   Union[discord.Member, User]
        :type guild:    Union[discord.Guild, Guild]
        :type user:     User | None
        """
        if not isinstance(user, User):
            # Retrieve ``User`` from database if not already provided.
            user = User.record(user or member)

        if not isinstance(guild, Guild):
            # Retrieve ``Guild`` from database if not already provided.
            guild = Guild.record(guild)

        # Create list of roles from ``Member`` object.
        roles = [
            Role(id=role.id, name=role.name)
            for role in member.roles
        ]

        # TODO: Investigate solution that includes ``default`` from above.
        return cls.objects(guild=guild, user=user).modify(
            upsert=True,
            new=True,

            set__joined_at=member.joined_at,
            set__roles=roles,
            set__updated_at=datetime.utcnow(),
            set__nick=member.nick,

            # These are only updated at the beginning.
            set_on_insert__guild=guild,
            set_on_insert__user=user,
        )
