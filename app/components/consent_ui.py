import discord
from discord.ui import DynamicItem, Button, View
from discord.enums import ButtonStyle

from .functions import construct_view, message_to_embed, get_interface
from .approved_ui import construct_approved_embed
from core.responses import responses
from models import MessageModel, UserModel, SatelliteModel, ConsentStatus, MessageStatus
from core.settings import settings
from datetime import datetime, timedelta


class YesConsentButton(DynamicItem[Button], template=r'yes:consent:([0-9]+)'):
    def __init__(self, _id):
        super().__init__(
            Button(
                label="Yes",
                style=ButtonStyle.success,
                custom_id=f"yes:consent:{_id}"
            )
        )
        self.id = _id

    @classmethod
    async def from_custom_id(cls, interaction, item, match,):
        _id = int(match[1])
        return cls(_id)
    
    async def callback(self, interaction):
        msg = MessageModel.objects(pk=self.id).first()
        user = UserModel.objects(pk=interaction.user.id).first()
        user.consent = ConsentStatus.YES
        user.save()

        updated_view = View.from_message(interaction.message, timeout=None)
        for item in updated_view.children:
            item.disabled = True
            
        await interaction.message.edit(view=updated_view)
        await interaction.response.send_message("You have opted-in to post collection!")

        await approve_message(msg, interaction.user, interaction.client)


class AnonymousConsentButton(DynamicItem[Button], template=r'anon:consent:([0-9]+)'):
    def __init__(self, _id):
        super().__init__(
            Button(
                label="Yes, anonymously",
                style=ButtonStyle.success,
                custom_id=f"anon:consent:{_id}"
            )
        )
        self.id = _id

    @classmethod
    async def from_custom_id(cls, interaction, item, match,):
        _id = int(match[1])
        return cls(_id)
    
    async def callback(self, interaction):
        msg = MessageModel.objects(pk=self.id).first()
        user = UserModel.objects(pk=interaction.user.id).first()
        user.consent = ConsentStatus.ANONYMOUS
        user.save()

        updated_view = View.from_message(interaction.message, timeout=None)
        for item in updated_view.children:
            item.disabled = True
            
        await interaction.message.edit(view=updated_view)
        await interaction.response.send_message("You have opted-in to anonymous post collection!")

        await approve_message(msg, interaction.user, interaction.client)


class NoConsentButton(DynamicItem[Button], template=r'no:consent:([0-9]+)'):
    def __init__(self, _id):
        super().__init__(
            Button(
                label="No",
                style=ButtonStyle.danger,
                custom_id=f"no:consent:{_id}"
            )
        )
        self.id = _id

    @classmethod
    async def from_custom_id(cls, interaction, item, match,):
        _id = int(match[1])
        return cls(_id)
    
    async def callback(self, interaction):
        msg = MessageModel.objects(pk=self.id).first()
        user = UserModel.objects(pk=interaction.user.id).first()
        user.consent = ConsentStatus.NO
        user.save()

        updated_view = View.from_message(interaction.message, timeout=None)
        for item in updated_view.children:
            item.disabled = True
            
        await interaction.message.edit(view=updated_view)
        await interaction.response.send_message("You have opted-out of post collection.")

        await reject_message(msg, interaction.user, interaction.client)


class RemoveConsentButton(DynamicItem[Button], template=r'remove:consent:([0-9]+)'):
    def __init__(self, _id):
        super().__init__(
            Button(
                label="Remove",
                style=ButtonStyle.danger,
                custom_id=f"remove:consent:{_id}"
            )
        )
        self.id = _id

    @classmethod
    async def from_custom_id(cls, interaction, item, match,):
        _id = int(match[1])
        return cls(_id)
    
    async def callback(self, interaction):
        updated_view = View.from_message(interaction.message, timeout=None)
        updated_view.children[0].disabled = True

        msg = MessageModel.objects(pk=self.id).first()
            
        await interaction.message.edit(view=updated_view)

        success = await retract_message(msg, interaction.user, interaction.client)

        if success:
            await interaction.response.send_message("You have removed this post from the dataset.")
        else:
            await interaction.response.send_message("The review period for this message has passed, please contact researchers directly if you wish to exclude your message from the dataset.")


def construct_consent_embed(msg):
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

    return embed

def construct_removal_embed(msg, anonymous):
    opt_in_status = "You are currently opted-in" + "." if anonymous else " anonymously."

    embed = message_to_embed(msg)
    embed.add_field(
        name="Removal",
        value=(responses.prompt_delete_message.format(opt_in_status))
    )

    return embed

def construct_consent_view(_id):
    return construct_view(_id, [YesConsentButton, AnonymousConsentButton, NoConsentButton])

def construct_removal_view(_id):
    return construct_view(_id, [RemoveConsentButton])

async def approve_message(msg, user, client):
    user_model = UserModel.objects(pk=msg.author_id).first()
    
    msg.status = MessageStatus.APPROVED
    msg.approved_at = datetime.utcnow()
    # TODO: change to days
    msg.locks_at = datetime.utcnow() + timedelta(seconds=settings.retraction_day_limit)
    msg.anonymous = (user_model.consent == ConsentStatus.ANONYMOUS)
    msg.save()

    await user.send(
        embed=construct_removal_embed(msg, msg.anonymous),
        view=construct_removal_view(msg.id)
    )

    interface = await get_interface(msg, client)

    updated_view = View.from_message(interface)
    updated_view.children[0].label = "Approved"
    updated_view.children[0].style = ButtonStyle.success

    await interface.edit(view=updated_view)

async def reject_message(msg, user, client):
    msg.status = MessageStatus.REJECTED
    msg.rejected_at = datetime.utcnow()
    msg.save()

    interface = await get_interface(msg, client)

    updated_view = View.from_message(interface)
    updated_view.children[0].label = "Rejected"
    updated_view.children[0].style = ButtonStyle.danger

    await interface.edit(view=updated_view)

async def retract_message(msg, user, client):
    if datetime.utcnow() < msg.locks_at:
        msg.status = MessageStatus.RETRACTED
        msg.retracted_at = datetime.utcnow()
        msg.save()

        interface = await get_interface(msg, client)

        updated_view = View.from_message(interface)
        updated_view.children[0].label = "Retracted"
        updated_view.children[0].style = ButtonStyle.danger

        await interface.edit(view=updated_view)
        return True
    
    else:
        return False