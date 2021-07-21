import discord

def user_to_color(user: discord.User):
    # Maps discord discriminator to a hex color value.
    return int(int(user.discriminator) / 9999 * 0xffffff)

def message_to_embed(msg: discord.Message):
    # Turns a message into an embed.
    embed = discord.Embed(
        description=msg.content,
        color=user_to_color(msg.author),
        timestamp=msg.edited_at or msg.created_at
    )

    # Link original message.
    embed.set_author(
        name=f"{msg.author.display_name}#{msg.author.discriminator}", 
        url=msg.jump_url,
        icon_url=msg.author.avatar_url
    )

    return embed
