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
        print(reaction)
        channel = self.bot.get_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)

        satellite = SatelliteModel.objects(id=message.guild.id).first()
        # print(satellite)
        pending_channel = self.bot.get_channel(satellite.pending_channel_id)

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
            embed=embed, view=components.construct_pending_view(message.id)
        )

        if (reaction.guild_id is not None) and (reaction.emoji.name == "🔭"):
            print(f"got telescope reaction on {reaction.guild_id}:{reaction.channel_id}:{reaction.message_id}")
