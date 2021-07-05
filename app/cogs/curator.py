from discord.channel import TextChannel
from discord.colour import Color
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.message import Message
from discord.raw_models import RawReactionActionEvent
from discord.user import User
from discord_slash.context import ComponentContext
from discord_slash.utils import manage_components
from discord_slash.model import ButtonStyle
from discord.embeds import Embed

class CuratorCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        print('Loaded Curator Cog')
        self.bot = bot

    def cog_unload(self):
        print('Unloaded Curator Cog')
    
    @commands.Cog.listener()
    async def on_component(self, ctx: ComponentContext):
        '''Triggered on any component interaction.
        
        Prefer global event handler over handling the events in the commands
        themselves because if the bot is restarted then the interactions will
        fail.'''
        
        # really messy way of doing this, let's see if we can find a way to edit componenets
        await ctx.edit_origin(components=[manage_components.create_actionrow(
                        manage_components.create_button(
                            style=ButtonStyle.green,
                            label='accept',
                            disabled=True
                        ),
                        manage_components.create_button(
                            style=ButtonStyle.red,
                            label='reject',
                            disabled=True
                        ),
                        manage_components.create_button(
                            style=ButtonStyle.URL,
                            label='join our server',
                            url='https://discord.com'
                        )
                    )])
        if ctx.custom_id is not None and ctx.custom_id.startswith('yes-'):
            reactor: User = await self.bot.fetch_user(int(ctx.custom_id[4:]))
            
            # ...
            if not reactor.dm_channel:
                await reactor.create_dm()
            dm: TextChannel = reactor.dm_channel
            
            # ...
            embed: Embed = ctx.origin_message.embeds[0].copy()
            embed.color = Color.green()
            embed.set_footer(text='Approved by author for anonymous use.')
            await dm.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        channel: TextChannel = await self.bot.fetch_channel(payload.channel_id)
        message: Message = await channel.fetch_message(payload.message_id)
        reactor: User = await self.bot.fetch_user(payload.user_id)
        
        # Ensure we are not in a DM.
        if not channel.guild:
            return False

        # ...
        if payload is not None and str(payload.emoji) == '🔭':
            author: User = message.author # Whoever wrote original message.

            # ...
            if not author.dm_channel:
                await author.create_dm()
            dm: TextChannel = author.dm_channel

            # ...
            embed = Embed(
                description=message.content,
                color=Color.blue()
            )

            embed.set_author(
                name=f"{author.display_name}#{author.discriminator}", 
                url=f"https://discord.com/users/{author.id}",
                icon_url=author.avatar_url
            )
            
            embed.set_footer(
                text='By pressing accept, you consent for your anonymized ' + \
                    'message to published.'
            )

            # ...
            await dm.send(
                embed=embed,
                components=[
                    manage_components.create_actionrow(
                        manage_components.create_button(
                            style=ButtonStyle.green,
                            label='accept',
                            custom_id=f'yes-{reactor.id}'
                        ),
                        manage_components.create_button(
                            style=ButtonStyle.red,
                            label='reject',
                            custom_id=f'no-{reactor.id}'
                        ),
                        manage_components.create_button(
                            style=ButtonStyle.URL,
                            label='join our server',
                            url='https://discord.com'
                        )
                    )
                ]
            )

def setup(bot):
    bot.add_cog(CuratorCog(bot))