from mongoengine import Document
from mongoengine.fields import *
from enum import Enum
from .comment import CommentModel

class MessageStatus(Enum):
    TAGGED      = 'tagged'
    REQUESTED   = 'requested'
    APPROVED    = 'approved'
    REJECTED    = 'rejected'
    RETRACTED   = 'retracted'

class MessageModel(Document):
    id                  = IntField(primary_key=True)
    channel_id          = IntField()
    channel_name        = StringField()
    guild_id            = IntField()
    guild_name          = StringField()
    content             = StringField()
    attachments         = ListField(StringField(), default=list)

    author_id           = IntField()
    author_name         = StringField()
    author_avatar_url   = StringField()
    anonymous           = BooleanField()

    created_at          = DateTimeField()
    edited_at           = DateTimeField()
    jump_url            = StringField()

    status              = EnumField(MessageStatus)
    interface_id        = IntField()

    tagged_by_id        = IntField()
    tagged_by_name      = StringField()
    tagged_at           = DateTimeField()

    requested_by_id     = IntField()
    requested_by_name   = StringField()
    requested_at        = DateTimeField()

    approved_at         = DateTimeField()
    rejected_at         = DateTimeField()
    retracted_at        = DateTimeField()

    locks_at            = DateTimeField()

    comments            = ListField(ReferenceField(CommentModel))

