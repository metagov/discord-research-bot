from discord.ext import commands
from discord_slash import SlashCommand
from config import config

bot = commands.Bot(command_prefix='.')
SlashCommand(bot, sync_commands=True)

extensions = [
    'cogs.owner',
    'cogs.curator',
    'cogs.bridge'
]

for ext in extensions:
    bot.load_extension(ext)

bot.run(config['token'], reconnect=True)
