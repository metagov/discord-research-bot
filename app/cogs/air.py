from core.extension import Extension
from airtable import Airtable
from discord.ext import tasks

class Air(Extension):
    def __init__(self, bot):
        self.bot = bot
        self.base_id = "appSOp4O7dyirWU8c"
        self.table_name = "Test"
        self.table = Airtable(
            self.bot.settings.base_id, 
            self.bot.settings.table_name, 
            self.bot.tokens.airtable
        )

        self.insert_queue = []
        self.delete_queue = []

        # self.air_table.create(self.table_name, data = "test,one,three")

        self.update.start()
    
    def insert(self, message):
        self.insert_queue.append(message)

    def delete(self, message):
        self.delete_queue.append(message)

    @tasks.loop(seconds=5)
    async def update(self):
        while self.insert_queue:
            to_insert = self.insert_queue.pop()
            record = self.table.insert(to_insert)
            to_insert.airtable_id = record['id']
            to_insert.save()

        while self.delete_queue:
            to_delete = self.delete_queue.pop()
            to_delete.deleted = True
            record = self.table.update(to_delete.airtable_id, to_delete)
            
            to_delete.save()



def setup(bot):
    cog = Air(bot)
    bot.add_cog(cog)
