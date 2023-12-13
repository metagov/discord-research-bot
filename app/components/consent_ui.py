import discord
from discord.ui import DynamicItem, Button, View
from discord.enums import ButtonStyle

from .functions import construct_view

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
        print("yes consent button callback")
        await interaction.response.send_message("yes consent " + str(self.id), ephemeral=True)


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
        print("anon consent button callback")
        await interaction.response.send_message("anon consent " + str(self.id), ephemeral=True)


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
        print("no consent button callback")
        await interaction.response.send_message("no consent " + str(self.id), ephemeral=True)

def construct_consent_view(_id):
    return construct_view(_id, [YesConsentButton, AnonymousConsentButton, NoConsentButton])