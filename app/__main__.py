from email.generator import Generator
from mongoengine.connection import connect
from discord_slash import SlashCommand
from discord.ext import commands
import discord
import logging
import cogs

bot = commands.Bot(command_prefix='.', help_command=None)
SlashCommand(bot, sync_commands=True)


def init_logging():
    # Configure all handlers.
    logging.basicConfig(
        format='[%(asctime)s] (%(levelname)s) %(name)s - %(message)s',
        level=logging.DEBUG,
    )

    # Silence the noisy ones.
    noisy_loggers = ['asyncio', 'discord', 'discord_slash', 'urllib3']
    for name in noisy_loggers:
        logging.getLogger(name).setLevel(logging.ERROR)


def get_extensions() -> Generator:
    for name in dir(cogs):
        if not name.startswith('_'):
            yield f'cogs.{name}'


@bot.event
async def on_ready():
    logging.info('Logged in as %s', bot.user)

# Initialize logging and load extensions.
init_logging()
for ext in get_extensions():
    logging.info('Loaded %s', ext)
    bot.load_extension(ext)

# Connect to the database and run the bot.
connect('development')
bot.run('don\'t leak the token!', reconnect=True)
