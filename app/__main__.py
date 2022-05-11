from core.telescope import Telescope
from core.settings import Settings
from core.helpers import get_token
from mongoengine import connect
from dotenv import load_dotenv
from core import log


log.init()
load_dotenv()

telescope = Telescope(
    discord_token=get_token('DISCORD_TOKEN'),
    airtable_token=get_token('AIRTABLE_TOKEN'),
    settings=Settings(),
)

connect(telescope.settings.database)
telescope.run()
