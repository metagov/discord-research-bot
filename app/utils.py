import discord

def user_to_color(user: discord.User):
    '''Maps discord discriminator to a hex color value.'''
    return int(int(user.discriminator) / 9999 * 0xffffff)
