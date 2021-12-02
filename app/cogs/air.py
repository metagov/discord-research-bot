from core.extension import Extension


class Air(Extension):
    ...


def setup(bot) -> None:
    cog = Air(bot)
    bot.add_cog(cog)
