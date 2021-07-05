import discord
from discord.ext import commands
from discord_components import ButtonStyle, Button, InteractionType

import core

class OwnerCog(commands.Cog):

    def __init__(self, bot):
        print('Loaded Owner Cog')
        self.bot = bot

    def cog_unload(self):
        print('Unloaded Onwer Cog')

    @commands.command(aliases=['m'])
    async def manage(self, ctx, cog):
        if cog not in core.extensions:
            if ('cogs.' + cog) not in core.extensions:
                return
        else:
            cog = cog[5:]

        emb = discord.Embed(
            title=cog,
            description='cog management panel',
            color=discord.Colour.blue()
        )

        await ctx.send(embed=emb, components=[[
            Button(style=ButtonStyle.blue, label='reload'),
            Button(style=ButtonStyle.green, label='load'),
            Button(style=ButtonStyle.red, label='unload')
        ]])

    @commands.Cog.listener()
    async def on_button_click(self, res):

        cog = 'cogs.' + res.raw_data['d']['message']['embeds'][0]['title']
        action = res.component.label

        print(cog, action)

        if action == 'reload':
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
            await res.respond(type = InteractionType.ChannelMessageWithSource, content='Reloaded ' + cog)
        elif action == 'load':
            self.bot.load_extension(cog)
            await res.respond(type = InteractionType.ChannelMessageWithSource, content='Loaded ' + cog)
        elif action == 'unload':
            self.bot.unload_extension(cog)
            await res.respond(type = InteractionType.ChannelMessageWithSource, content='Unloaded ' + cog)
       

    @commands.command()
    async def reset(self, ctx):
        for cog in ['cogs.owner', 'cogs.curator',]:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        await ctx.send('Done!')

        
    @commands.command()
    async def ping(self, ctx):
        await ctx.send('pong')

def setup(bot):
    bot.add_cog(OwnerCog(bot))