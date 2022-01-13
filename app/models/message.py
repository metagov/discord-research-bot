from mongoengine.fields import (
    ReferenceField,
    DateTimeField,
    BooleanField,
    StringField,
    EnumField,
    ListField,
    IntField,
)

from mongoengine import CASCADE, PULL, NULLIFY
from mongoengine.document import Document
from core.helpers import user_to_hash
from datetime import datetime
from enum import Enum
import discord
import logging
import json

from .comment import Comment
from .channel import Channel
from .member import Member
from .mirror import Mirror
from .guild import Guild
from .user import User

# To keep proper indentation-level.
C = {'reverse_delete_rule': CASCADE}
N = {'reverse_delete_rule': NULLIFY}
P = {'reverse_delete_rule': PULL}
logger = logging.getLogger(__name__)


class MessageStatus(Enum):
    CURATED         = 'curated'
    PENDING         = 'pending'
    REQUESTED       = 'requested'
    APPROVED        = 'approved'
    ANONYMOUS       = 'anonymous'
    REJECTED        = 'rejected'


class Message(Document, Mirror):
    id              = IntField(primary_key=True)
    channel         = ReferenceField(Channel, required=True, **C)
    guild           = ReferenceField(Guild, required=True, **C)
    content         = StringField(required=True)
    attachment_urls = ListField(StringField(), default=list)
    created_at      = DateTimeField(required=True)
    author_hash     = StringField(required=True)

    # The following are not required.
    edited_at       = DateTimeField(default=None)
    curated_by      = ListField(ReferenceField(User, **P), default=list)
    curated_at      = DateTimeField(default=datetime.utcnow)
    requested_by    = ReferenceField(User, default=None, **N)
    requested_at    = DateTimeField(default=None)
    fulfilled_at    = DateTimeField(default=None)
    author          = ReferenceField(User, default=None, **C)
    status          = EnumField(MessageStatus, default=MessageStatus.CURATED)
    deleted         = BooleanField(default=False)
    airtable_id     = StringField(default=None)

    @classmethod
    def record(cls, message, guild=None, channel=None) -> 'Message':
        """Get the document for a given message.

        :type message:  discord.Message
        :type guild:    Optional[Union[discord.Guild, Guild]]
        :type channel:  Optional[Union[discord.TextChannel, Channel]]
        :rtype:         Message
        """
        assert message.guild, "Cannot record direct messages!"

        if not isinstance(guild, Guild):
            guild = Guild.record(guild or message.guild)

        if not isinstance(channel, Channel):
            channel = Channel.record(channel or message.channel, guild=guild)

        attachment_urls = [str(x) for x in message.attachments]

        # TODO: Investigate solution that includes ``default`` from above.
        return cls.objects(id=message.id).modify(
            upsert=True,
            new=True,

            set_on_insert__id=message.id,
            set_on_insert__channel=channel,
            set_on_insert__guild=guild,
            set_on_insert__content=message.content,
            set_on_insert__attachment_urls=attachment_urls,
            set_on_insert__created_at=message.created_at,
            set_on_insert__edited_at=message.edited_at,
            set_on_insert__author_hash=user_to_hash(message.author),

            # These are defaults that we have to specify.
            set_on_insert__curated_by=[],
            set_on_insert__curated_at=datetime.utcnow(),
            set_on_insert__requested_by=None,
            set_on_insert__requested_at=None,
            set_on_insert__fulfilled_at=None,
            set_on_insert__author=None,
            set_on_insert__status=MessageStatus.CURATED,
            set_on_insert__deleted=False,
            set_on_insert__airtable_id=None
        )

    async def fetch(self, bot) -> discord.Message:
        channel = await self.channel.fetch(bot)

        try:
            return await channel.fetch_message(self.id)
        except Exception as exception:
            logger.warning('Message (%d/%d) no longer exists!',
                           channel.id, self.id)

            # Mark this message document as deleted and save it. Note that if
            # the channel was deleted, and this is why we cannot fetch the
            # message, it will appear as if the message was deleted.
            self.deleted = True
            self.save()

            raise exception

    def export(self) -> dict:
        def convert_timestamp(timestamp) -> str:
            return timestamp.isoformat() if timestamp else None

        message_dict = {
            'id'            : str(self.id),
            'deleted'       : self.deleted,
            'content'       : self.content,
            'created_at'    : convert_timestamp(self.created_at),
            'edited_at'     : convert_timestamp(self.edited_at),
            'author_hash'   : self.author_hash,
            'channel_id'    : str(self.channel.id),
            'channel_name'  : self.channel.name,
            'guild_id'      : str(self.guild.id),
            'guild_name'    : self.guild.name,
            'curated_by'    : self.curated_by[0].name if self.curated_by else None,
            'curated_at'    : convert_timestamp(self.curated_at),
            'requested_by'  : self.requested_by.name if self.requested_by else None,
            'requested_at'  : convert_timestamp(self.requested_at),
            'fulfilled_at'  : convert_timestamp(self.fulfilled_at),

        }

        if self.author:
            message_dict.update({
                'author_is_anonymous'   : False,
                'author_id'             : str(self.author.id),
                'author_name'           : self.author.name,
                'author_discriminator'  : self.author.discriminator,
                # 'author_nick'           : self.author.nick,
            })
        else:
            message_dict.update({
                'author_is_anonymous'   : True,
                'author_id'             : None,
                'author_name'           : None,
                'author_discriminator'  : None,
                # 'author_nick'           : None,
            })

        if self.attachment_urls:
            message_dict.update({
                'attachment_urls': ', '.join(self.attachment_urls)
            })

        return message_dict

    def retrieve_comments(self) -> str:
        to_export = []
        for comment_doc in Comment.objects(original=self):
            to_export.append({
                "author_name":  comment_doc.author.name,
                "created_at":   comment_doc.created_at.isoformat(),
                "author_id":    comment_doc.author.id,
                "content":      comment_doc.content,
            })
        return json.dumps(to_export)
