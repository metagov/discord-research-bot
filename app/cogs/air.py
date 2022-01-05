from core.extension import Extension
from airtable import Airtable

class Air(Extension):
    def __init__(self, bot):
        self.bot = bot
        self.base_id = "appSOp4O7dyirWU8c"
        self.table_name = "MetaEth"
        self.table = Airtable(self.base_id, self.table_name, self.bot.tokens.airtable)

        print(self.table.get_all())

        self.table.insert({'id': "3492340"})

        # self.air_table.create(self.table_name, data = "test,one,three")


def setup(bot) -> None:
    cog = Air(bot)
    bot.add_cog(cog)
