import discord
from discord.ext import commands
from item import RequestPendingButton, CancelPendingButton, construct_view
from model import MessageModel, SatelliteModel
from mongoengine import connect

from cogs import Admin

connect("telescope")

class TelescopeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents
        )

    async def setup_hook(self):
        self.add_dynamic_items()
    
    async def setup_hook(self):
        guild = discord.Object(id=474736509472473088)
        # await self.load_extension("cog_test")
        await self.add_cog(Admin(self), guild=guild)
        await self.tree.sync(guild=guild)
        print(f"Logged in as {self.user}")


bot = TelescopeBot()

@bot.event
async def on_raw_reaction_add(reaction):
    print(reaction)
    channel = bot.get_channel(reaction.channel_id)
    message = await channel.fetch_message(reaction.message_id)

    satellite = SatelliteModel.objects(id=message.guild.id).first()
    # print(satellite)
    pending_channel = bot.get_channel(satellite.pending_channel_id)

    msg = MessageModel(
        id          = message.id,
        channel_id  = message.channel.id,
        guild_id    = message.guild.id,
        author_id   = message.author.id,
        author_name = message.author.name,
        content     = message.content,
        attachments = message.attachments,

        created_at  = message.created_at,
        edited_at   = message.edited_at,
        jump_url    = message.jump_url
    )

    msg.save()

    embed = discord.Embed(
        description=message.content,
        timestamp=message.edited_at or message.created_at
    )
    embed.set_author(
        name=message.author.global_name,
        icon_url=message.author.display_avatar.url,
        url=message.jump_url
    )

    embed.set_footer(text=f"{message.guild.name} - #{message.channel.name}")
    embed.add_field(
        name="Curated By",
        value=reaction.member.global_name,
        inline=False
    )

    pending_message = await pending_channel.send(
        embed=embed, view=construct_view(message.id, [RequestPendingButton, CancelPendingButton])
    )

    if (reaction.guild_id is not None) and (reaction.emoji.name == "🔭"):
        print(f"got telescope reaction on {reaction.guild_id}:{reaction.channel_id}:{reaction.message_id}")

