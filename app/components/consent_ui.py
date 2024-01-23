import discord
from discord.ui import DynamicItem, Button, View
from discord.enums import ButtonStyle

from .functions import construct_view
from models import UserModel, ConsentStatus

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
        user = UserModel.objects(pk=interaction.user.id).first()
        user.consent = ConsentStatus.YES
        user.save()

        updated_view = View.from_message(interaction.message, timeout=None)
        for item in updated_view.children:
            item.disabled = True
            
        await interaction.message.edit(view=updated_view)
        await interaction.response.send_message("You have opted-in to post collection!")


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
        user = UserModel.objects(pk=interaction.user.id).first()
        user.consent = ConsentStatus.ANONYMOUS
        user.save()

        updated_view = View.from_message(interaction.message, timeout=None)
        for item in updated_view.children:
            item.disabled = True
            
        await interaction.message.edit(view=updated_view)
        await interaction.response.send_message("You have opted-in to anonymous post collection!")


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
        user = UserModel.objects(pk=interaction.user.id).first()
        user.consent = ConsentStatus.NO
        user.save()

        updated_view = View.from_message(interaction.message, timeout=None)
        for item in updated_view.children:
            item.disabled = True
            
        await interaction.message.edit(view=updated_view)
        await interaction.response.send_message("You have opted-out of post collection.")

def construct_consent_view(_id):
    return construct_view(_id, [YesConsentButton, AnonymousConsentButton, NoConsentButton])