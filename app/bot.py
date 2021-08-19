from helpers import get_prefix, get_token
from discord_slash import SlashCommand
from discord.ext import commands
from constants import EXTENSIONS
import logging

logger = logging.getLogger(__name__)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=get_prefix)
        SlashCommand(self, sync_commands=True)
        self.load_extensions()

    def load_extensions(self):
        for ext in EXTENSIONS:
            logger.info('Loading %s', ext)
            self.load_extension(ext)

    async def fetch_guild(self, guild_id):
        return self.get_guild(guild_id) or \
            await super().fetch_guild(guild_id)

    async def fetch_channel(self, channel_id):
        return self.get_channel(channel_id) or \
            await super().fetch_channel(channel_id)
    
    def run(self):
        super().run(get_token(), reconnect=True)
    
    async def on_ready(self):
        logger.info('Logged in as %s', self.user)
