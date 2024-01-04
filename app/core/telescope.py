import discord
from discord.ext import commands
from cogs import Admin, Curation
from components import *
from .settings import Settings

class TelescopeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents
        )

        self.settings = Settings()
    
    async def setup_hook(self):
        observatory = await self.fetch_guild(self.settings.observatory)

        self.add_dynamic_items(RequestPendingButton)
        self.add_dynamic_items(DisabledRequestPendingButton)
        self.add_dynamic_items(CancelPendingButton)
        self.add_dynamic_items(YesConsentButton)
        self.add_dynamic_items(AnonymousConsentButton)
        self.add_dynamic_items(NoConsentButton)

        cogs = [Admin, Curation]
        for Cog in cogs:
            await self.add_cog(Cog(self), guild=observatory)

        await self.tree.sync(guild=observatory)
        print(f"Logged in as {self.user} in observatory {observatory}")


bot = TelescopeBot()