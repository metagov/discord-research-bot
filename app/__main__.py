from core.telescope import Telescope
from core.settings import Settings
from core.responses import Responses
from core.helpers import get_token, check_observatory_set
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

check_observatory_set(telescope)

connect(telescope.settings.database)
telescope.run()
