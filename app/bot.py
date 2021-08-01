from discord.activity import Activity, Game
from discord_slash.client import SlashCommand
from config import config, DEFAULT_TOKEN
from discord.ext import commands
from pathlib import Path
import logging
import sys

extensions = [
    'cogs.admin',
    'cogs.curator',
    'cogs.owner',
    'cogs.bridge'
]

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=config['command_prefix'])
        SlashCommand(self, sync_commands=True)
        self.load_extensions()

    async def on_ready(self):
        """Called when library is done preparing data from discord."""
        print(f'Logged in successfully as {self.user}')
        print(f'Command prefix is \'{self.command_prefix}\'')
        print(f'Extensions are {extensions}')

        # Show command prefix in status.
        await self.change_presence(
            activity=Game(name=f'use {self.command_prefix} or /')
        )

    def load_extensions(self):
        """Loads all default extensions."""
        for ext in extensions: 
            print(f'Loaded {ext}')
            self.load_extension(ext)
    
    def unload_extensions(self):
        """Unloads all default extensions."""
        for ext in extensions:
            print(f'Unloaded {ext}')
            self.unload_extension(ext)
    
    def reload_extensions(self):
        """Reloads all default extensions."""
        self.unload_extensions()
        self.load_extensions()

    def run(self):
        """Runs bot with configured token."""
        if config['token'] == DEFAULT_TOKEN:
            logging.error('Hey there! It doesn\'t look like the token is'
                ' setup correctly in the config. Please change it and re-launch'
                ' the program.')
            sys.exit(1)
        super().run(config['token'], reconnect=True)
    
