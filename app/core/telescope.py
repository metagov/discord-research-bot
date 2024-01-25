import discord
from discord.ext import commands
from cogs import Admin, Curation
from components import *
from .settings import settings

class TelescopeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents
        )

        self.settings = settings

        if not self.settings.observatory:
            print("Missing observatory guild id in settings.json")
            quit()
    
    async def setup_hook(self):
        observatory = await self.fetch_guild(self.settings.observatory)

        self.add_dynamic_items(
            RequestPendingButton,
            DisabledRequestPendingButton,
            CancelPendingButton,
            YesConsentButton,
            AnonymousConsentButton,
            NoConsentButton,
            RemoveConsentButton,
            AddCommentButton
        )

        cogs = [Admin, Curation]
        for Cog in cogs:
            await self.add_cog(Cog(self), guild=observatory)

        print(f"Logged in as {self.user} in observatory {observatory}")

bot = TelescopeBot()