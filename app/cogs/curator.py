from discord.ext import commands

class CuratorCog(commands.Cog):

    def __init__(self, bot):
        print('Loaded Curator Cog')
        self.bot = bot

    def cog_unload(self):
        print('Unloaded Curator Cog')
    
def setup(bot):
    bot.add_cog(CuratorCog(bot))