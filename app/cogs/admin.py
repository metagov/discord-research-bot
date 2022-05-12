from core.helpers import user_to_hash
from models.special import Special, SpecialType
from core.extension import Extension
from models.message import Message
from discord_slash import cog_ext
from discord.ext import commands
from models.guild import Guild
from models.user import User


class Admin(Extension):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name='setup',
        description='Initializes Telescope and enables text channel bridge',
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
        category = await observatory.create_category(ctx.guild.name)
        ch_bridge = await observatory.create_text_channel("Bridge", category=category)
        ch_pending = await observatory.create_text_channel("Pending Messages", category=category)
        ch_approved = await observatory.create_text_channel("Approved Messages", category=category)

        # sets bridge, pending, and fulfilled channels
        Special.set(ctx.guild, SpecialType.BRIDGE, ctx.channel)
        Special.set(ctx.guild, SpecialType.PENDING, ch_pending)
        Special.set(ctx.guild, SpecialType.FULFILLED, ch_approved)

        # creates bridge between setup channel and observatory channel
        # bridge group is the guild id (guaranteed to be unique)
        bridge_cog = self.bot.get_cog("Bridge")
        bridge_cog.set_channel_group(ctx.channel, str(ctx.guild.id))
        bridge_cog.set_channel_group(ch_bridge,   str(ctx.guild.id))

        await ctx.reply("Done!")

    @commands.command(name='smovebridgehere')
    @commands.is_owner()
    async def move_bridge_here(self, ctx):
        sat_guild = ctx.guild
        sat_channel = ctx.channel

        guild = Guild.objects(id=sat_guild.id).first()
        bridge = Special.objects(guild=guild, stype=SpecialType.BRIDGE).first()

        old_channel = await self.bot.fetch_channel(bridge.channel.id)
        bridge.delete()

        print(f"moving bridge {old_channel} ({old_channel.id}) -> {sat_channel} ({sat_channel.id})")

        Special.set(sat_guild, SpecialType.BRIDGE, sat_channel)
        
        bridge_cog = self.bot.get_cog("Bridge")
        bridge_cog.reset_channel_group(old_channel)
        bridge_cog.set_channel_group(sat_channel, str(sat_guild.id))

    @commands.command(name='smanualsetup')
    @commands.is_owner()
    async def manual_setup(self, ctx, pending_id, approved_id, bridge_id):
        sat_guild = ctx.guild
        sat_channel = ctx.channel
        print(pending_id, approved_id, bridge_id)
        pending = await self.bot.fetch_channel(int(pending_id))
        approved = await self.bot.fetch_channel(int(approved_id))
        bridge = await self.bot.fetch_channel(int(bridge_id))

        Special.set(sat_guild, SpecialType.BRIDGE, sat_channel)
        Special.set(sat_guild, SpecialType.PENDING, pending)
        Special.set(sat_guild, SpecialType.FULFILLED, approved)

        bridge_cog = self.bot.get_cog("Bridge")
        bridge_cog.set_channel_group(sat_channel, str(sat_guild.id))
        bridge_cog.set_channel_group(bridge, str(sat_guild.id))

        await ctx.message.add_reaction("👍")

    @cog_ext.cog_slash(
        name="optout",
        description="Remove all of your messages from The Observatory dataset.",
    )
    async def optout(self, ctx) -> None:
        author_hash = user_to_hash(ctx.author)
        at_cog = self.bot.get_cog("Air")
        for message_doc in Message.objects(author_hash=author_hash):
            self.bot.logger.warning("Queueing %s for deletion.", message_doc)
            at_cog.delete(message_doc)
        
        # Send a message after queueing all for deletion.
        await ctx.reply(self.bot.responses.on_opt_out_message)

def setup(bot):
    cog = Admin(bot)
    bot.add_cog(cog)
