import discord
from discord.ext import commands
from discord.ui import Button, View, DynamicItem

class RequestPendingButton(DynamicItem[Button], template=r'request:pending:(?P<id>[0-9]+)'):
    def __init__(self, message_id):
        super().__init__(
            Button(
                label="Request",
                style=discord.ButtonStyle.success,
                custom_id=f"request:pending:{message_id}"
            )
        )
        self.message_id = message_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match,):
        message_id = int(match['id'])
        print("from_custom_id", message_id)
        return cls(message_id)
    
    async def callback(self, interaction):
        await interaction.response.send_message(str(self.message_id), ephemeral=True)

class PersistentViewBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=commands.when_mentioned_or('$'), intents=intents)

    async def setup_hook(self):
        self.add_dynamic_items(RequestPendingButton)

    async def on_ready(self):
        print("logged in")

bot = PersistentViewBot()

@bot.command()
async def dynamic_button(ctx):
    view = View(timeout=None)
    view.add_item(RequestPendingButton(ctx.author.id))
    await ctx.send("here is your button", view=view)

@bot.command()
async def not_mine(ctx):
    msg = await ctx.channel.fetch_message(1182315233969197066)

bot.run("ODUyMjk2MDYyNDc1MTczOTA5.GAOcMC.QrUDvSOmaAbSVZrswSKrEOqHpgNDl8zI-JuJN8")