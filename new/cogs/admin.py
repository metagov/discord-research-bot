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

        observatory = self.bot.get_guild(474736509472473088)

        category = await observatory.create_category(interaction.guild.name)
        pending =  await observatory.create_text_channel("Pending Messages", category=category)
        approved = await observatory.create_text_channel("Approved Messages", category=category)

        satellite = SatelliteModel(
            id = interaction.guild.id,
            pending_channel_id = pending.id,
            approved_channel_id = approved.id
        )
        satellite.save()

        await interaction.followup.send(content="Setup complete!")