import discord
from discord.ui import DynamicItem, Button, View
from discord.enums import ButtonStyle
from model import MessageModel

def construct_view(_id, items):
    view = View(timeout=None)
    for Item in items:
        view.add_item(Item(_id))
    
    return view

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
        print(msg.guild_id, guild)
        author = guild.get_member(msg.author_id)
        print(msg.author_id, author)
        await interaction.response.send_message(msg.to_json(), ephemeral=True)

        embed = discord.Embed(
            
        )

        await author.send("What is your consent level?", view=construct_view(self.id, [YesConsentButton, AnonymousConsentButton, NoConsentButton]))


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
        await interaction.response.send_message("no consent " + str(self.id), ephemeral=True)