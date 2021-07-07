from typing import Text
from discord import utils
from discord.channel import TextChannel
from discord.colour import Color
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.guild import Guild
from discord.member import Member
from discord.message import Message
from discord.raw_models import RawReactionActionEvent
from discord.user import User
from discord_slash.context import ComponentContext
from discord_slash.model import ButtonStyle
from discord.embeds import Embed
from discord_slash.utils.manage_components import create_actionrow, create_button

class CuratorCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        print('Loaded Curator Cog')
        self.bot = bot

    def cog_unload(self):
        print('Unloaded Curator Cog')

    def build_permission_embed(self, message: Message):
        '''Builds the embed(ded) for the permission message.'''
        embed = Embed(
            description=message.content,
            color=Color.blue(),
        )

        author: User = message.author

        embed.set_author(
            name=f"{author.display_name}#{author.discriminator}", 
            url=f"https://discord.com/users/{author.id}",
            icon_url=author.avatar_url
        )

        embed.set_footer(
            text='By pressing accept, you consent for your anonymized' + \
                ' message to be published.'
        )

        return embed

    def build_permission_action_row(self, curator: User):
        '''Builds the action row for the permission message.'''
        return create_actionrow(
            create_button(
                custom_id='accept' if not curator else f'accept-{curator.id}',
                style=ButtonStyle.green,
                disabled=curator is None,
                label='accept',
            ),

            create_button(
                custom_id='reject' if not curator else f'reject-{curator.id}',
                style=ButtonStyle.red,
                disabled=curator is None,
                label='reject',
            ),

            create_button(
                style=ButtonStyle.URL,
                label='join our server',
                url='https://discord.com'
            ),
        )

    async def begin_curation_process(self, message: Message, curator: User):
        '''Begins the curation process.'''
        embed = self.build_permission_embed(message=message)
        action_row = self.build_permission_action_row(curator=curator)
        await message.author.send(embed=embed, components=[action_row])

    @commands.command()
    @commands.has_role('Curator') # TODO: Make this work in DMs.
    async def curate(self, context: Context, message: Message):
        '''Begins the curation process.'''
        await self.begin_curation_process(message, context.author)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        '''Triggered when a reaction is added to any message.'''
        channel: TextChannel = await self.bot.fetch_channel(payload.channel_id)

        # Ensure we are not in a DM.
        if not channel.guild:
            return

        message: Message = await channel.fetch_message(payload.message_id)
        reactor: Member = await channel.guild.fetch_member(payload.user_id)

        # Check for the appropriate emoji.
        if str(payload.emoji) == '🔭':
            # Check for the appropriate role.
            if utils.get(reactor.roles, name='Curator'): # TODO: Same as above.
                await self.begin_curation_process(message, reactor)

    @commands.Cog.listener()
    async def on_component(self, context: ComponentContext):
        '''Triggered on any component interaction.'''
        if isinstance(context.custom_id, str) and '-' in context.custom_id:
            # Recover the curator from the custom IDs.
            curator_id = int(context.custom_id[context.custom_id.find('-') + 1:])
            curator: User = await self.bot.fetch_user(curator_id)

            # Disable the accept and reject buttons.
            action_row = self.build_permission_action_row(None)
            await context.edit_origin(components=[action_row])

            color = Color.blue()
            footer = ''

            # Handle the 'accept' case.
            if context.custom_id.startswith('accept'):
                color = Color.green()
                footer = 'Approved by author for anonymous use.'
    
            # Handle the 'reject' case.
            elif context.custom_id.startswith('reject'):
                color = Color.red()
                footer = 'Anonymous use rejected by author.'
            
            # Notify the curator.
            embed: Embed = context.origin_message.embeds[0].copy()
            embed.color = color
            embed.set_footer(text=footer)
            await curator.send(embed=embed)
    
def setup(bot):
    bot.add_cog(CuratorCog(bot))