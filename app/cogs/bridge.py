from discord.ext import commands

class BridgeCog(commands.Cog):

    def __init__(self, bot):
        print('Loaded Bridge Cog')
        self.bot = bot

    def cog_unload(self):
        print('Unloaded Bridge Cog')
    
def setup(bot):
    bot.add_cog(BridgeCog(bot))