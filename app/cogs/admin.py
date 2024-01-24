import discord
from discord import app_commands
from discord.ext import commands
from models import SatelliteModel

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="setup",
        description="initialize a new satellite server"
    )
    async def setup_satellite(self, interaction):
        await interaction.response.defer()

        observatory = self.bot.get_guild(self.bot.settings.observatory)

        category = await observatory.create_category(interaction.guild.name)
        pending =  await observatory.create_text_channel("Pending Messages", category=category)
        approved = await observatory.create_text_channel("Approved Messages", category=category)

        satellite = SatelliteModel(
            id                  = interaction.guild.id,
            name                = interaction.guild.name,
            pending_channel_id  = pending.id,
            approved_channel_id = approved.id
        )
        satellite.save()

        await interaction.followup.send(content="Setup complete!")

    @commands.command()
    async def sync(self, ctx):
        if ctx.author.id == 151856436710866944:
            observatory = self.bot.get_guild(self.bot.settings.observatory)
            await self.bot.tree.sync(guild=observatory)
            await ctx.send("Synced successfully!")
