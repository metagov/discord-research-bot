import discord
from discord import app_commands, ui
from mongoengine import connect
from model import MessageModel, SatelliteModel
from item import RequestPendingButton, CancelPendingButton, construct_view

connect("telescope")

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(
    name="commandname",
    description="first application command",
    guild=discord.Object(id=474736509472473088)
)
async def first_command(context):
    await context.response.send_message("Hello!")

@tree.command(
    name="setup",
    description="initialize a new satellite server",
    guild=discord.Object(id=474736509472473088)
)
async def setup_satellite(context):
    await context.response.defer()

    observatory = client.get_guild(474736509472473088)

    category = await observatory.create_category(context.guild.name)
    pending =  await observatory.create_text_channel("Pending Messages", category=category)
    approved = await observatory.create_text_channel("Approved Messages", category=category)

    satellite = SatelliteModel(
        id = context.guild.id,
        pending_channel_id = pending.id,
        approved_channel_id = approved.id
    )
    satellite.save()

    await context.followup.send(content="Setup complete!")


@client.event
async def setup_hook():
    client.add_dynamic_items(RequestPendingButton, CancelPendingButton)

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=474736509472473088))
    print("ready!")

@client.event
async def on_raw_reaction_add(reaction):
    print(reaction)
    channel = client.get_channel(reaction.channel_id)
    message = await channel.fetch_message(reaction.message_id)

    satellite = SatelliteModel.objects(id=message.guild.id).first()
    # print(satellite)
    pending_channel = client.get_channel(satellite.pending_channel_id)

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


client.run("")