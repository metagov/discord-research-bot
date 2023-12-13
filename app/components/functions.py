import discord
from discord.ui import View

def construct_view(_id, items):
    view = View(timeout=None)
    for Item in items:
        view.add_item(Item(_id))
    
    return view

def message_to_embed(message):
    embed = discord.Embed(
        description=message.content,
        timestamp=message.edited_at or message.created_at
    )

    embed.set_author(
        name=message.author_name,
        icon_url=message.author_avatar_url,
        url=message.jump_url
    )

    embed.set_footer(text=f"{message.guild_name} - #{message.channel_name}")

    return embed