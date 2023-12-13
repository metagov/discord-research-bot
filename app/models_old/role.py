from mongoengine.fields import IntField, StringField
from mongoengine.document import EmbeddedDocument


class Role(EmbeddedDocument):
    id      = IntField(required=True)
    name    = StringField(required=True)
