from discord.colour import Color
from discord.embeds import Embed
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option
from datetime import datetime
from config import config
import os

class OwnerCog(commands.Cog):
    '''Provides useful owner-only commands for live bot management.'''

    def __init__(self, bot):
        self.bot = bot
    
    @commands.group()
    @commands.is_owner()
    async def owner(self, ctx):
        # is_owner is propagated to all commands within group.
        pass

    @owner.command()
    async def reload(self, ctx):
        try:
            self.bot.reload_extensions()
            await ctx.message.add_reaction('👍')
        except Exception as e:
            await ctx.send(f'An error has occurred. `{type(e).__name__} - {e}`.'
                ' A restart is most likely required.')

    @owner.command()
    async def update(self, ctx):
        stream = os.popen('git pull')
        output = stream.read()
        self.bot.reload_extensions()
        await ctx.send(f'```{output}```')

    @cog_ext.cog_slash(
        name='bugreport',
        description='Report a bug to the development team.',
        guild_ids=config['guild_ids'],
        options=[
            create_option(
                name='description',
                description='Please describe what happened! Your handle, guild,'
                    ' and channel will be recorded.',
                option_type=3,
                required=True
            )
        ]
    )
    async def _bugreport(self, ctx: SlashContext, description):
        # Build an embed that describes the bug.
        embed = Embed(
            description=description,
            color=Color.red(),
            timestamp=datetime.utcnow()
        )

        # Show reporter's profile picture.
        embed.set_author(
            name=f'{ctx.author.display_name}#{ctx.author.discriminator}',
            url=f'https://discordapp.com/users/{ctx.author_id}',
            icon_url=ctx.author.avatar_url
        )

        # Show guild.
        embed.add_field(
            name='Guild',
            value=f'{ctx.guild.name} ({ctx.guild_id})',
            inline=False
        )

        # Show channel.
        embed.add_field(
            name='Channel',
            value=f'{ctx.channel.name} ({ctx.channel_id})',
            inline=False
        )

        if 'report_id' not in config:
            # Tell owner why it was sent to him.
            embed.set_footer(
                text='This bug report has been sent to you because \'report_id'
                    '\' is not set in the config.'
            )

            # Send to bot owner.
            owner = await self.bot.get_or_fetch_user(self.bot.owner_id)
            await owner.send(embed=embed)
        else:
            # Send to special channel.
            channel = await self.bot.get_or_fetch_channel(ctx.channel_id)
            await channel.send(embed=embed)
        
        await ctx.send('Thanks! This information will help make the bot even '
            'better. 😄')

def setup(bot):
    bot.add_cog(OwnerCog(bot))