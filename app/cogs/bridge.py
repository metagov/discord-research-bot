from discord.channel import TextChannel
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option
import discord

GUILD_IDS = [474736509472473088]

def to_embed(msg: discord.Message) -> discord.Embed:
    '''Turns a message into an embed(ded).'''
    embed = discord.Embed(
        description=msg.content,
        color=discord.Color.blue(),
    )

    author: discord.User = msg.author

    embed.set_author(
        name=f"{author.display_name}#{author.discriminator}", 
        url=f"https://discord.com/users/{author.id}",
        icon_url=author.avatar_url
    )

    embed.set_footer(text=f'{msg.guild.name} - #{msg.channel.name}')

    return embed

class BridgeCog(commands.Cog):
    '''Transports messages across guild boundaries.'''
    
    def __init__(self, bot: commands.Bot):
        print('Loaded', self.__class__.__name__)
        self.channels = {} # Channel -> List[Tag].
        self.tags = {}     # Tag -> List[Channel].
        self.bot = bot

    @cog_ext.cog_subcommand(
        base='bridge',
        name='add',
        description='Adds a tag to a list associated with this channel. ' + \
           'Messages are replicated via common tags.',
        guild_ids=GUILD_IDS,
        options=[
            create_option(
                name='tag',
                description='Any string.',
                option_type=3, # 3 means string.
                required=True
            )
        ])
    async def _bridge_add(self, ctx: SlashContext, tag: str):
        if ctx.channel_id not in self.channels:
            self.channels[ctx.channel_id] = []
        self.channels[ctx.channel_id].append(tag)
        if tag not in self.tags:
            self.tags[tag] = []
        self.tags[tag].append(ctx.channel_id)
        await ctx.send('Done!')
        print(self.channels)
        print(self.tags)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        # Ensure it wasn't sent by us and is in an interesting channel.
        if msg.author == self.bot.user or msg.channel.id not in self.channels:
            print('Quitting early!')
            return
        
        sent = set()
        embed = to_embed(msg)
        for tag in self.channels[msg.channel.id]:
            for _id in self.tags[tag]:
                if _id == msg.channel.id or _id in sent:
                    continue
                channel: TextChannel = await self.bot.fetch_channel(_id)
                await channel.send(embed=embed)
                sent.add(_id)

def setup(bot: commands.Bot):
    cog = BridgeCog(bot)
    bot.add_cog(cog)
