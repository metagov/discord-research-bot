import discord
from discord.ext import commands
from cogs import Admin, Curation
from components import *
from settings import Settings

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
        guild = discord.Object(id=474736509472473088)

        self.add_dynamic_items(
            RequestPendingButton,
            DisabledRequestPendingButton,
            CancelPendingButton,
            YesConsentButton,
            AnonymousConsentButton,
            NoConsentButton
        )

        cogs = [Admin, Curation]
        for Cog in cogs:
            await self.add_cog(Cog(self), guild=guild)

        await self.tree.sync(guild=guild)
        print(f"Logged in as {self.user}")


bot = TelescopeBot()