from discord.embeds import EmbedProxy, EmptyEmbed
from discord.reaction import Reaction
from discord.utils import get
from discord.ext import commands
from config import config
from discord import Guild, TextChannel, RawReactionActionEvent, Message, Member
from discord_slash.context import ComponentContext, SlashContext
from discord_slash.model import ButtonStyle
from discord_slash.utils import manage_components
from discord_slash import cog_ext
from utils import message_to_embed
from discord import utils
from tinydb import TinyDB
import discord
import dataset

'''
Database schema for storing messages.
{
    'author': {
        '_id':  1290581592859,
        'name': 'Andrew Wiles'
    }
    'content':    'message content',
    'timestamp':  'iso string',
    'guild': {
        '_id':  189083261364,
        'name': 'Bug\'s bunker'
    },
    'channel': {
        '_id': 198657173626,
        'name': 'awuie129048165'
    }
}
'''

def build_permission_action_row(disabled=False):
    # Builds the action row for the permission message.
    return manage_components.create_actionrow(
        manage_components.create_button(
            custom_id='accept',
            style=ButtonStyle.green,
            disabled=disabled,
            label='yes'
        ),

        manage_components.create_button(
            custom_id='anon',
            style=ButtonStyle.gray,
            disabled=disabled,
            label='yes, but anonymously'
        ),

        manage_components.create_button(
            custom_id='decline',
            style=ButtonStyle.red,
            disabled=disabled,
            label='no'
        ),

        manage_components.create_button(
            style=ButtonStyle.URL,
            label='join our server',
            url='https://discord.com'
        )
    )

class CuratorCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        print('Loaded', self.__class__.__name__)
        self.bot = bot

    @commands.command()
    @commands.has_role('Curator') # TODO: Make this work in DMs.
    async def curate(self, ctx: commands.Context, msg: discord.Message):
        # Manually start curation process.
        await self.begin_curation_process(msg)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        # Triggered when a reaction is added to any message.
        ch: TextChannel = await self.bot.fetch_channel(payload.channel_id)

        # Ensure we are not in a DM.
        if not ch.guild:
            return

        message: Message = await ch.fetch_message(payload.message_id)

        # Only propagate when the reaction count is now 1.
        reaction: Reaction = get(message.reactions, emoji=payload.emoji.name)
        if reaction.count != 1:
            return

        reactor: Member = await ch.guild.fetch_member(payload.user_id)

        # Check for the appropriate emoji.
        if str(payload.emoji) == '🔭':
            # Check for the appropriate role.
            if utils.get(reactor.roles, name='Curator'): # TODO: Same as above.
                await self.begin_curation_process(message)

    async def begin_curation_process(self, msg: discord.Message):
        # gd: Guild = await self.bot.fetch_guild(config['guild_id'])
        ch: TextChannel = await self.bot.fetch_channel(config['pending_id'])

        # Create "ask for permission" button.
        action_row = manage_components.create_actionrow(
            manage_components.create_button(
                custom_id=f'ask-{msg.author.id}',
                style=ButtonStyle.green,
                label='request permission'
            )
        )

        await ch.send(embed=message_to_embed(msg), components=[action_row])

    @commands.Cog.listener()
    async def on_component(self, ctx: ComponentContext):
        # Triggered on any component interaction.
        if 'ask-' in ctx.custom_id:
            embed: discord.Embed = ctx.origin_message.embeds[0]
            await ctx.origin_message.delete()

            # Ask user for permission.
            askee_id = int(ctx.custom_id[4:])
            askee: discord.User = await self.bot.fetch_user(askee_id)
            # embed.set_footer(text='May we quote you in our research?')
            action_row = build_permission_action_row()
            await askee.send(embed=embed, components=[action_row])
        
        if 'accept' == ctx.custom_id:
            embed: discord.Embed = ctx.origin_message.embeds[0]
            action_row = build_permission_action_row(disabled=True)
            await ctx.origin_message.edit(components=[action_row])
            await self.message_approved(embed)
            
        if 'anon' == ctx.custom_id:
            embed: discord.Embed = ctx.origin_message.embeds[0]
            embed.set_author(
                name=f'anonymous sally', 
                url='',
                icon_url='https://i.ytimg.com/vi/LCgQhShov40/maxresdefault.jpg'
            )

            # Propagate the anonymized message.
            action_row = build_permission_action_row(disabled=True)
            await ctx.origin_message.edit(components=[action_row])
            await self.message_approved(embed)
        
        if 'decline' == ctx.custom_id:
            action_row = build_permission_action_row(disabled=True)
            await ctx.origin_message.edit(components=[action_row])
            # Do nothing else, they have declined.
        
        await ctx.send('Done!', delete_after=5)
    
    async def on_message_approved(self, embed: discord.Embed):
        d = TinyDB('messages.json')

        # Find the original message link.
        message: discord.Message = None
        for field in embed.fields:
            if field.value.startswith('[Jump to message]'):
                text = field.value[18:-1]
                parts = text.split('/')
                guild_id = int(parts[4])
                channel_id = int(parts[5])
                msg_id = int(parts[6])

                # attempting to retrieve message from the link
                guild = await self.bot.fetch_guild(guild_id)
                if guild:
                    channel = guild.get_channel(channel_id)                    
                    if channel:
                        try:
                            message = await channel.fetch_message(msg_id)
                        except discord.errors.Forbidden as e:
                            if e.code == 50001:
                                print("I couldn't access that channel")
                    else:
                        print("Channel may have been deleted")
                else:
                    print("I couldn't access that server")

        d.insert({

            'content': message.content
        })
        
        
    async def message_approved(self, embed: discord.Embed):
        '''Called when a message should be sent to the approved channel.'''
        # gd: Guild = await self.bot.fetch_guild(config['guild_id'])
        ch: TextChannel = await self.bot.fetch_channel(config['approved_id'])
        # embed.set_footer(text=EmptyEmbed)
        await self.on_message_approved(embed)
        await ch.send(embed=embed)

    '''Commands to manipulate pending and approved channels.'''

    @cog_ext.cog_subcommand(base='set', name='approved',
        guild_ids=config['guild_ids'])
    async def _set_approved(self, ctx: SlashContext):
        config['approved_id'] = ctx.channel.id
        await ctx.send('Done!')

    @cog_ext.cog_subcommand(base='set', name='pending',
        guild_ids=config['guild_ids'])
    async def _set_pending(self, ctx: SlashContext):
        config['pending_id'] = ctx.channel.id
        await ctx.send('Done!')

def setup(bot: commands.Bot):
    cog = CuratorCog(bot)
    bot.add_cog(cog)