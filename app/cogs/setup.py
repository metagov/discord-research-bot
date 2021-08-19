from discord import guild
from discord.ext import commands
from discord.ext.commands import cog
from discord_slash import cog_ext
from constants import CENTRAL_HUB_ID
from database import *


logger = logging.getLogger(__name__)

class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @cog_ext.cog_slash(
        name="setup",
        guild_ids=[474736509472473088, 870551183339696138, 870551292525809684,
                   872936378118324235]
    )
    async def setup(self, ctx):
        if not db.user(user=ctx.author).is_admin:
            return await ctx.send('Insufficient permissions!')

        observatory = self.bot.get_guild(CENTRAL_HUB_ID)
        
        if ctx.guild == observatory:
            await ctx.send("Setup can only be run in Satellite Servers.")
            return

        # creating category and channels in Observatory
        category = await observatory.create_category(ctx.guild.name)
        bridge   = await observatory.create_text_channel("Bridge", category=category)
        pending  = await observatory.create_text_channel("Pending Messages", category=category)
        approved = await observatory.create_text_channel("Approved Messages", category=category)

        # setting channel ids for curation process
        db.guild(ctx.guild).pending_channel = pending
        db.guild(ctx.guild).approved_channel = approved
        
        db.channel(channel=ctx.channel).group = ctx.guild.name
        db.channel(channel=bridge).group = ctx.guild.name
        
        await ctx.reply("Done!")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        # downloads text file containing POAP claim urls
        if str(payload.emoji) == '🔗':
            if message.attachments == []:
                return logger.debug('Message did not contain a file attachment')
            else:
                attachment = message.attachments[0]
                if attachment.filename.endswith('.txt'):
                    await attachment.save('temp.txt')

                    poap_codes = []
                    url_pattern = 'http://POAP.xyz/claim/'
                    with open('temp.txt') as f:
                        for line in f.readlines():
                            if line.startswith(url_pattern):
                                # extracting code substring to store in db
                                poap_codes.append(line[len(url_pattern):].rstrip())
                    
                    print(poap_codes)

                    return logger.info('Received file and saved it to memory')
                else:
                    return logger.debug('Message did not contain a .txt file')

def setup(bot):
    cog = SetupCog(bot)
    bot.add_cog(cog)