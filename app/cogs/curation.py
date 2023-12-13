import discord
from discord import app_commands
from discord.ext import commands
from models import SatelliteModel, MessageModel
import components

class Curation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if not reaction.guild_id: return
        if reaction.emoji.name != self.bot.settings.emoji: return

        channel = self.bot.get_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)

        satellite = SatelliteModel.objects(id=message.guild.id).first()
        pending_channel = self.bot.get_channel(satellite.pending_channel_id)

        msg = MessageModel(
            id                  = message.id,
            channel_id          = message.channel.id,
            channel_name        = message.channel.name,
            guild_id            = message.guild.id,
            guild_name          = message.guild.name,
            author_id           = message.author.id,
            author_name         = message.author.name,
            author_avatar_url   = message.author.display_avatar.url,
            content             = message.content,
            attachments         = message.attachments,

            created_at          = message.created_at,
            edited_at           = message.edited_at,
            jump_url            = message.jump_url
        )

        msg.save()

        embed = components.message_to_embed(msg)
        embed.add_field(
            name="Curated By",
            value=reaction.member.global_name,
            inline=False
        )

        pending_message = await pending_channel.send(embed=embed, view=components.construct_pending_view(message.id)
        )
