from discord_slash.utils.manage_components import *
from discord_slash.model import ButtonStyle
from discord.ext import commands
from hashlib import shake_128
from constants import *
import logging
import discord
import sys
import os

logger = logging.getLogger(__name__)

# Using variables to avoid bugs from spelling mistakes.
REQUEST_PERMISSION_CUSTOM_ID = 'request_permission'
REQUEST_WITH_COMMENT_CUSTOM_ID = 'request_with_comment'
YES_CUSTOM_ID = 'yes'
YES_ANONYMOUSLY_CUSTOM_ID = 'yes_anonymously'
NO_CUSTOM_ID = 'no'

def init_logging() -> None:
    logging.basicConfig(level=logging.DEBUG)

    # Quieten loggers which would otherwise be very noisy.
    for logger_name in ['asyncio', 'discord', 'discord_slash']:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

def get_token():
    # Gets token from environment variables.
    if TOKEN_ENV_NAME not in os.environ:
        logger.error('%s environment variable not set', TOKEN_ENV_NAME)
        sys.exit(1)
    return os.environ[TOKEN_ENV_NAME]

def get_prefix(bot, message):
    # Allows per-guild command prefixes.
    return commands.when_mentioned_or(COMMAND_PREFIX)(bot, message)

def get_emoji(bot, message) -> str:
    """Gets the emoji for a given message that is required to curate it.

    :param bot: An instance of the bot.
    :type bot: commands.Bot
    :param message: Any message.
    :type message: discord.Message
    :return: An emoji.
    :rtype: str
    """
    return '🔭'

def user_to_hash(user_id) -> str:
    """Gets the pseudo-unique identifier for a given user.

    :param user: Any user.
    :type user: discord.User
    :return: An identifier that is 18 characters long.
    :rtype: str
    """
    data = f'guac{user_id}amole'.encode('utf-8')

    shaker = shake_128()
    shaker.update(data)
    return shaker.hexdigest(9)

def user_to_color(user) -> int:
    """Gets the color for a given user.

    Example:

        `discord.Embed(color=user_to_color(ctx.author))`

    :param user: Any user.
    :type user: discord.User
    :return: Any color.
    :rtype: int
    """
    return int(int(user.discriminator) / 9999 * 0xffffff)

def message_to_embed(message, anonymize=False) -> discord.Embed:
    """Turns a message into a embed as if it is being quoted.

    :param message: Any message.
    :type message: discord.Message
    :param anonymize: Whether to anonymize the author, defaults to False.
    :type anonymize: bool
    :return: An embed.
    :rtype: discord.Embed
    """
    embed = discord.Embed(
        description=message.content,
        timestamp=message.edited_at or message.created_at,
        color=user_to_color(message.author)
    )

    if not anonymize:
        embed.set_author(
            name='{0.name}#{0.discriminator}'.format(message.author),
            url=message.jump_url,
            icon_url=message.author.avatar_url
        )

    else: # Anonymize.
        embed.set_author(
            name=user_to_hash(message.author),
            url=message.jump_url, # TODO: Should still link?
            icon_url='https://i.imgur.com/qbkZFWO.png'
        )
    
    # Footer will look like 'My Server - #general'.
    footer_text = '{0.guild.name} - #{0.channel.name}'.format(message)
    embed.set_footer(text=footer_text)

    return embed

def make_pending_action_row(disabled=False) -> dict:
    """Makes the action row for a pending message. The action row contains
    the buttons i.e., 'Request permission'.

    Example:

        `await channel.send(components=[make_pending_action_row()])`

    :param disabled: Whether to disable the buttons, defaults to False.
    :type disabled: bool
    :return: Something to pass directly to the library.
    :rtype: dict
    """
    return create_actionrow(
        create_button(
            style=ButtonStyle.blue,
            label='Request permission',
            custom_id=REQUEST_PERMISSION_CUSTOM_ID,
            disabled=disabled
        )
    )

async def disable_pending_action_row(pending):
    """Disables the action row for a pending message. Assumes that the
    components on `pending` were created by `make_pending_action_row`.

    :param pending: Any pending message.
    :type pending: discord.Message
    """
    row = make_pending_action_row(disabled=True)
    await pending.edit(components=[row])

