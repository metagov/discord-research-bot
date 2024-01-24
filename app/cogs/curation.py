import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from models import SatelliteModel, MessageModel, MessageStatus
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

        guild_id = message.guild.id
        satellite = SatelliteModel.objects(id=guild_id).first()

        if not satellite:
            print(f"Satellite for guild {guild_id} not setup yet, ignoring reaction")
            return

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
            jump_url            = message.jump_url,

            status              = MessageStatus.TAGGED,

            tagged_by_id        = reaction.member.id,
            tagged_by_name      = reaction.member.name,
            tagged_at           = datetime.utcnow()
        )

        msg.save()

        print(f"Message {message.id} tagged by user {message.author.name}")

        await pending_channel.send(
            embed=components.construct_pending_embed(msg),
            view=components.construct_pending_view(message.id)
        )