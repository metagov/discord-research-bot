from discord.ext import commands

class BridgeCog(commands.Cog):
    '''Transports messages across guild boundaries.'''
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

def setup(bot: commands.Bot):
    bot.add_cog(BridgeCog(bot))