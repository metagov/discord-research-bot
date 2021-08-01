from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from config import config, parse_config
from utils import message2embed

# For slash command parameters.
supp_config = parse_config(config)

class BridgeCog(commands.Cog):
    """Allows the replication of messages across guild boundaries."""

    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        description='Sets or resets the bridge associated with this channel.',
        guild_ids=supp_config.guild_ids
    )
    async def bridge(self, ctx: SlashContext, group=''):
        if ctx.author_id not in config['admins']:
            return await ctx.send(f'Sorry, {ctx.author.mention}, but you have'
                ' insufficient permissions to run this command.')

        if group:
            self.set_channel_group(ctx.channel, group)

            count = len(config['bridges']['groups'][group]) - 1
            await ctx.send(f'{ctx.author.mention}, {ctx.channel.mention} is'
                f' now connected to `{count}` other channels in the group'
                f' `{group}`.')
        else:
            self.reset_channel_group(ctx.channel)

            await ctx.send(f'{ctx.author.mention}, {ctx.channel.mention} is'
                f' no longer connected to any other channels.')
    
    def set_channel_group(self, channel, group):
        """Sets channel group in config and saves."""
        self.reset_channel_group(channel, save=False) # Clears existing mapping.

        config['bridges']['channels'][str(channel.id)] = group

        if group not in config['bridges']['groups']:
            config['bridges']['groups'][group] = []
        
        # Don't add duplicates.
        if channel.id not in config['bridges']['groups'][group]:
            config['bridges']['groups'][group].append(channel.id)

        config.save() # Does not save automatically.
        

    def reset_channel_group(self, channel, save=True):
        """Removes channel group mapping from config and conditionally saves."""
        group = ''
        if str(channel.id) in config['bridges']['channels']:
            key = str(channel.id)

            # Remove from 'channels'.
            group = config['bridges']['channels'].pop(key)

        # Remove from 'groups'.
        if group in config['bridges']['groups'] and \
            channel.id in config['bridges']['groups'][group]:
            config['bridges']['groups'][group].remove(channel.id)

            # Remove group if it is now empty.
            if not config['bridges']['groups'][group]:
                del config['bridges']['groups'][group]

        # Save config if requested.
        if save:
            config.save()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return # Don't replicate own messages.

        # Replicate message within bridge groups.
        if str(message.channel.id) not in config['bridges']['channels']:
            return # Does not map to a group.
        
        group = config['bridges']['channels'][str(message.channel.id)]
        if group not in config['bridges']['groups']:
            print(f'Detected hangling reference. {message.channel.id} is'
                f' mapped to {group} but {group} maps to nothing. Resetting'
                ' the mapping for this channel and aborting.')
            return self.reset_channel_group(message.channel)
        
        # Create the embed.
        embed = message2embed(message)
        embed.set_footer(text=f'{group} | {embed.footer.text}')

        for channel_id in config['bridges']['groups'][group]:
            
            # Don't send to same channel.
            if channel_id == message.channel.id:
                continue
            
            channel = await self.bot.fetch_channel(channel_id)
            await channel.send(embed=embed)
    
    def link_channels(self, *channels):
        """Link a variable number of channels."""
        group = self.next_available_group_name()
        for channel in channels:
            self.set_channel_group(channel, group)

    def next_available_group_name(self):
        """Returns a group name not in use by any other channels."""
        number = 0
        while str(number) not in config['bridges']['groups']:
            number += 1
        return str(number)


def setup(bot):
    cog = BridgeCog(bot)
    bot.add_cog(cog)
