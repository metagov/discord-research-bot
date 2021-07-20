from discord.ext import commands
from discord_slash import SlashCommand
from config import config
import discord

extensions = [
    'cogs.owner',
    'cogs.curator',
    'cogs.bridge'
]

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='.')
        SlashCommand(self, sync_commands=True)
        self.load_extensions()
    
    async def on_ready(self):
        # Refresh owner_id here.
        app = await self.application_info()
        self.owner_id = app.owner.id
        
        print('  Logged in as', self.user)
        print('  Discord.py version is', discord.__version__)

    def load_extensions(self):
        for ext in extensions:
            self.load_extension(ext)
        
    def unload_extensions(self):
        for ext in extensions:
            self.unload_extension(ext)

    def reload_extensions(self):
        for ext in extensions:
            self.unload_extension(ext)
            self.load_extension(ext)

    async def get_or_fetch_channel(self, _id):
        channel = self.get_channel(_id)
        if not channel:
            channel = await self.fetch_channel(_id)
        return channel
    
    async def get_or_fetch_guild(self, _id):
        guild = self.get_guild(_id)
        if not guild:
            guild = await self.fetch_guild(_id)
        return guild
    
    async def get_or_fetch_user(self, _id):
        user = self.get_user(_id)
        if not user:
            user = await self.fetch_user(_id)
        return user
    
    def run(self):
        super().run(config['token'], reconnect=True)

MyBot().run()
