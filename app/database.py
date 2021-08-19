from abc import ABC, abstractproperty
from tinydb.table import Document
from tinydb.queries import Query
from tinydb import TinyDB, where
from helpers import user_to_hash
from datetime import datetime
from typing import Generator, List, Optional
from enum import IntEnum
from constants import *
import logging
import discord

logger = logging.getLogger(__name__)

# Again, to ensure that I do not make a spelling mistake.
STATUSES_TABLE_NAME   = 'statuses'
ALTERNATES_TABLE_NAME = 'alternates'
CHANNELS_TABLE_NAME   = 'channels'
USERS_TABLE_NAME      = 'users'
HOOKS_TABLE_NAME      = 'hooks'
COMMENTS_TABLE_NAME   = 'comments'
MESSAGES_TABLE_NAME   = 'messages'
ADMINS_TABLE_NAME     = 'admins'
BRIDGES_TABLE_NAME    = 'bridges'

class LiveDocument(ABC):
    def __init__(self, handle, **kwargs):
        self.handle = handle
    
    @abstractproperty
    def base_query(self) -> Query:
        raise NotImplementedError()

class MessageStatus(IntEnum):
    CURATED = 0
    REQUESTED = 1
    APPROVED = 2
    ANONYMOUS = 3
    DENIED = 4

class AlternateType(IntEnum):
    """When we send a message in the pending channel for a given guild, or when
    we send the message to a message's author that requests for their
    permission, we need a way to tie all of these messages together. If we want
    to, say, delete the pending message when the author fulfills the permission
    request, then we need a way to go from the request message to the pending
    one. Using these enums, we can do this."""
    PENDING = 0
    REQUEST = 1
    APPROVED = 2
    COMMENT = 3

