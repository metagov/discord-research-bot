from discord.ext import commands
from discord.ext.commands.core import group
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option
from config import config
import discord

class BridgeCog(commands.Cog):
    '''Transports messages across guild boundaries.'''
    
    def __init__(self, bot: commands.Bot):
        # print('Loaded', self.__class__.__name__)
        self.bot = bot
    
    @cog_ext.cog_subcommand(
        base='bridge',
        name='set',
        description='Adds this channel to a group. Messages are shared among'
            ' the same group.',
        guild_ids=config['guild_ids'],
        options=[
            create_option(
                name='group_name',
                description='Any string.',
                option_type=3, # 3 means string.
                required=True
            )
        ]
    )
    async def _bridge_set(self, ctx: SlashContext, group_name: str):
        # Map channel IDs to group names.
        if 'bridge_channels' not in config:
            config['bridge_channels'] = {}
        if ctx.channel_id not in config['bridge_channels'] or \
            group_name != config['bridge_channels'][ctx.channel_id]:
            config['bridge_channels'][ctx.channel_id] = group_name

        # Map group name to channel IDs.
        if 'bridge_groups' not in config:
            config['bridge_groups'] = {}
        if group_name not in config['bridge_groups']:
            config['bridge_groups'][group_name] = []
        if ctx.channel_id not in config['bridge_groups'][group_name]:
            config['bridge_groups'][group_name] = \
                config['bridge_groups'][group_name] + [ctx.channel_id]
            config._save()

        # Give response to author.
        await ctx.send(
            f'{ctx.channel.mention} added to group `{group_name}` '
            f'({len(config["bridge_groups"][group_name])} in this group).'
        )

    @cog_ext.cog_subcommand(
        base='bridge',
        name='list',
        description='Lists all group names or the channels associated with a '
            'certain group name.',
        guild_ids=config['guild_ids'],
        options=[
            create_option(
                name='group_name',
                description='Any string.',
                option_type=3, # 3 means string.
                required=False
            )
        ]
    )
    async def _bridge_list(self, ctx: SlashContext, group_name: str=''):
        if group_name:
            # Show channels associated with this group.
            if group_name not in config['bridge_groups']:
                return await ctx.send('That group does not exist!')
            
            text = f'Here are the channels associated with `{group_name}`\n```'

            for _id in config['bridge_groups'][group_name]:
                channel = await self.bot.fetch_channel(_id)
                text += f' • {channel.guild.name} - #{channel.name}'
            
            text += '```'
            await ctx.send(text)

        else:
            # Show all groups.
            n = len(config['bridge_groups'])
            text = f'Here are all the groups ({n} in total)\n```'

            for group_name in config['bridge_groups']:
                m = len(config['bridge_groups'][group_name])
                text += f' • {group_name} ({m} in this group)\n'

            text += '```'
            await ctx.send(text)

    @cog_ext.cog_subcommand(
        base='bridge',
        name='clear',
        description='Clears this channel\'s group or deletes a specific group '
            'by name.',
        guild_ids=config['guild_ids'],
        options=[
            create_option(
                name='group_name',
                description='Any string.',
                option_type=3, # 3 means string.
                required=False
            )
        ]
    )
    async def _bridge_clear(self, ctx: SlashContext, group_name: str=''):
        if group_name:
            # Delete this channel's group.
            if 'bridge_channels' in config and \
                ctx.channel_id in config['bridge_channels']:
                del config['bridge_channels'][ctx.channel_id]
                config._save() # Unsure if I need this.
            
            if 'bridge_groups' in config and \
                group_name in config['bridge_groups'] and \
                    ctx.channel_id in config['bridge_groups'][group_name]:
                l: list = config['bridge_groups'][group_name]
                l.remove(ctx.channel_id)
                config._save() # Unsure if I need this.

                # Delete group if it is now empty.
                if not config['bridge_groups'][group_name]:
                    del config['bridge_groups'][group_name]
                    config._save() # Unsure if I need this.

            await ctx.send('Done!')
        else:
            # Delete the specific group.
            await ctx.send('Done!')

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        # Ensure it wasn't sent by us and is in an interesting channel.
        # if msg.author == self.bot.user or msg.channel.id 
        pass

def setup(bot: commands.Bot):
    bot.add_cog(BridgeCog(bot))