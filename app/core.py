extensions = [
    'cogs.owner',
    'cogs.curator',
    'cogs.bridge'
]

# def filter_dms(msg):


# def convert_from_url(bot, url):
#     if not url.startswith('https://discord.com/channels/'):
#         return False

#     try:
#         parts = url.split('/')
#         guild_id = int(parts[4])
#         channel_id = int(parts[5])
#         msg_id = int(parts[6])
#     except (ValueError, IndexError):
#         return False
    
#     guild = bot.get_guild(guild_id)
#     if guild:
#         channel = 