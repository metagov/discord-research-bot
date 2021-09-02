import json
from discord.ext import commands
from discord_slash.utils.manage_commands import create_option
from constants import DEVELOPER_IDS
from database import MESSAGES_TABLE_NAME, db, is_admin
from pathlib import Path, PurePath
from discord_slash import cog_ext
from datetime import datetime
import discord

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name='admin',
        description=('Makes the owner of the bot an admin or makes/unmakes'
            'someone else an admin.'),
        options=[
            create_option(
                name='user',
                description='The user to add or remove from the admin list.',
                option_type=6, # 6 means user.
                required=False
            )
        ]
    )
    async def _admin(self, ctx, user: discord.User=None):
        if user is None and ctx.author.id in DEVELOPER_IDS:
            # Give developer admin.
            db.user(ctx.author).is_admin = True
            return await ctx.reply('Done!')
        
        # Check if author is an admin.
        if not is_admin(ctx):
            return await ctx.reply('You are not an admin!')

        db.user(user).is_admin = not db.user(user).is_admin
        await ctx.reply('Done!')

    @cog_ext.cog_slash(
        name='export',
        description='Gives the callee all of the curated data.'
    )
    async def export(self, ctx):
        """Gives the callee all of the curated data."""
        # Check if author is an admin.
        if not is_admin(ctx):
            return await ctx.reply('Insuffient permissions!')

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
        

        # Write to a file.
        filename = 'export.json'
        with open(filename, 'w') as file:
            json.dump(exported, file, indent=4)

        # Send to callee.
        with open(filename, 'r') as file:
            await ctx.send(file=discord.File(file))

def setup(bot):
    cog = AdminCog(bot)
    bot.add_cog(cog)