class Message(LiveDocument):
    def __init__(self, handle, message=None, channel_id=0, message_id=0):
        super().__init__(handle)
        self.channel_id = channel_id
        self.message_id = message_id

        if isinstance(message, discord.Message):
            self.channel_id = message.channel.id
            self.message_id = message.id
        
        elif message is not None: # This class.
            self.channel_id = message.channel_id
            self.message_id = message.message_id
    
    @property
    def base_query(self) -> Query:
        return (where('original_cid') == self.channel_id) & \
               (where('original_mid') == self.message_id)

    @property
    def status(self) -> Optional[MessageStatus]:
        result = self.handle.table(STATUSES_TABLE_NAME).get(self.base_query)
        return None if result is None else MessageStatus(result['status'])
    
    @status.setter
    def status(self, new_status):
        self.handle.table(STATUSES_TABLE_NAME).upsert({
            'original_cid': self.channel_id,
            'original_mid': self.message_id,
            'status':       int(new_status)
        }, self.base_query)

    # ...

    def get_alternate(self, altype) -> Optional['Message']:
        """Gets the alternate message for an original one i.e., the pending
        or approved messages.

        :param altype: The type of alternate.
        :type altype: AternateType
        :return: Either the alternate or `None` if it is not set.
        :rtype: Optional[Message]
        """
        query = self.base_query & (where('altype') == int(altype))
        result = self.handle.table(ALTERNATES_TABLE_NAME).get(query)
        return None if result is None else \
            Message(self.handle, channel_id=result['message_cid'],
                                 message_id=result['message_mid'])
    
    def set_alternate(self, message, altype):
        """Sets the alternate message for an original one i.e., the pending
        or approved messages.
        
        :param message: The message or alternate.
        :type message: Union[discord.Message, Message]
        :param altype: The type of alternate.
        :type altype: AternateType
        """
        channel_id = 0
        message_id = 0

        if isinstance(message, discord.Message):
            channel_id = message.channel.id
            message_id = message.id
        
        else: # This class.
            channel_id = message.channel_id
            message_id = message.message_id
        
        logger.debug('Setting %s for %s/%s to %s/%s', altype, self.channel_id,
            self.message_id, channel_id, message_id)

        query = self.base_query & (where('altype') == int(altype))
        self.handle.table(ALTERNATES_TABLE_NAME).upsert({
            'original_cid': self.channel_id,
            'original_mid': self.message_id,
            'altype':       int(altype),
            'message_cid':  channel_id,
            'message_mid':  message_id
        }, query)
    
    # ...

    @property
    def pending_message(self):
        return self.get_alternate(AlternateType.PENDING)
    
    @pending_message.setter
    def pending_message(self, new_pending):
        self.set_alternate(new_pending, AlternateType.PENDING)
    
    @property
    def request_message(self):
        return self.get_alternate(AlternateType.REQUEST)

    @request_message.setter
    def request_message(self, new_request):
        self.set_alternate(new_request, AlternateType.REQUEST)
    
    @property
    def approved_message(self):
        return self.get_alternate(AlternateType.APPROVED)
    
    @approved_message.setter
    def approved_message(self, new_approved):
        self.set_alternate(new_approved, AlternateType.APPROVED)
    
    @property
    def original_message(self):
        query = (where('message_cid') == self.channel_id) & \
                (where('message_mid') == self.message_id)
        
        result = self.handle.table(ALTERNATES_TABLE_NAME).get(query)
        return Message(self.handle, channel_id=result['original_cid'],
                                    message_id=result['original_mid'])

    async def fetch(self, bot):
        channel = await bot.fetch_channel(self.channel_id)
        return await channel.fetch_message(self.message_id)
    
    # ...

    def add_comment_hook(self, comment_message):
        channel_id = 0
        message_id = 0

        if isinstance(comment_message, discord.Message):
            channel_id = comment_message.channel.id
            message_id = comment_message.id
        
        else: # This class.
            channel_id = comment_message.channel_id
            message_id = comment_message.message_id
        
        logger.debug('Adding %s/%s as comment hook for %s/%s',
            channel_id, message_id, self.channel_id, self.message_id)

        query = self.base_query                                  & \
            (where('altype')      == int(AlternateType.COMMENT)) & \
            (where('message_cid') == channel_id)                 & \
            (where('message_mid') == message_id)
        
        self.handle.table(ALTERNATES_TABLE_NAME).upsert({
            'original_cid': self.channel_id,
            'original_mid': self.message_id,
            'altype':       int(AlternateType.COMMENT),
            'message_cid':  channel_id,
            'message_mid':  message_id
        }, query)
    
    @property
    def is_comment_hook(self) -> bool:
        """Checks if this message is a registered comment hook of another
        message. A comment hook is a message that, when replied to, adds a
        comment onto the original message."""
        query = (where('message_cid') == self.channel_id) & \
                (where('message_mid') == self.message_id) & \
                (where('altype')      == int(AlternateType.COMMENT))

        return self.handle.table(ALTERNATES_TABLE_NAME).get(query) is not None

    # ...

    def add_comment(self, user, content):
        logger.debug('User %s commented on message %s/%s: %s', user.id,
            self.channel_id, self.message_id, content)
        
        self.handle.table(COMMENTS_TABLE_NAME).insert({
            'original_cid': self.channel_id,
            'original_mid': self.message_id,
            'author': {
                'id': user.id,
                'name': user.name,
                'discriminator': user.discriminator
            },
            'content':      content
        })
    
    # ...

    @property
    def comments(self) -> Generator[dict, None, None]:
        results = self.handle.table(COMMENTS_TABLE_NAME).search(self.base_query)
        for document in results:
            # Yields elements that look like:
            # {
            #     'author': {
            #         'id': 0,
            #         'name': '',
            #         'discriminator': 0
            #     },
            #     'content': ''
            # }

            yield {
                'author': document.get('author'),
                'content': document.get('content')
            }

    # ...

    async def add_to_database(self, bot, anonymize=False):
        logger.debug('Adding %s/%s to database',
            self.channel_id, self.message_id)

        # Fetch the actual message.
        message = await self.fetch(bot)

        doc = {
            'original_cid': self.channel_id,
            'original_mid': self.message_id,

            # ...
            'author_hash':  user_to_hash(message.author),
            'added_at':     datetime.utcnow().isoformat(),
            'content':      message.content,

            # ...
            'channel': {
                'name': message.channel.name,
                'id':   message.channel.id
            },
            'guild': {
                'name': message.guild.name,
                'id':   message.guild.id
            }
        }

        # Add info about author.
        if not anonymize:
            doc['author'] = {
                'name':          message.author.name,
                'discriminator': message.author.discriminator,
                'id':            message.author.id
            }
        
        self.handle.table(MESSAGES_TABLE_NAME).upsert(doc, self.base_query)
    
    def add_metadata(self, metadata):
        result = self.get_metadata()
        result.update(metadata)
        self.set_metadata(result)

    def set_metadata(self, metadata):
        logger.debug('Setting metadata of %s/%s to %s',
            self.channel_id, self.message_id, metadata)

        self.handle.table(MESSAGES_TABLE_NAME).upsert({
            'original_cid': self.channel_id,
            'original_mid': self.message_id,
            'metadata':     metadata
        }, self.base_query)
    
    def get_metadata(self) -> dict:
        result = self.handle.table(MESSAGES_TABLE_NAME).get(self.base_query)
        return {} if result is None else result.get('metadata', {})

class Channel(LiveDocument):
    def __init__(self, handle, channel=None, id=0):
        self.handle = handle
        self.id = id

        if channel is not None:
            self.id = channel.id
    
    @property
    def base_query(self) -> Query:
        return where('channel_id') == self.id
    
    async def fetch(self, bot):
        return await bot.fetch_channel(self.id)

    @property
    def group(self) -> Optional[str]:
        document = self.handle.table(BRIDGES_TABLE_NAME).get(self.base_query)
        return None if document is None else document.get('group', None)
    
    @group.setter
    def group(self, value):
        logger.debug('Group for %s set to %s', self.id, value)

        self.handle.table(BRIDGES_TABLE_NAME).upsert({
            'channel_id': self.id,
            'group': value
        }, self.base_query)
    
    @group.deleter
    def group(self):
        logger.debug('Group for %s removed', self.id)

        query = where('channel_id') == self.id
        self.handle.table(BRIDGES_TABLE_NAME).remove(query)
    
    def get_channels_in_group(self, group) -> Generator['Channel', None, None]:
        query = where('group') == group
        results = self.handle.table(BRIDGES_TABLE_NAME).search(query)

        for document in results:
            yield Channel(self.handle, id=document['channel_id'])

