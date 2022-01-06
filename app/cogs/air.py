from core.extension import Extension
from airtable import Airtable
from discord.ext import tasks
from models.message import Message


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

        self.update.start()

    def insert(self, message) -> None:
        self.insert_queue.append(message)

    def delete(self, message) -> None:
        self.delete_queue.append(message)

    @tasks.loop(seconds=5)
    async def update(self) -> None:
        # for document in Message.objects:
        #     if document.airtable_id:
        #         self.delete(document)

        while self.insert_queue:
            to_insert = self.insert_queue.pop()
            record = self.table.insert(to_insert.export())
            to_insert.airtable_id = record['id']
            to_insert.save()

        while self.delete_queue:
            to_delete = self.delete_queue.pop()
            to_delete.deleted = True
            to_delete.save()
            record = self.table.update(
                to_delete.airtable_id,
                to_delete.export(),
            )


def setup(bot):
    cog = Air(bot)
    bot.add_cog(cog)
