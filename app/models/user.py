from mongoengine import Document
from mongoengine.fields import *
from enum import Enum

class ConsentStatus(Enum):
    UNDECIDED       = 'undecided'
    YES             = 'yes'
    ANONYMOUS       = 'anonymous'
    NO              = 'no'

class UserModel(Document):
    id      = IntField(primary_key=True)
    name    = StringField()
    consent = EnumField(ConsentStatus, default=ConsentStatus.UNDECIDED)