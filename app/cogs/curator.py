import discord
from discord.ext import commands

class CuratorCog(commands.Cog):

    def __init__(self, bot):
        print('Loaded Curator Cog')
        self.bot = bot

    def cog_unload(self):
        print('Unloaded Curator Cog')
    
    @commands.Cog.listener()
    async def on_message(self, message):
        ctx = await self.bot.get_context(message)
        # bot won't respond to it's own messages
        if message.author == self.bot.user:
            return

        # filters for direct messages
        if message.channel.id == message.author.dm_channel.id:
            text = message.content
            # filters for links to discord messages
            if text.startswith('https://discord.com/channels/'):
                # extract ids from the url
                parts = text.split('/')
                guild_id = int(parts[4])
                channel_id = int(parts[5])
                msg_id = int(parts[6])

                # attempting to retrieve message from the link
                guild = self.bot.get_guild(guild_id)
                if guild:
                    channel = guild.get_channel(channel_id)                    
                    if channel:
                        try:
                            message = await channel.fetch_message(msg_id)
                            await ctx.send(message.content)
                        except discord.errors.Forbidden as e:
                            if e.code == 50001:
                                await ctx.send("I couldn't access that channel")

                    else:
                        await ctx.send("Channel may have been deleted")
                else:
                    await ctx.send("I couldn't access that server")
                

def setup(bot):
    bot.add_cog(CuratorCog(bot))