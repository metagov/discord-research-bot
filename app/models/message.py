from mongoengine import Document
from mongoengine.fields import *


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

    curation_id         = IntField()
    curated_by_id       = IntField()
    curated_by_name     = StringField()
    curated_at          = DateTimeField()

    request_id          = IntField()
    requested_by_id     = IntField()
    requested_by_name   = StringField
    requested_at        = DateTimeField()

    approval_id         = IntField()
    approved_at         = DateTimeField()

    # status              = EnumField()
    retraction_id       = IntField()
    retracted           = BooleanField(default=False)

