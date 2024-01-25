from mongoengine import Document
from mongoengine.fields import *


class CommentModel(Document):
    id              = IntField(primary_key=True)
    content         = StringField()
    author_id       = IntField()
    author_name     = StringField()
    created_at      = DateTimeField()