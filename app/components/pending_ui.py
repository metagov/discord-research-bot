import discord
from discord.ui import DynamicItem, Button, View
from discord.enums import ButtonStyle
from models import MessageModel, UserModel, ConsentStatus, MessageStatus
from .functions import construct_view, message_to_embed
from .consent_ui import construct_consent_view, construct_removal_view, construct_consent_embed, construct_removal_embed


async def handle_forbidden(interaction, e):
    if e.code == 50007:
        await interaction.response.send_message("This user has their DMs closed, and they have been sent a message informing them. Pressing request again will retry this request, so please use sparingly.")
    else:
        raise e

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
        # msg.requested_at =
        msg.save()

        print(interaction.created_at, interaction.expires_at)

        user = UserModel.objects(pk=msg.author_id).first()

        guild = interaction.client.get_guild(msg.guild_id)
        author = guild.get_member(msg.author_id)

        print(f"Message {msg.id} requested by user {interaction.user.name}")

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

                
        # user has opted-in or opted-in anonymously
        elif (user.consent == ConsentStatus.YES) or (user.consent == ConsentStatus.ANONYMOUS):
            msg.status = MessageStatus.APPROVED
            msg.save()

            try:
                await author.send(
                    embed=construct_removal_embed(msg, user.consent),
                    view=construct_removal_view(self.id)
                )
            
            except discord.errors.Forbidden as e:
                await handle_forbidden(interaction, e)
                

        # user has opted-out
        elif user.consent == ConsentStatus.NO:
            msg.status = MessageStatus.REJECTED
            msg.save()

            await interaction.response.send_message("This user has refused consent, no request has been sent.")
            return
        
        updated_view = View.from_message(interaction.message, timeout=None)

        updated_view.children[0].label = "Pending"
        updated_view.children[0].disabled = True
        updated_view.remove_item(updated_view.children[1])

        await interaction.message.edit(view=updated_view)
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

def construct_pending_embed(msg, name):
    embed = message_to_embed(msg)
    embed.add_field(
        name="Curated By",
        value=name,
        inline=False
    )

    return embed

def construct_pending_view(_id):
    return construct_view(_id, [RequestPendingButton, CancelPendingButton])