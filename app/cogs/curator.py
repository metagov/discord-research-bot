import discord
from discord.ext import commands
from discord_components import ButtonStyle, Button, InteractionType

class CuratorCog(commands.Cog):

    def __init__(self, bot):
        print('Loaded Curator Cog')
        self.bot = bot

    def cog_unload(self):
        print('Unloaded Curator Cog')
    
    @commands.Cog.listener()
    async def on_message(self, msg):
        ctx = await self.bot.get_context(msg)
        # bot won't respond to it's own messages
        if msg.author == self.bot.user:
            return False
        
        if msg.channel.id != msg.author.dm_channel.id:
            return False

        text = msg.content
        # filters for links to discord messages
        if text.startswith('https://discord.com/channels/'):
            try:
                # extract ids from the url
                parts = text.split('/')
                guild_id = int(parts[4])
                channel_id = int(parts[5])
                msg_id = int(parts[6])
            except (ValueError):
                print('Bad argument')
                return False

            # attempting to retrieve message from the link
            guild = self.bot.get_guild(guild_id)
            if guild:
                channel = guild.get_channel(channel_id)                    
                if channel:
                    try:
                        linked_msg = await channel.fetch_message(msg_id)
                        
                    except discord.errors.Forbidden as error:
                        if error.code == 50001:
                            await ctx.send("I couldn't access that channel")
                            return False
                else:
                    await ctx.send("Channel may have been deleted")
                    return False
            else:
                await ctx.send("I couldn't access that server")
                return False
            
            color = int(int(ctx.author.discriminator) / 9999 * 0xffffff)
            color = discord.Colour.blue()

            info_embed = discord.Embed(
                title='Discord Cryptocurrency Research',
                description='test message',
                color=color
            )

            linked_msg_embed=discord.Embed(
                description=linked_msg.content, 
                color=color)
            linked_msg_embed.set_author(
                name=f"{ctx.author.display_name}#{ctx.author.discriminator}", 
                url=f"https://discord.com/users/{ctx.author.id}",
                icon_url=ctx.author.avatar_url
            )
            linked_msg_embed.set_footer(
                text='by pressing accept you consent for your anonymized message to published'
            )
            

            await ctx.send(embed=info_embed)
            sent_msg = await ctx.send(embed=linked_msg_embed,
                components=[[
                    Button(style=ButtonStyle.green, label="accept"),
                    Button(style=ButtonStyle.red, label="reject"),
                    Button(style=ButtonStyle.URL, label="join our server", url="https://discord.com"),
                ]]
            )
    
    @commands.Cog.listener()
    async def on_button_click(self, res):
        choice = res.component.label

        # if choice == 'accept':

        print(res.component.id)
        # print(res.component)

        # res.component.disabled(True)
            
        
        await res.respond(
            type=4, content=f"{res.component.label} pressed"
        )

def setup(bot):
    bot.add_cog(CuratorCog(bot))