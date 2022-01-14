from asyncio.tasks import sleep
from core.extension import Extension
from airtable import Airtable
from discord.ext import tasks
from models.message import Message
from core.settings import Settings
import discord

class Air(Extension):
    def __init__(self, bot):
        self.bot = bot
        self.table = Airtable(
            self.bot.settings.base_id,
            self.bot.settings.table_name,
            self.bot.tokens.airtable
        )

        self.insert_queue = []
        self.delete_queue = []

        # starts update loop
        self.update.start()

    def insert(self, message):
        self.insert_queue.append(message)

    def delete(self, message):
        self.delete_queue.append(message)

    def fetch_role_data(self, message):
        if message['author_is_anonymous']: return

        guild = self.bot.fetch_guild(int(message['guild_id']))
        member = discord.utils.get(guild.members, id=int(message['author_id']))

        message['author_roles'] = []

        if member:
            message['author_nick'] = member.nick
            for role in member.roles:
                message['author_roles'].append({
                    'name': role.name,
                    'id': role.id
                })

    # inserts and deletes all messages in queue
    @tasks.loop(minutes=Settings().sync_time)
    async def update(self):
        while self.insert_queue:
            to_insert = self.insert_queue.pop()
            # exports message Document to dict and inserts in airtable
            record = self.table.insert(to_insert.export())
            to_insert.airtable_id = record['id']
            to_insert.save()
    
            await sleep(self.table.API_LIMIT)

        while self.delete_queue:
            to_delete = self.delete_queue.pop()
            to_delete.deleted = True
            to_delete.save()
            # exports message Document to dict and updates airtable (marks deleted)
            record = self.table.update(
                to_delete.airtable_id,
                to_delete.export(),
            )
            
            await sleep(self.table.API_LIMIT)


def setup(bot):
    cog = Air(bot)
    bot.add_cog(cog)