def make_request_action_row(disabled=False) -> dict:
    """Makes the action row for the request message. The action row contains
    the buttons i.e., 'Yes' or 'Yes, anonymously'.

    Example:
        
        `await channel.send(components=[make_request_action_row()])`

    :param disabled: Whether to disable the buttons, defaults to False.
    :type disabled: bool
    :return: Something to pass directly to the library.
    :rtype: dict
    """
    return create_actionrow(
        create_button(
            style=ButtonStyle.green,
            label='Yes',
            custom_id=YES_CUSTOM_ID,
            disabled=disabled
        ),
        create_button(
            style=ButtonStyle.gray,
            label='Yes, anonymously',
            custom_id=YES_ANONYMOUSLY_CUSTOM_ID,
            disabled=disabled
        ),
        create_button(
            style=ButtonStyle.red,
            label='No',
            custom_id=NO_CUSTOM_ID,
            disabled=disabled
        ),
        create_button(
            style=ButtonStyle.URL,
            label='Join our server',
            url='https://discord.com/'
        )
    )

async def disable_request_action_row(request):
    """Disables the action row for a request message. Assumes that the
    components on `request` were made from `make_request_action_row`.

    :param request: Any request message.
    :type request: discord.Message
    """
    row = make_request_action_row(disabled=True)
    await request.edit(components=[row])

def add_consent_message(embed) -> discord.Embed:
    """Adds the consent message onto an embed as a field.

    :param embed: Any embed.
    :type embed: discord.Embed
    :return: The same embed.
    :rtype: discord.Embed
    """
    embed.add_field(
        name='Consent Message',
        value='''We're asking for permission to quote you in our research.
    • Yes, you may quote my post and attribute it to my Discord Handle.
    • You may quote my post anonymously. Do not use my Discord Handle or any other identifying information.
    • No, you may not quote my post in your research.
Thanks for helping us understand the future of governance!''',
        inline=False
    )

    return embed

async def send_introduction(user, guild):
    """Sends an introductory message to `user` that explains who we are so they
    don't immediately block us.

    :param user: The person that will receive the message.
    :type user: discord.User
    :param guild: The name of this guild is used in the message.
    :type guild: discord.Guild
    """
    link = ('https://www.rmit.edu.au/research/centres-collaborations/derc/'
        'cooperation-through-code/crypto-governance-observatory')

    embed = discord.Embed(
        title='👋 Hello from the Crypto-Governance Observatory!',
        description='We\'re a team of researchers interested in the power of'
            f' community governance. Find out more about us [here]({link}).'
            f' You might have noticed our channel in the **{guild.name}**'
            ' server. Your post was highlighted by another user who thought it'
            ' was interesting.'
    )

    logger.debug('Sending introduction to %s from %s', user.id, guild.id)

    await user.send(embed=embed)

def add_introduction_field(embed, guild):
    link = ('https://www.rmit.edu.au/research/centres-collaborations/derc/'
        'cooperation-through-code/crypto-governance-observatory')
    
    embed.add_field(
        name='👋 Hello from the Crypto-Governance Observatory!',
        value='We\'re a team of researchers interested in the power of'
            f' community governance. Find out more about us [here]({link}).'
            f' You might have noticed our channel in the **{guild.name}**'
            ' server. Your post was highlighted by another user who thought it'
            ' was interesting.',
        inline=False
    )

async def send_thanks(user, responded_yes, guild):
    """Sends a thank you note to a `user` with different content based on
    whether or not `user` granted or denied permission to use one of their
    messages. Note that the user wishing to remain anonymous still counts as
    responding yes.

    :param user: Any user that was just requested for permission.
    :type user: discord.User
    :param responded_yes: Whether or not user responded yes, defaults to True.
    :type responded_yes: bool
    :param guild: The guild which the curated message is from.
    :type guild: discord.Guild
    """
    text_yes = ('Thanks! Your post will help us to understand the future of'
        ' governance. If you want to get more involved in The Observatory,'
        ' we have some awesome NFTs available for participants. Just join'
        f' the "Cryto-Governance Channel" in the **{guild.name}** server.') 
    
    text_no = ('No problem. Thanks anyway and please head over to our channel'
        ' if you\'d like to learn more about what we do.')
    
    logger.debug('Thanking %s for %s from %s', user.id,
        'responding yes' if responded_yes else 'responding no', guild.id)

    await user.send(content=text_yes if responded_yes else text_no)

async def notify_observer(observer, subject):
    """Notifies `observer` that `subject` just gave consent to use their post
    for research.

    :param observer: Any observer.
    :type observer: discord.User
    :param subject: Any subject.
    :type subject: discord.User
    """
    text = (f'Good news! **{subject.name}#{subject.discriminator}** has given'
        ' their consent for you to use their post for research. Their post has'
        ' been added to our repository.')

    logger.debug('Notifying observer %s about %s', observer.id, subject.id)

    await observer.send(content=text)

def add_commentable_message(embed):
    embed.add_field(
        name='💬 Commentable',
        value='Reply to this message to add a comment.',
        inline=False
    )
