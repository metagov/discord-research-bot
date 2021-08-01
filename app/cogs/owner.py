from datetime import datetime
from discord.embeds import Embed
from discord_slash import cog_ext
from discord.ext import commands
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option
from config import config, parse_config
from utils import user2color

# For slash commands.
supp_config = parse_config(config)

class OwnerCog(commands.Cog):
    """Functions available only to the owner of the bot."""

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.is_owner()
    async def bootstrap(self, ctx: commands.Context):
        """Adds the owner to the admin list."""
        await ctx.invoke(self.bot.get_command('admin'), ctx.author)
    
    @commands.command()
    @commands.is_owner()
    async def extensions(self, ctx: commands.Context):
        """Displays the loaded extensions."""
        texts = ['The currently loaded extensions are:\n']
        for ext in self.bot.extensions:
            texts.append(f' • {ext}\n')
        await ctx.reply(''.join(texts))
    
    @commands.command()
    @commands.is_owner()
    async def adminlist(self, ctx: commands.Context):
        """Displays the admin list."""
        texts = ['The current admins are:\n']
        for admin_id in config['admins']:
            user = await self.bot.fetch_user(admin_id)
            texts.append(f' • {user.name}#{user.discriminator} ({user.id})\n')
        await ctx.reply(''.join(texts))
    
    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx: commands.Context):
        """Reloads all extensions."""
        self.bot.reload_extensions()
        await ctx.reply('All extensions have been reloaded.')
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.NotOwner):
            await ctx.reply(f'Sorry, {ctx.author.mention}, but you have'
                ' insufficient permissions.')
        
        else:
            # Propagate upwards.
            raise error
    
    @cog_ext.cog_slash(
        name='bugreport',
        description='Report a bug to the development team.',
        guild_ids=supp_config.guild_ids,
        options=[
            create_option(
                name='description',
                description='A description of the bug.',
                option_type=3, # 3 means string
                required=True
            )
        ]
    )
    async def _bugreport_slash(self, ctx: SlashContext, description):
        async def send_to(user):
            """Send a report to the specified user."""

            embed = Embed(
                title='Bug Report',
                description=description,
                color=user2color(ctx.author),
                timestamp=datetime.utcnow()
            )

            author = ctx.author
            
            embed.set_author(
                name=f'{author.display_name}#{author.discriminator}',
                url='', # No message to link.
                icon_url=author.avatar_url
            )

            embed.set_footer(
                text=f'{ctx.guild.name} - #{ctx.channel.name}'
            )

            await user.send(embed=embed)

        if self.bot.owner_id:
            owner = await self.bot.fetch_user(self.bot.owner_id)
            await send_to(owner)
        elif self.bot.owner_ids:
            for owner_id in self.bot.owner_ids:
                owner = await self.bot.fetch_user(owner_id)
                await send_to(owner)
        else:
            # Request owners.
            app = await self.bot.application_info()
            if app.team:
                for owner in app.team.members:
                    await send_to(owner)
            else:
                await send_to(app.owner)
        
        await ctx.send('Thanks! 😄')
    
def setup(bot):
    cog = OwnerCog(bot)
    bot.add_cog(cog)
