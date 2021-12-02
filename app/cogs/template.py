from core.extension import Extension


class Template(Extension):
    ...


def setup(bot) -> None:
    cog = Template(bot)
    bot.add_cog(cog)
