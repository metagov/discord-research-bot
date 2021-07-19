from discord.ext import commands
from discord.ext.commands.core import command
from discord_slash import SlashCommand
from config import config

extensions = [
    'cogs.owner',
    'cogs.curator',
    'cogs.bridge'
]

bot = commands.Bot(command_prefix='.')
for ext in extensions:
    bot.load_extension(ext)
slash = SlashCommand(bot, sync_commands=True)

bot.run(config['token'], reconnect=True)
