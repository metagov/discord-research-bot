import discord
from discord.ui import View
from models import SatelliteModel, MessageModel
from datetime import timezone

def construct_view(_id, items):
    view = View(timeout=None)
    for Item in items:
        view.add_item(Item(_id))
    
    return view

def message_to_embed(message):
    msg_model = MessageModel.objects(pk=message.id).first()

    timestamp = (message.edited_at or message.created_at).replace(tzinfo=timezone.utc)

    embed = discord.Embed(
        description=message.content,
        timestamp=timestamp
    )

    embed.set_author(
        name=message.author_name,
        icon_url=message.author_avatar_url,
        url=message.jump_url
    )

    embed.set_footer(text=f"{message.guild_name} - #{message.channel_name} • Tagged by {msg_model.tagged_by_name}")

    return embed

async def get_interface(msg, client):
    satellite = SatelliteModel.objects(id=msg.guild_id).first()
    pending_channel = client.get_channel(satellite.pending_channel_id)
    return await pending_channel.fetch_message(msg.interface_id)

async def handle_forbidden(interaction, e):
    if e.code == 50007:
        await interaction.response.send_message("This user has their DMs closed, and they have been sent a message informing them. Pressing request again will retry this request, so please use sparingly.")
    else:
        raise e