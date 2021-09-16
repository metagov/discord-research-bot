from hashlib import shake_128
from discord.ext import commands
import discord


def id_to_hash(id) -> str:
    # Obfuscate an arbitrary integer by hashing it.
    data = f'guac{id}amole'.encode('utf-8')
    shaker = shake_128()
    shaker.update(data)
    return shaker.hexdigest(9)


def message_to_embed(message: discord.Message, anonymize: bool = False) -> discord.Embed:
    embed = discord.Embed(
        description=message.content,
        timestamp=message.edited_at or message.created_at,
        # TODO: Do custom discriminators cause this to raise an exception?
        # color=int(int(message.author.discriminator) / 9999 * 0xffffff),
    )

    if not anonymize:
        embed.set_author(
            name='{0.name}#{0.discriminator}'.format(message.author),
            icon_url=message.author.avatar_url,
            url=message.jump_url,
        )
    else:
        embed.set_author(
            name=id_to_hash(message.author.id),
            icon_url='https://i.imgur.com/qbkZFWO.png',
            # TODO: Should still link?
            # url=message.jump_url,
        )

    # Show originating guild and channel.
    if message.guild:
        text = '{0.guild.name} - #{0.channel.name}'.format(message)
        embed.set_footer(text=text)

    return embed
