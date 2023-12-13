import discord
from discord.ext import commands
from discord import app_commands

class Curator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="test", description="test", guild=discord.Object(id=474736509472473088))
    async def test(interaction):
        await interaction.response.send_message("test")