from discord import channel
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option
from config import config, perms
from utils import message_to_embed

class BridgeCog(commands.Cog):
    '''Transports messages across guild boundaries.'''
    
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_subcommand(
        base='set',
        name='bridge',
        description='Set the bridge group associated with this channel.',
        guild_ids=config['guild_ids'],
        base_permissions=perms,
        base_default_permission=False,
        options=[
            create_option(
                name='group',
                description='Any string.',
                option_type=3, # 3 means string.
                required=False
            )
        ]
    )
    async def _set_bridge(self, ctx: SlashContext, group=''):
        if not group:
            self.remove_bridge(ctx.channel_id)

            # Remove observatory channel from server.
            if 'repeats' in config and \
                str(ctx.guild_id) in config['repeats']:
                del config['repeats'][str(ctx.guild_id)]

            await ctx.send(f'{ctx.channel.mention} is no longer associated'
                ' with a bridge. This channel\'s observatory channel has been'
                ' cleared.')
        if group:
            self.remove_bridge(ctx.channel_id)
            self.add_bridge(ctx.channel_id, group)

            # Set observatory channel for server.
            if 'repeats' not in config:
                config['repeats'] = {}
            config['repeats'][str(ctx.guild_id)] = ctx.channel_id

            await ctx.send(f'{ctx.channel.mention} is now associated with'
                f' `{group}`. This channel has been set as the observatory'
                ' channel for this server.')
        config.save()
    
    def add_bridge(self, channel_id, group):
        # Does not save config.
        if 'groups' not in config: # groups -> channel IDs.
            config['groups'] = {}
        if group not in config['groups']:
            config['groups'][group] = []
        if channel_id not in config['groups'][group]:
            config['groups'][group].append(channel_id)
        
        if 'channels' not in config: # channel ID -> group.
            config['channels'] = {}
        if str(channel_id) not in config['channels']:
            config['channels'][str(channel_id)] = group
    
    def remove_bridge(self, channel_id):
        # Does not save config.
        if 'channels' in config and \
            str(channel_id) in config['channels']:
            
            group = config['channels'][str(channel_id)]
            if 'groups' in config and \
                group in config['groups'] and \
                    channel_id in config['groups'][group]:
                    
                    config['groups'][group].remove(channel_id)
                    if not config['groups'][group]: # If it is now empty.
                        del config['groups'][group]
            
            del config['channels'][str(channel_id)]

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if it is associated with a group.
        if 'channels' not in config or \
            str(message.channel.id) not in config['channels'] or \
                message.author == self.bot.user:
            return
        
        group = config['channels'][str(message.channel.id)]
        embed = message_to_embed(message)

        if 'groups' in config and \
            group in config['groups']:
            for dest_id in config['groups'][group]:
                
                # Don't repeat to same channel.
                if dest_id == message.channel.id:
                    continue

                channel = await self.bot.get_or_fetch_channel(dest_id)
                await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(BridgeCog(bot))