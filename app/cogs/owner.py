from discord.ext import commands
from main import extensions

class OwnerCog(commands.Cog):

    def __init__(self, bot):
        print('Loaded Owner Cog')
        self.bot = bot

    def cog_unload(self):
        print('Unloaded Onwer Cog')

    @commands.is_owner()
    @commands.command()
    async def reset(self, ctx):
        for cog in extensions:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        await ctx.send('Done!')

    @commands.is_owner()
    @commands.command()
    async def ping(self, ctx):
        await ctx.send('pong')

def setup(bot):
    bot.add_cog(OwnerCog(bot))