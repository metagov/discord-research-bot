from discord.ext.commands.errors import BadArgument, MissingRequiredArgument
from discord.guild import Guild
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option
from config import config, parse_config
from discord_slash import cog_ext
from discord.ext import commands
from utils import is_admin
import logging
import discord

# For slash command parameters.
supp_config = parse_config(config)

class AdminCog(commands.Cog):
    """Provides functions for everyday configuration of the bot."""

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.check(is_admin)
    async def admin(self, ctx: commands.Context, user: discord.User):
        """Adds someone to the list of admins."""
        if user.id not in config['admins']:
            config['admins'].append(user.id)
            config.save() # Does not automatically save.
            
            await ctx.reply(f'{user.mention}, you\'ve successfully been'
                ' added to the list of bot administrators.')
        else:
            await ctx.reply(f'{user.mention}, you are already in the'
                ' list of bot administrators.')
    
    @admin.error
    async def admin_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadArgument):
            await ctx.reply(f'Sorry, {ctx.author.mention}, but I cannot find'
                ' that member.')
        
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply(f'Sorry, {ctx.author.mention}, but you have'
                ' insufficient permissions.')

    @commands.command()
    @commands.check(is_admin)
    async def deadmin(self, ctx: commands.Context, user: discord.User):
        """Removes someone from the list of admins."""
        if user.id not in config['admins']:
            await ctx.reply(f'{user.mention}, you are not in the list of'
                ' bot administrators.')
        else:
            config['admins'].remove(user.id)
            config.save() # Does not save automatically.

            await ctx.reply(f'{user.mention}, you have been removed from the'
                ' list of bot administrators.')

    @deadmin.error
    async def deadmin_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadArgument):
            await ctx.reply(f'Sorry, {ctx.author.mention}, but I cannot find'
                ' that member.')
        
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply(f'Sorry, {ctx.author.mention}, but you have'
                ' insufficient permissions.')

        else:
            # Propagate upwards.
            raise error

    @commands.command()
    @commands.check(is_admin)
    async def viewconfig(self, ctx: commands.Context, guild: Guild=None):
        """Displays per-guild configuration(s)."""
        return await ctx.reply('Unimplemented, sorry!')

        if not guild:
            # Show specific guild.
            pass
        else:
            # Show all guilds.
            pass

    @commands.command(name='addguild')
    @commands.check(is_admin)
    async def _addguild(self, ctx: commands.Context, guild: Guild=None):
        """Adds a guild to the list of slash command guild ids."""
        if not guild:
            guild = ctx.guild

        if guild.id not in config['guild_ids']:
            config['guild_ids'].append(guild.id)
            config.save() # Does not save automatically.

            await ctx.reply(f'Alright, {ctx.author.mention}. Slash commands'
                f' are now enabled in **{guild.name}**.')
        else:
            await ctx.reply(f'{ctx.author.mention}, slash commands are already'
                f' enabled in **{guild.name}**.')

    @cog_ext.cog_slash(
        name='addguild',
        description='Adds a guild to the list of slash command guild ids.',
        guild_ids=supp_config.guild_ids,
        options=[
            create_option(
                name='guild',
                description='The numeric id of the guild to add.',
                option_type=4, # 4 means integer.
                required=False
            )
        ]
    )
    async def _addguild_slash(self, ctx: SlashContext, guild=0):
        # Check for permissions first.
        if ctx.author_id not in config['admins']:
            return await ctx.send(f'Sorry, {ctx.author.mention}, but you have'
                ' insufficient permissions.')

        return await ctx.send('Unimplemented!')

        if not guild:
            print(guild)
            guild = ctx.guild_id # Default to current guild.

        guild = await self.bot.fetch_guild(guild)
        if not guild:
            return await ctx.send(f'Sorry, {ctx.author.mention}, but that'
                ' guild doesn\'t seem to exist.')

        if guild.id not in config['guild_ids']:
            config['guild_ids'].append(guild.id)
            config.save() # Does not save automatically.

            await ctx.send(f'Alright, {ctx.author.mention}. **{guild.name}**'
                ' has been added to the list of guilds with slash commands.')
        else:
            await ctx.send(f'{ctx.author.mention}, **{guild.name}** is already'
                ' in the list of guilds with slash commands.')
    
def setup(bot):
    cog = AdminCog(bot)
    bot.add_cog(cog)