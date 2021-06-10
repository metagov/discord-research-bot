import discord
from discord.ext import commands

class BridgeCog(commands.Cog):

    def __init__(self, bot):
        print('Loaded Bridge Cog')
        self.bot = bot

    def cog_unload(self):
        print('Unloaded Bridge Cog')

    @commands.Cog.listener()
    async def on_message(self, message):
        ctx = await self.bot.get_context(message)

        if message.author == self.bot.user:
            return

        # maps discord discriminator to a hex color value
        color = int(int(ctx.author.discriminator) / 9999 * 0xffffff)

        embed=discord.Embed(
            description=message.content, 
            color=color)
        embed.set_author(
            name=f"{ctx.author.display_name}#{ctx.author.discriminator}", 
            url=f"https://discord.com/users/{ctx.author.id}",
            icon_url=ctx.author.avatar_url
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def color(self, ctx):
        await ctx.send(ctx.author.color)

def setup(bot):
    bot.add_cog(BridgeCog(bot))