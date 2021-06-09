from discord.ext import commands

extensions = [
    'cogs.owner'
]

bot = commands.Bot(command_prefix='.')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id}) on {", ".join([x.name for x in bot.guilds])}')

    for ext in extensions:
        bot.load_extension(ext)

bot.run(
    open('token.txt', 'r').read(),
    bot = True,
    reconnect = True
)