import discord
from discord.ui import DynamicItem, Button, View
from discord.enums import ButtonStyle
from models import MessageModel
from core.responses import responses
from .functions import construct_view, message_to_embed
from .consent_ui import construct_consent_view

class DisabledRequestPendingButton(DynamicItem[Button], template=r'disabledrequest:pending:([0-9]+)'):
    def __init__(self, _id):
        super().__init__(
            Button(
                label="Request",
                style=ButtonStyle.success,
                custom_id=f"disabledrequest:pending:{_id}"
            )
        )
        self.id = _id

    @classmethod
    async def from_custom_id(cls, interaction, item, match,):
        _id = int(match[1])
        return cls(_id)

class RequestPendingButton(DynamicItem[Button], template=r'request:pending:([0-9]+)'):
    def __init__(self, _id):
        super().__init__(
            Button(
                label="Request",
                style=ButtonStyle.success,
                custom_id=f"request:pending:{_id}"
            )
        )
        self.id = _id

    @classmethod
    async def from_custom_id(cls, interaction, item, match,):
        _id = int(match[1])
        return cls(_id)
    
    async def callback(self, interaction):        
        msg = MessageModel.objects(pk=self.id).first()

        guild = interaction.client.get_guild(msg.guild_id)
        author = guild.get_member(msg.author_id)

        print(msg.to_json())

        embed = message_to_embed(msg)
        embed.add_field(
            name="Introduction",
            inline=False,
            value=(responses.introduction_message),
        )

        embed.add_field(
            name="Permission",
            inline=False,
            value=(responses.permission_message),
        )

        embed.add_field(
            name="Consent Message",
            inline=False,
            value=(responses.consent_message)
        )

        embed.add_field(
            name="Get Involved",
            inline=False,
            value=(responses.get_involved_message)
        )

        try:
            await author.send(embed=embed, view=construct_consent_view(self.id))

            updated_view = View.from_message(interaction.message, timeout=None)

            updated_view.children[0].label = "Pending"
            updated_view.children[0].disabled = True
            updated_view.remove_item(updated_view.children[1])

            await interaction.message.edit(view=updated_view)
            await interaction.response.defer()
            
        except discord.errors.Forbidden as e:
            if e.code == 50007:
                await interaction.response.send_message("This user has their DMs closed, and they have been sent a message informing them. Pressing request again will retry this request, so please use sparingly.")
            else:
                raise e


class CancelPendingButton(DynamicItem[Button], template=r'cancel:pending:([0-9]+)'):
    def __init__(self, _id):
        super().__init__(
            Button(
                label="Cancel",
                style=ButtonStyle.secondary,
                custom_id=f"cancel:pending:{_id}"
            )
        )
        self.id = _id

    @classmethod
    async def from_custom_id(cls, interaction, item, match,):
        _id = int(match[1])
        return cls(_id)
    
    async def callback(self, interaction):
        await interaction.message.delete()


def construct_pending_view(_id):
    return construct_view(_id, [RequestPendingButton, CancelPendingButton])