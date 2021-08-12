# from typing import Generator, Optional
# from discord.channel import TextChannel
# from discord.ext import commands
# from database import is_admin
# import discord

# class BridgeCog(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot

#     @commands.Cog.listener()
#     async def on_message(self, message):
#         group = self.get_group(message.channel)
#         if group is not None and message.author != self.bot.user:
#             await self.replicate_in_group(message, group)
    
#     async def replicate_in_group(self, message, group) -> None:
#         for channel in self.get_channels_in_group(group):
#             if channel != message.channel:
#                 await channel.send(content='{0.name}#{0.author}> {1}'.format(
#                     message.author, message.content))

#     def get_channels_in_group(self, group) -> Generator[TextChannel]:
#         yield None
    
#     async def get_group(self, channel) -> Optional[str]:
#         return None
    

# def setup(bot):
#     cog = BridgeCog(bot)
#     bot.add_cog(cog)
