from mongoengine import Document
from mongoengine.fields import *
from enum import Enum

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
    author_id           = IntField()
    author_name         = StringField()
    author_avatar_url   = StringField()
    content             = StringField()
    attachments         = ListField(StringField(), default=list)

    created_at          = DateTimeField()
    edited_at           = DateTimeField()
    jump_url            = StringField()

    status              = EnumField(MessageStatus)

    # curation_id         = IntField()
    tagged_by_id       = IntField()
    tagged_by_name     = StringField()
    tagged_at          = DateTimeField()

    # request_id          = IntField()
    requested_by_id     = IntField()
    requested_by_name   = StringField()
    requested_at        = DateTimeField()

    # approval_id         = IntField()
    approved_at         = DateTimeField()

    # retraction_id       = IntField()
    # retracted           = BooleanField(default=False)
    retracted_at       = DateTimeField()

