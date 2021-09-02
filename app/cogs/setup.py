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
        name="setup"
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
        db.guild(ctx.guild).bridge_channel = ctx.channel
        
        db.channel(channel=ctx.channel).group = ctx.guild.name
        db.channel(channel=bridge).group = ctx.guild.name
        
        await ctx.reply("Done!")

    @cog_ext.cog_slash(
        name="airdrop"
    )
    async def airdrop(self, ctx):
        async for user in db.get_all_curators(self.bot):
            url = 'http://POAP.xyz/claim/' + db.pop_compensation_code()
            await user.send(f'Thank you for your help in advancing Crypto-Goverance research! As a token of our gratitude, please accept this badge that you can add to your crypto wallet! {url}')

        await ctx.reply('Done!')

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
                    
                    db.insert_compensation_codes(poap_codes)

                    return logger.info('Received file and saved it to memory')
                else:
                    return logger.debug('Message did not contain a .txt file')

def setup(bot):
    cog = SetupCog(bot)
    bot.add_cog(cog)