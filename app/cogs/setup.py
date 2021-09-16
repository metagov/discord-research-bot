from discord.ext import commands
from discord import TextChannel
from models import Guild
import discord


class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def quickconfig(self, ctx: commands.Context, cpending: TextChannel,
                          cfulfilled: TextChannel, cbridge: TextChannel):
        # A quick-and-dirty command that configures a guild's channels.
        if not ctx.guild:
            return await ctx.send('This can only be run in a guild!')

        gdocument = Guild.get(ctx.guild.id)
        gdocument.pending_id = cpending.id
        gdocument.fulfilled_id = cfulfilled.id
        gdocument.bridge_id = cbridge.id
        gdocument.save()

        await ctx.send(
            f'**{ctx.guild.name}** is now configured like so.\n'
            f'```{cpending.name.ljust(16)} - The pending messages channel.\n'
            f'{cfulfilled.name.ljust(16)} - The fulfilled messages channel.\n'
            f'{cbridge.name.ljust(16)} - The bridge channel.\n```'
        )
    
    @quickconfig.error
    async def quickconfig_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.ChannelNotFound):
            return await ctx.send('I couldn\'t find that channel.')
        raise error


def setup(bot):
    cog = SetupCog(bot)
    bot.add_cog(cog)
