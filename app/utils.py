import json
import discord

def user_to_color(user: discord.User):
    '''Maps discord discriminator to a hex color value.'''
    return int(int(user.discriminator) / 9999 * 0xffffff)

def message_to_embed(msg: discord.Message):
    '''Turns a message into an embed(ded).'''
    # Include time that message was edited or sent.
    embed = discord.Embed(
        description=msg.content,
        color=user_to_color(msg.author),
        timestamp=msg.edited_at or msg.created_at
    )

    author: discord.User = msg.author

    # Include author's avatar and name.
    embed.set_author(
        name=f"{author.display_name}#{author.discriminator}", 
        url=f"{msg.jump_url}",
        icon_url=author.avatar_url
    )

    # Put guild and channel name in the footer.
    # embed.set_footer(text=f'{msg.guild.name} - #{msg.channel.name}')

    # Link the original message in the footer.
    # embed.set_footer(text=')

    return embed
