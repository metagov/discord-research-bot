from discord.ext import commands
from discord_slash import SlashCommand
from utils import PersistentJSON
import discord

extensions = [
    'cogs.owner',
    'cogs.curator',
    'cogs.bridge'
]

config_fn = 'config.json'

config = PersistentJSON(config_fn)

bot = commands.Bot(command_prefix='.')
slash = SlashCommand(bot, sync_commands=True)
for ext in extensions:
    bot.load_extension(ext)


@bot.event
async def on_ready():
    '''Called when the client is done preparing the data received from Discord.
    
    May be called many times when running.'''
    print(f'Logged in as {bot.user.name} ({bot.user.id}) on ' + \
            f'{", ".join([x.name for x in bot.guilds])}')

# Read the token from a file that will not be pushed to source control.
bot.run(
    open('token.txt', 'r').read(),
    bot=True,
    reconnect=True
)

