from discord_slash import SlashCommand
from types import SimpleNamespace
from discord.ext import commands
from typing import Iterator
import logging
import pkgutil
import cogs


class Telescope(commands.Bot):
    def __init__(self, **kwargs) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or('.'),
            description='My objective is to observe and record!',
            help_command=None,
        )

        SlashCommand(self, sync_commands=True, sync_on_cog_reload=True)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.tokens = SimpleNamespace(
            # A place to keep all of our tokens.
            discord=kwargs.get('discord_token'),
            airtable=kwargs.get('airtable_token'),
        )

        # A place to keep all of our settings.
        self.settings = kwargs.pop('settings')

        # Automatically load all of our extensions.
        for _, name, _ in self.__iter_namespace(cogs):
            self.load_extension(name)

    @classmethod
    def __iter_namespace(cls, ns_pkg) -> Iterator:
        # https://packaging.python.org/guides/creating-and-discovering-plugins/
        return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")

    def run(self) -> None:
        super().run(self.tokens.discord, reconnect=True)

    async def on_ready(self) -> None:
        self.logger.info('Logged in as %s', self.user)
