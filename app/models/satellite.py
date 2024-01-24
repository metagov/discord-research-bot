from mongoengine import Document
from mongoengine.fields import *


class SatelliteModel(Document):
    id                  = IntField(primary_key=True)
    name                = StringField()
    pending_channel_id  = IntField()
    approved_channel_id = IntField()