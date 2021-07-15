from json.decoder import JSONDecodeError
from discord.embeds import EmptyEmbed
from discord.ext import commands
from discord import Guild, TextChannel, RawReactionActionEvent, Message, Member
from discord_slash.context import ComponentContext
from discord_slash.model import ButtonStyle
from discord_slash.utils import manage_components
from utils import user_to_color
from discord import utils
from datetime import datetime
import discord_slash
from main import slash # Use this to declare slash commands.
import os              # For manipulating files.
import discord
import json

GUILD_IDS  = [860079798616457227] # For slash commands.
DATA_FNAME = 'curation.json'      # Store all of our data in this file.
INIT_DATA  = {                    # What is initially stored & used.
    'guild_id':    860079798616457227,
    'pending_id':  862848348087517235,
    'approved_id': 862848298876141568
}

def to_embed(msg: discord.Message) -> discord.Embed:
    '''Turns a message into an embed(ded).'''
    embed = discord.Embed(
        description=msg.content,
        color=discord.Color.blue(),
        timestamp=msg.edited_at or msg.created_at
    )

    author: discord.User = msg.author

    embed.set_author(
        name=f"{author.display_name}#{author.discriminator}", 
        url=f"https://discord.com/users/{author.id}",
        icon_url=author.avatar_url
    )

    return embed

def build_permission_action_row(disabled=False):
    # Builds the action row for the permission message.
    return manage_components.create_actionrow(
        manage_components.create_button(
            custom_id='accept',
            style=ButtonStyle.green,
            disabled=disabled,
            label='accept'
        ),

        manage_components.create_button(
            custom_id='anon',
            style=ButtonStyle.gray,
            disabled=disabled,
            label='accept, anonymously'
        ),

        manage_components.create_button(
            custom_id='decline',
            style=ButtonStyle.red,
            disabled=disabled,
            label='decline'
        ),

        manage_components.create_button(
            style=ButtonStyle.URL,
            label='join our server',
            url='https://discord.com'
        )
        # manage_components.create_select(
        #     options=[
        #         create_select_option('yes', value='approve', emoji='👍'),
        #         create_select_option('yes, anonymously', value='anon', emoji='😎'),
        #         create_select_option('no',  value='decline', emoji='👎')
        #     ],
        #     placeholder='may we quote you in our research?',
        #     min_values=1,
        #     max_values=1
        # )
    )

class CuratorCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        print('Loaded', self.__class__.__name__)
        self.bot  = bot

        # Load configuration from disk.
        try:
            with open(DATA_FNAME, 'r') as file:
                self.data = json.load(file)
            print('  Configuration is', self.data)
        except JSONDecodeError:
            # Backup the existing file.
            print(f'  Error loading {DATA_FNAME}. Backing up and proceeding.')
            self.data = INIT_DATA

            relocate = f'{DATA_FNAME}-{datetime.utcnow()}'
            os.rename(DATA_FNAME, relocate)

        except FileNotFoundError:
            print(f'  Created {DATA_FNAME}.')

            self.data = INIT_DATA
            self.sync()
    
    def sync(self):
        # Save data to disk.
        with open(DATA_FNAME, 'w') as file:
            json.dump(self.data, file, indent=4)

    @commands.command()
    @commands.has_role('Curator') # TODO: Make this work in DMs.
    async def curate(self, ctx: commands.Context, msg: discord.Message):
        # Manually start curation process.
        gd: Guild = await self.bot.fetch_guild(self.data['guild_id'])
        ch: TextChannel = await self.bot.fetch_channel(self.data['pending_id'])

        # Create "ask for permission" button.
        action_row = manage_components.create_actionrow(
            manage_components.create_button(
                custom_id=f'ask-{msg.author.id}',
                style=ButtonStyle.green,
                label='ask for permission'
            )
        )

        await ch.send(embed=to_embed(msg), components=[action_row])
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        # Triggered when a reaction is added to any message.
        ch: TextChannel = await self.bot.fetch_channel(payload.channel_id)

        # Ensure we are not in a DM.
        if not ch.guild:
            return

        message: Message = await ch.fetch_message(payload.message_id)
        reactor: Member = await ch.guild.fetch_member(payload.user_id)

        # Check for the appropriate emoji.
        if str(payload.emoji) == '🔭':
            # Check for the appropriate role.
            if utils.get(reactor.roles, name='Curator'): # TODO: Same as above.
                await self.begin_curation_process(message, reactor)

    @commands.Cog.listener()
    async def on_component(self, ctx: ComponentContext):
        # Triggered on any component interaction.
        if 'ask-' in ctx.custom_id:
            embed: discord.Embed = ctx.origin_message.embeds[0]
            await ctx.origin_message.delete()

            # Ask user for permission.
            askee_id = int(ctx.custom_id[4:])
            askee: discord.User = await self.bot.fetch_user(askee_id)
            embed.set_footer(text='May we quote you in our research?')
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
                icon_url=''
            )

            # Propagate the anonymized message.
            action_row = build_permission_action_row(disabled=True)
            await ctx.origin_message.edit(components=[action_row])
            await self.message_approved(embed)
        
        if 'decline' == ctx.custom_id:
            action_row = build_permission_action_row(disabled=True)
            await ctx.origin_message.edit(components=[action_row])
            # Do nothing else, they have declined.
        
    async def message_approved(self, embed: discord.Embed):
        '''Called when a message should be sent to the approved channel.'''
        gd: Guild = await self.bot.fetch_guild(self.data['guild_id'])
        ch: TextChannel = await self.bot.fetch_channel(self.data['approved_id'])
        embed.set_footer(text=EmptyEmbed)
        await ch.send(embed=embed)

    @slash.slash(name='curate', guild_ids=GUILD_IDS)
    async def _curate(self, ctx: discord_slash.SlashContext):
        await ctx.send('pong!')

    @commands.group(name='set')
    async def _set(self, ctx: commands.Context):
        # Deliberately empty.
        pass

    @_set.command()
    async def approved(self, ctx: commands.Context):
        # Use current channel as approved messages channel.
        self.data['approved_id'] = ctx.channel.id
        self.sync()
        await ctx.message.add_reaction('👍')

    @_set.command()
    async def pending(self, ctx: commands.Context):
        # Use current channel as pending messages channel.
        self.data['pending_id'] = ctx.channel.id
        self.sync()
        await ctx.message.add_reaction('👍')

    @_set.command()
    async def reset(self, ctx: commands.Context):
        # Reset current configuration.
        self.data = INIT_DATA
        self.sync()
        await ctx.message.add_reaction('👍')
    
    # @slash.slash(name="setchannel", 
    #             guild_ids=[474736509472473088],
    #             options=[
    #                 create_option(
    #                     name="type",
    #                     description="Specify a channel to set",
    #                     option_type=3,
    #                     required=True,
    #                     choices=[
    #                         create_choice(
    #                             name="pending channel",
    #                             value="pending"
    #                         ),
    #                         create_choice(
    #                             name="approved channel",
    #                             value="approved"
    #                         )
    #                     ]
    #                 )
    #             ])
    # async def set_server(ctx, channel: str):
    #     await ctx.send(channel)

def setup(bot: commands.Bot):
    cog = CuratorCog(bot)
    bot.add_cog(cog)