from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import (
    create_actionrow,
    create_button,
    create_select,
    create_select_option,
)

import hashlib
import logging
import discord
import sys
import os


logger = logging.getLogger(__name__)


def get_token(name) -> str:
    if name not in os.environ:
        logger.critical('%s is not set, cannot continue!', name)
        sys.exit(1)
    return os.environ[name]

def check_observatory_set(telescope):
    if not telescope.settings.observatory:
        logger.critical('Observatory guild id is not set, cannot continue!')
        quit(1)

def user_to_hash(user) -> str:
    """Convert user or integer to hexadecimal digest.

    :type user:         Union[discord.User, User, int]
    :raises ValueError: An invalid type was given.
    :rtype:             str
    """

    if hasattr(user, 'id'):
        user = user.id

    # You can just pass in an ``int`` directly.
    if not isinstance(user, int):
        raise ValueError('Expected int, got %s instead' % type(user).__name__)

    # Turn integer into hash of the same length.
    data = f'guac{user}amole'.encode('utf-8')
    shaker = hashlib.shake_128()
    shaker.update(data)
    return shaker.hexdigest(9)


def user_to_color(user) -> discord.Color:
    """Convert user or string to color.

    :type user:         Optional[Union[discord.User, User, str]]
    :raises ValueError: An invalid type was given.
    :rtype:             discord.Color
    """

    if not user:
        return discord.Color.blue()

    if hasattr(user, 'discriminator'):
        user = user.discriminator

    # You can just pass in a ``str`` directly.
    if not isinstance(user, str):
        raise ValueError('Expected str, got %s instead' % type(user).__name__)

    try:
        # Try to convert discriminator to integer.
        return int(user) // 9999 * 0xffffff
    except:
        return discord.Color.blue()


def message_to_embed(message, anonymize: bool = False) -> discord.Embed:
    """Convert a message to an embedded.

    :type message:      discord.Message
    :type anonymize:    bool
    :param anonymize:   Whether or not to anonymize the author of the message.
    :rtype:             discord.Embed
    """

    embed = discord.Embed(
        description=message.content,
        timestamp=message.edited_at or message.created_at,
        color=user_to_color(message.author),
    )

    if not anonymize:
        embed.set_author(
            name='{0.name}#{0.discriminator}'.format(message.author),
            icon_url=message.author.avatar_url,
            url=message.jump_url,
        )
    else:
        embed.set_author(
            name=user_to_hash(message.author),
            icon_url='https://i.imgur.com/qbkZFWO.png',

            # TODO: Should still link?
            url=message.jump_url,
        )

    # Show originating guild and channel.
    if message.guild:
        text = '{0.guild.name} - #{0.channel.name}'.format(message)
        embed.set_footer(text=text)

    return embed


def create_pending_arow(disabled: bool = False) -> dict:
    return create_actionrow(
        create_button(
            style=ButtonStyle.primary,
            label='Request',
            custom_id='request',
            disabled=disabled,
        ),
    )


def create_request_arow(disabled: bool = False) -> dict:
    return create_actionrow(
        create_button(
            style=ButtonStyle.green,
            label='Yes',
            custom_id='yes',
            disabled=disabled
        ),
        create_button(
            style=ButtonStyle.gray,
            label='Yes, anonymously',
            custom_id='anonymous',
            disabled=disabled
        ),
        create_button(
            style=ButtonStyle.red,
            label='No',
            custom_id='no',
            disabled=disabled
        ),
        # create_button(
        #     style=ButtonStyle.URL,
        #     label='Join our server',
        #     url='https://discord.com/'
        # ),
    )


def create_delete_arow(disabled: bool = False) -> dict:
    return create_actionrow(
        create_button(
            style=ButtonStyle.red,
            label="Remove",
            custom_id="delete",
            disabled=disabled,
        ),
    )
