from discord import guild
from discord.ext import commands
from discord.ext.commands import cog
from discord_slash import cog_ext
from constants import CENTRAL_HUB_ID
from database import *

from cogs.curator import CuratorCog

class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @cog_ext.cog_slash(
        name="setup",
        guild_ids=[474736509472473088, 870551183339696138, 870551292525809684,
                   872936378118324235]
    )
    async def setup(self, ctx):
        if not db.user(user=ctx.author).is_admin:
            return await ctx.send('Insufficient permissions!')

        observatory = self.bot.get_guild(CENTRAL_HUB_ID)
        
        if ctx.guild == observatory:
            await ctx.send("Setup can only be run in Satellite Servers.")
            return

        # creating category and channels in Observatory
        category = await observatory.create_category(ctx.guild.name)
        bridge   = await observatory.create_text_channel("Bridge", category=category)
        pending  = await observatory.create_text_channel("Pending Messages", category=category)
        approved = await observatory.create_text_channel("Approved Messages", category=category)

        # setting channel ids for curation process
        db.guild(ctx.guild).pending_channel = pending
        db.guild(ctx.guild).approved_channel = approved
        
        db.channel(channel=ctx.channel).group = ctx.guild.name
        db.channel(channel=bridge).group = ctx.guild.name
        
        await ctx.reply("Done!")

def setup(bot):
    cog = SetupCog(bot)
    bot.add_cog(cog)