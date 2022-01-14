from asyncio.tasks import sleep
from core.extension import Extension
from airtable import Airtable
from discord.ext import tasks
from models.message import Message
from models.comment import Comment
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

    async def fetch_role_data(self, message):
        if message['author_is_anonymous']: return

        guild = await self.bot.fetch_guild(int(message['guild_id']))
        member = discord.utils.get(guild.members, id=int(message['author_id']))

        message['author_roles'] = None

        if member:
            message['author_nick'] = member.nick
            if member.roles:
                message['author_roles'] = []
                for role in member.roles:
                    message['author_roles'].append({
                        'name': role.name,
                        'id': role.id
                    })
        else:
            print("failed to get members list")
        


    def fetch_comments(self, message_json, message_doc):
        message_json['researcher_comments'] = Comment.retrieve_comments(message_doc)

    # inserts and deletes all messages in queue
    @tasks.loop(seconds=5)
    async def update(self):
        while self.insert_queue:
            to_insert = self.insert_queue.pop()

            message_json = to_insert.export()

            await self.fetch_role_data(message_json)
            self.fetch_comments(message_json, to_insert)

            print(message_json)

            # exports message Document to dict and inserts in airtable
            record = self.table.insert(message_json)
            to_insert.airtable_id = record['id']
            to_insert.save()

            await sleep(self.table.API_LIMIT)

        while self.delete_queue:
            to_delete = self.delete_queue.pop()
            to_delete.deleted = True
            to_delete.save()

            message_json = to_delete.export()

            await self.fetch_role_data(message_json)
            self.fetch_comments(to_delete)

            # exports message Document to dict and updates airtable (marks deleted)
            record = self.table.update(
                to_delete.airtable_id,
                message_json,
            )
            
            await sleep(self.table.API_LIMIT)


def setup(bot):
    cog = Air(bot)
    bot.add_cog(cog)
