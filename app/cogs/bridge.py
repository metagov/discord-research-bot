from helpers import message_to_embed
from typing import Generator, Optional
from discord.channel import TextChannel
from discord.ext import commands
from database import is_admin, db
import discord

class BridgeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(is_admin)
    async def bridge(self, ctx, group: str=None, channel: TextChannel=None):
        """Sets a channel's group to `group`. If `group` is not provided, then
        the channel's group is cleared. Defaults to the channel where this
        command is being executed."""
        if channel is None:
            channel = ctx.channel

        if group is not None:
            db.channel(channel=channel).group = group
        else: # Delete group.
            del db.channel(channel=channel).group
        
        await ctx.message.add_reaction('👍')

    @commands.Cog.listener()
    async def on_message(self, message):
        group = self.get_group(message.channel)
        if group is not None and message.author != self.bot.user:
            await self.replicate_in_group(message, group)
    
    async def replicate_in_group(self, message, group):
        embed = message_to_embed(message)
        embed.set_footer(text=f'{group} | {embed.footer.text}')

        async for channel in self.get_channels_in_group(message.channel, group):
            if channel != message.channel:
                await channel.send(embed=embed)

    async def get_channels_in_group(self, channel, group):
        # TODO: Remove `channel` from parameter list.
        results = db.channel(channel=channel).get_channels_in_group(group)
        for channel_doc in results:
            yield await channel_doc.fetch(self.bot)
    
    def get_group(self, channel) -> Optional[str]:
        return db.channel(channel=channel).group

def setup(bot):
    cog = BridgeCog(bot)
    bot.add_cog(cog)
