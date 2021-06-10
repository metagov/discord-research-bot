from discord.ext import commands

class OwnerCog(commands.Cog):

    def __init__(self, bot):
        print('Loaded Owner Cog')
        self.bot = bot

    def cog_unload(self):
        print('Unloaded Onwer Cog')

    @commands.command()
    async def ping(self, ctx):
        await ctx.send('pong')

def setup(bot):
    bot.add_cog(OwnerCog(bot))