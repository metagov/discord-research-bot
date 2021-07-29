from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option
from config import config

class RewardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @cog_ext.cog_slash(
        name='reward',
        description='Set your ETH wallet address.',
        guild_ids=config['guild_ids'],
        options=[
            create_option(
                name='address',
                description='A ETH wallet address.',
                option_type=3, # 3 means string
                required=True
            )
        ]
    )
    async def _reward(self, ctx: SlashContext, address: str):
        if 'wallets' not in config:
            config['wallets'] = {}
        # Do some verification step probably.
        config['wallets'][ctx.author_id] = address
        config.save()
        await ctx.send('Done!')

def setup(bot):
    cog = RewardCog(bot)
    bot.add_cog(cog)