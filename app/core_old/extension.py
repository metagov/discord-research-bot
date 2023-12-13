from discord.ext import commands


class Extension(commands.Cog):
    def __init__(self, bot, **kwargs) -> None:
        bot.logger.info('Extension "%s" loaded!', self.__class__.__name__)
        self.bot = bot

    def cog_unload(self) -> None:
        self.bot.logger.info('"%s" unloaded!', self.__class__.__name__)
