import discord
from discord.ui import DynamicItem, Button, View
from discord.enums import ButtonStyle
from models import MessageModel, UserModel, ConsentStatus, MessageStatus
from .functions import construct_view, message_to_embed, handle_forbidden
from .consent_ui import construct_consent_view, construct_consent_embed, approve_message, reject_message
from datetime import datetime


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

        msg.status = MessageStatus.REQUESTED
        msg.requested_by_id = interaction.user.id
        msg.requested_by_name = interaction.user.name
        msg.requested_at = datetime.utcnow()
        msg.save()

        user = UserModel.objects(pk=msg.author_id).first()

        guild = interaction.client.get_guild(msg.guild_id)
        author = guild.get_member(msg.author_id)

        print(f"Message {msg.id} requested by user {interaction.user.name}")

        updated_view = View.from_message(interaction.message, timeout=None)
        updated_view.children[0].disabled = True
        updated_view.remove_item(updated_view.children[1])
        await interaction.message.edit(view=updated_view)

        # user is unknown to system or has not set consent status
        if (user is None) or (user.consent == ConsentStatus.UNDECIDED):
            user = UserModel(
                id = msg.author_id,
                name = msg.author_name
            )

            user.save()

            try:
                await author.send(
                    embed=construct_consent_embed(msg),
                    view=construct_consent_view(self.id)
                )
            
            except discord.errors.Forbidden as e:
                await handle_forbidden(interaction, e)

            updated_view.children[0].label = "Pending"
            updated_view.children[0].style = ButtonStyle.secondary
            await interaction.message.edit(view=updated_view)
                
        # user has opted-in or opted-in anonymously
        elif (user.consent == ConsentStatus.YES) or (user.consent == ConsentStatus.ANONYMOUS):
            try:
                await approve_message(msg, author, interaction.client)
            except discord.errors.Forbidden as e:
                await handle_forbidden(interaction, e)
                
        # user has opted-out
        elif user.consent == ConsentStatus.NO:
            await reject_message(msg, author, interaction.client)
        
        await interaction.response.defer()
            

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

def construct_pending_embed(msg):
    embed = message_to_embed(msg)
    embed.add_field(
        name="Curated By",
        value=msg.tagged_by_name,
        inline=False
    )

    return embed

def construct_pending_view(_id):
    return construct_view(_id, [RequestPendingButton, CancelPendingButton])