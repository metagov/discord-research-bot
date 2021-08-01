from config import config
from hashlib import shake_128
import discord
import re

def user2color(user):
    """Maps a user's discriminator to a color value."""
    return int(int(user.discriminator) / 9999 * 0xffffff)

def message2embed(message) -> discord.Embed:
    """Converts a message to an embed(ded).
    
    Links the original message in the author url, and also uses a color
    which is based off of the original author's discriminator."""
    embed = discord.Embed(
        description=message.content,
        color=user2color(message.author),
        timestamp=message.edited_at or message.created_at
    )

    author = message.author
    embed.set_author(
        name=f'{author.display_name}#{author.discriminator}',
        url=message.jump_url, # Link the original message.
        icon_url=author.avatar_url
    )

    # Show where this message came from.
    embed.set_footer(text=f'{message.guild.name} - #{message.channel.name}')

    return embed

async def embed2message(bot, embed) -> discord.Message:
    """Assuming that the embed was created using `message2embed`, this function
    recovers the original message by parsing the author url."""
    pattern = '^.*/([0-9]+)/([0-9]+)/([0-9]+)$'
    results = re.search(pattern, embed.author.url)

    channel_id = results.group(2)
    message_id = results.group(3)

    channel = await bot.fetch_channel(channel_id)
    return await channel.fetch_message(message_id)

def is_admin(ctx):
    """Returns whether or not this context is from a bot admin.
    
    Bot admins are not to be confused with guild admins. A bot admin just gets
    special privileges related to the everyday configuration of the bot."""
    return ctx.author.id in config['admins']

def user_hash(user) -> str:
    """Hashes a user's id.
    
    If we hashed the username and discriminator, that would change every single
    time they changed their name and, well, discriminator."""
    data = str(user.id) + 'guacamole'
    data = data.encode('utf-8')
    shake = shake_128()
    shake.update(data)
    return shake.hexdigest(8)
