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

from .channel import Channel
from .message import Message
from .member import Member
from .mirror import Mirror
from .guild import Guild
from .user import User


# To keep proper indentation-level.
C = {'reverse_delete_rule': CASCADE}
N = {'reverse_delete_rule': NULLIFY}
P = {'reverse_delete_rule': PULL}


class Comment(Document):
    id          = IntField(primary_key=True)
    content     = StringField(required=True)
    created_at  = DateTimeField(required=True)
    author      = ReferenceField(User, required=True, **C)
    original    = ReferenceField(Message, required=True, **C)

    # The following are not required.
    edited_at   = DateTimeField(default=None)

    @classmethod
    def save(cls, original, comment, user=None) -> 'Comment':
        """
        :type original: Union[discord.Message, Message]
        :type comment:  discord.Message
        :type user:     Union[discord.User, User] | None
        """
        if isinstance(original, discord.Message):
            original = Message.record(original)

        if not isinstance(comment, discord.Message):
            raise ValueError("Expected discord.Message, got %s",
                             type(comment).__name__)
                
        if not isinstance(user, User):
            user = User.record(user or original.author)

        return cls.objects(id=comment.id).modify(
            upsert=True,
            new=True,

            set__content=comment.content,
            set__edited_at=comment.edited_at,

            # These are only updated at the beginning.
            set_on_insert__id=comment.id,
            set_on_insert__created_at=comment.created_at,
            set_on_insert__author=user,
            set_on_insert__original=original,
        )
