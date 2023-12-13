import discord
from discord.ui import DynamicItem, Button, View
from discord.enums import ButtonStyle
from models import MessageModel
from .functions import construct_view, message_to_embed
from .consent_ui import construct_consent_view

class DisabledRequestPendingButton(DynamicItem[Button], template=r'request:pending:([0-9]+)'):
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

        updated_view = View.from_message(interaction.message, timeout=None)
        updated_view.children[0].disabled = True

        await interaction.message.edit(view=updated_view)

        guild = interaction.client.get_guild(msg.guild_id)
        author = guild.get_member(msg.author_id)
        await interaction.response.send_message(msg.to_json(), ephemeral=True)

        embed = message_to_embed

        await author.send("What is your consent level?", view=construct_consent_view(self.id))


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
        await interaction.response.send_message(str(self.id), ephemeral=True)


def construct_pending_view(_id):
    return construct_view(_id, [RequestPendingButton, CancelPendingButton])