from dotenv import load_dotenv
import os
from mongoengine import connect
from telescope import TelescopeBot

load_dotenv()
connect("telescope")

bot_token = os.environ.get('DISCORD_BOT_TOKEN', None)

if not bot_token:
    print("Missing Discord bot token in environment variable")

bot = TelescopeBot()
bot.run(bot_token)