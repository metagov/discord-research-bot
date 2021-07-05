from discord.ext import commands
from discord_components import DiscordComponents

import core

bot = commands.Bot(command_prefix='.')

@bot.event
async def on_ready():
    DiscordComponents(bot)
    
    print(f'Logged in as {bot.user.name} ({bot.user.id}) on {", ".join([x.name for x in bot.guilds])}')

    for ext in core.extensions:
        bot.load_extension(ext)

bot.run(
    open('token.txt', 'r').read(),
    bot = True,
    reconnect = True
)

