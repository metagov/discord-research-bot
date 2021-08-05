from discord.ext import commands
from discord_slash.context import SlashContext
from utils import is_admin
from discord_slash import cog_ext
from config import config, parse_config

# For slash commands.
supp_config = parse_config(config)

class DeployCog(commands.Cog):
    """Makes it easy to deploy to new servers."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @cog_ext.cog_slash(
        name='deploy',
        description='Start the deployment process to a new satellite server.',
        guild_ids=supp_config.guild_ids
    )
    async def _deploy(self, ctx: SlashContext):
        if not is_admin(ctx):
            await ctx.send(f'{ctx.author.mention}, you have insufficient'
                ' permissions to run this command.')
        
        # (1) Explain the deployment process to the author.
        await ctx.author.send(f'{ctx.author.mention}, you have just started'
            ' the process of deploying to a new satellite server. I\'m going'
            ' to need you to **send any message in what you want to be the'
            ' Observatory channel for the satellite server**. You may type'
            ' \'cancel\' (case insensitive) at any point to cancel this'
            ' process.')

        # (2) User sends a message to the observatory channel in the deployee.
        await ctx.send(f'{ctx.author.mention}, the deployment process'
            ' has now begun! I\'ve sent you a private message explaining'
            ' the progress and what you should do now.')
    
    @commands.Cog.listener()
    async def on_message(self, message):
        key = str(message.author.id)

        # Check if they are doing a deployment.
        if key not in config['deploys_wip']:
            return

        # Check if author wants to cancel.
        if message.content and message.content.strip().lower() == 'cancel':
            del config['deploys_wip'][key]
            config.save() # Not automatic.

            await message.author.send(f'{message.author.mention}, I have just'
                ' canceled your deployment.')
            
            return # Leave here.
        
        # Check if we are in a DM.
        if not message.guild:
            return

        if config['deploys_wip'][key]['stage'] == 0:
            # Author just sent a message in the satellite Observatory channel.
            config['deploys_wip'][key]['observatory'] = message.channel.id
            config['deploys_wip'][key]['stage'] = 1
            config.save() # Not automatic.

            await message.author.send(f'{message.author.mention}, you have'
                f' just set **{message.guild.name} - #{message.channel.name}**'
                f' to be the Observatory channel for **{message.guild.name}**.'
                ' Now, I am asking you to **send a message in the channel'
                ' you want to be the **pending messages** channel for'
                f' **{message.guild.name}.')
        
        elif config['deploys_wip'][key]['stage'] == 1:
            # Author just sent message in the approved channel.
            config['deploys_wip'][key]['pending'] = message.channel.id
            config['deploys_wip'][key]['stage'] = 2
            config.save() # Not automatic.

            # Get Observatory satellite channel.
            channel_id = config['deploys_wip'][key]['observatory']
            channel = await self.bot.fetch_channel(channel_id)

            await message.author.send(f'{message.author.mention}, you have'
                f' just set **{message.guild.name} - #{message.channel.name}**'
                f' to be the pending channel for **{channel.name}**.'
                ' Now, I am asking you to **send a message in the channel'
                ' you want to be the **pending messages** channel for'
                f' **{channel.name}.') 


        elif config['deploys_wip'][key]['stage'] == 2:
            # Author just sent message in approved channel.
            settings = config['deploys_wip'][key]
            settings['approved'] = message.channel.id

            self.commit_deployment(settings)
            self.delete_deployment(message.author)
    
    def commit_deployment(self, settings):
        """Applies the desired changes that have accrued during the deployment
        process."""
        cog_name = 'curator'
        cog = self.bot.get_cog(cog_name)

        if not cog:
            raise Exception(f'Failed to get cog \'{cog_name}\'!')
        
        # (1) Use setup function (setup approved and pending).
        observatory_id = settings['observatory']
        pending_id = settings['pending']
        approved_id = settings['approved']
        cog.setup(observatory_id, pending_id, approved_id)

        # (2) Setup bridge for satellite server.
        cog_name = 'bridge'
        cog = self.bot.get_cog(cog_name)

        if not cog:
            raise Exception(f'Failed to get cog \'{cog_name}\'!')
        
    def delete_deployment(self, user, save=True):
        """Deletes a current user's deployment in process."""
        del config['deploys_wip'][str(user.id)]

        if save:
            config.save() # Not automatic.


def setup(bot):
    cog = DeployCog(bot)
    bot.add_cog(cog)
