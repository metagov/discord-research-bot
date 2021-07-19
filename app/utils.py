import json
import discord

def user_to_color(user: discord.User):
    '''Maps discord discriminator to a hex color value.'''
    return int(int(user.discriminator) / 9999 * 0xffffff)

def message_to_embed(msg: discord.Message):
    '''Turns a message into an embed(ded).'''
    embed = discord.Embed(
        description=msg.content,
        color=user_to_color(msg.author),
        timestamp=msg.edited_at or msg.created_at
    )

    author: discord.User = msg.author

    embed.set_author(
        name=f"{author.display_name}#{author.discriminator}", 
        url=f"https://discord.com/users/{author.id}",
        icon_url=author.avatar_url
    )

    return embed
