from discord.ext import commands

class OwnerCog(commands.Cog):

    def __init__(self, bot):
        print('Loaded OwnerCog')
        self.bot = bot

    def unload_cog(self):
        print('Unloaded OnwerCog')

    @commands.command()
    async def ping(self, ctx):
        await ctx.send('pong')

def setup(bot):
    bot.add_cog(OwnerCog(bot))