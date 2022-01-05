from core.extension import Extension
from discord.ext import commands
from discord_slash import cog_ext
from models.special import Special, SpecialType
from models.guild import Guild

class Admin(Extension):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name='setup',
        description='Initializes Telescope and enables text channel bridge'
    )
    async def setup(self, ctx):
        observatory = self.bot.get_guild(self.bot.settings.observatory)

        # retrieving guild document
        guild = Guild.record(ctx.guild)
        if Special.objects(guild=guild).first():
            await ctx.reply("This server has already been setup.")
            return

        if ctx.guild == observatory:
            await ctx.reply("Setup can only be run in Satellite Servers, not the Observatory.")
            return

        # creates remote observatory channels
        category    = await observatory.create_category(ctx.guild.name)
        ch_bridge   = await observatory.create_text_channel("Bridge", category=category)
        ch_pending  = await observatory.create_text_channel("Pending Messages", category=category)
        ch_approved = await observatory.create_text_channel("Approved Messages", category=category)

        # sets bridge, pending, and fulfilled channels
        Special.set(ctx.guild, SpecialType.BRIDGE, ch_bridge)
        Special.set(ctx.guild, SpecialType.PENDING, ch_pending)
        Special.set(ctx.guild, SpecialType.FULFILLED, ch_approved)

        # creates bridge between setup channel and observatory channel
        # bridge group is the guild id (guaranteed to be unique)
        bridge_cog = self.bot.get_cog("Bridge")
        bridge_cog.set_channel_group(ctx.channel, str(ctx.guild.id))
        bridge_cog.set_channel_group(ch_bridge,   str(ctx.guild.id))

        await ctx.reply("Done!")


def setup(bot):
    cog = Admin(bot)
    bot.add_cog(cog)