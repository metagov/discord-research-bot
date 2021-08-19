import json
from discord.ext import commands
from database import MESSAGES_TABLE_NAME, db, is_admin
from pathlib import Path, PurePath
from datetime import datetime
import discord

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def bootstrap(self, ctx):
        """Makes the owner of the bot an admin."""
        db.user(ctx.author).is_admin = True
        await ctx.message.add_reaction('👍')
    
    @commands.command()
    @commands.check(is_admin)
    async def admin(self, ctx, user: discord.User=None):
        """Makes a user an admin or demotes them if they are an admin."""
        db.user(user).is_admin = not db.user(user).is_admin
        await ctx.message.add_reaction('👍')

    @commands.command()
    @commands.check(is_admin)
    async def export(self, ctx):
        """Gives the callee all of the curated data."""
        if ctx.guild:
            return await ctx.reply('This command must be run in DMs.')

        # Show that the command was successfully received.
        await ctx.message.add_reaction('👍')

        exported = []
        for document in db.handle.table(MESSAGES_TABLE_NAME):

            # Add all comments to this message.
            if 'comments' not in document:
                document['comments'] = []
            
            message = db.message(
                channel_id=document.get('original_cid'),
                message_id=document.get('original_mid')
            )

            for comment in message.comments:
                document['comments'].append(comment)
            
            # Add to resulting list.
            exported.append(document)
        
        # Make the folder if it does not exist.
        folder = Path('exports')
        folder.mkdir(exist_ok=True)

        # Write to a file.
        filename = folder / f'{datetime.utcnow().isoformat()}.json'
        with open(filename, 'w') as file:
            json.dump(exported, file, indent=4)

        # Send to callee.
        with open(filename, 'r') as file:
            await ctx.send(file=discord.File(file))

def setup(bot):
    cog = AdminCog(bot)
    bot.add_cog(cog)
