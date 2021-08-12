from discord.ext import commands
from database import db, is_admin
import discord

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def bootstrap(self, ctx):
        """Makes the owner of the bot an admin."""
        db.user(ctx.author).is_admin = True
        await ctx.message.add_reaction('👍')
    
    @commands.command()
    @commands.check(is_admin)
    async def admin(self, ctx, user: discord.User=None):
        """Makes a user an admin or demotes them if they are an admin."""
        db.user(user).is_admin = not db.user(user).is_admin
        await ctx.message.add_reaction('👍')


def setup(bot):
    cog = AdminCog(bot)
    bot.add_cog(cog)
