from .functions import message_to_embed

def construct_approved_embed(msg):
    embed = message_to_embed(msg)
    embed.add_field(
        name="Curated By",
        value=msg.tagged_by_name,
        inline=False
    )

    return embed