class Guild(LiveDocument):
    def __init__(self, handle, guild=None, id=0):
        self.handle = handle
        self.id = id

        if guild is not None:
            self.id = guild.id

    @property
    def base_query(self):
        return where('guild_id') == self.id

    def set_channel(self, channel, is_pending):
        """Sets this guild's pending or approved channel.

        :param channel: The new channel.
        :type channel: Union[discord.abc.GuildChannel, Channel]
        :param is_pending: If this is pending or approved.
        :type is_pending: bool
        """
        logger.debug('%s channel for guild %s set to %s',
            'Pending' if is_pending else 'Approved', self.id, channel.id)

        self.handle.table(CHANNELS_TABLE_NAME).upsert({
            'guild_id':   self.id,
            'is_pending': is_pending,
            'channel_id': channel.id
        }, self.base_query & (where('is_pending') == is_pending))
    
    def get_channel(self, is_pending):
        """Gets this channel's pending or approved channel.

        :param is_pending: If we're looking for pending or approved.
        :type is_pending: bool
        :return: The channel document or `None` if not found.
        :rtype: Optional[Channel]
        """
        query = self.base_query & (where('is_pending') == is_pending)
        result = self.handle.table(CHANNELS_TABLE_NAME).get(query)
        return None if result is None else \
            Channel(self.handle, id=result['channel_id'])

    # ...

    @property
    def pending_channel(self):
        return self.get_channel(is_pending=True)
    
    @pending_channel.setter
    def pending_channel(self, new_channel):
        self.set_channel(new_channel, is_pending=True)

    @property
    def approved_channel(self):
        return self.get_channel(is_pending=False)
    
    @approved_channel.setter
    def approved_channel(self, new_channel):
        self.set_channel(new_channel, is_pending=False)

class User(LiveDocument):
    def __init__(self, handle, user=None, id=0):
        self.handle = handle
        self.id = id

        if user is not None:
            self.id = user.id
    
    @property
    def base_query(self) -> Query:
        # We will be accessing by `doc_id`, so we don't need this.
        raise NotImplementedError()

    @property
    def have_met(self) -> bool:
        result = self.handle.table(USERS_TABLE_NAME).get(doc_id=self.id)
        return False if result is None else result.get('have_met', False)
    
    @have_met.setter
    def have_met(self, new_met):
        logger.debug('Setting `have_met` for %s to %s', self.id, new_met)

        self.handle.table(USERS_TABLE_NAME).upsert(Document({
            'have_met': new_met
        }, doc_id=self.id))
    
    @property
    def is_admin(self) -> bool:
        result = self.handle.table(USERS_TABLE_NAME).get(doc_id=self.id)
        return False if result is None else result.get('is_admin', False)
    
    @is_admin.setter
    def is_admin(self, new_status):
        logger.debug('Setting `is_admin` for %s to %s', self.id, new_status)

        self.handle.table(USERS_TABLE_NAME).upsert(Document({
            'is_admin': new_status
        }, doc_id=self.id))

class Database:
    def __init__(self, filename):
        self.handle = TinyDB(filename, indent=4)

        logger.info('Opening %s as database', filename)
    
    def message(self, *args, **kwargs) -> Message:
        """Gets the live document referring to a message from the database.

        Examples:

            `db.message(ctx.origin_message).status`

            `await db.message(ctx.origin_message).original.fetch(bot)`

        :return: A live document referring to a specific message.
        :rtype: Message
        """
        return Message(self.handle, *args, **kwargs)
    
    def guild(self, *args, **kwargs) -> Guild:
        """Gets the live document referring to a guild from the database.

        Examples:

            `db.guild(ctx.guild).pending_channel`

            `db.guild(ctx.guild).approved_channel

        :return: A live document referring to a specific guild.
        :rtype: Guild
        """
        return Guild(self.handle, *args, **kwargs)
    
    def user(self, *args, **kwargs) -> User:
        """Gets the live document referring to a user from the database.
        
        Example:
            
            `db.user(ctx.author).have_met`
            
        :return: A live document referring to a specific user.
        :rtype: User
        """
        return User(self.handle, *args, **kwargs)
    
    def channel(self, *args, **kwargs) -> Channel:
        return Channel(self.handle, *args, **kwargs)
    
# Accessible in other modules.
db = Database(DATABASE_FNAME)

def is_admin(ctx) -> bool:
    """Checks whether or not the given context is from an admin.

    :param ctx: Any command context.
    :type ctx: commands.Context
    :return: Whether or not `ctx.author` is an admin.
    :rtype: bool
    """
    return db.user(ctx.author).is_admin
