from quart import Quart, render_template
from core.settings import Settings
from mongoengine import connect
import logging
import asyncio

from models.alternate import Alternate
from models.message import Message
from models.channel import Channel
from models.comment import Comment
from models.special import Special
from models.member import Member
from models.guild import Guild
from models.user import User

HOST = '0.0.0.0'
PORT = 8080

app = Quart(__name__)
app.logger.setLevel(logging.DEBUG)
settings = Settings()
context = {}


def update() -> None:
    app.logger.info('Brace for impact, we are updating!')

    global context
    context = {
        'alternates':   Alternate.objects.all(),
        'messages':     Message.objects.all(),
        'channels':     Channel.objects.all(),
        'comments':     Comment.objects.all(),
        'specials':     Special.objects.all(),
        'members':      Member.objects.all(),
        'guilds':       Guild.objects.all(),
        'users':        User.objects.all(),
    }


def register_update_loop() -> None:
    update()  # Call once in the beginning.
    loop = asyncio.get_event_loop()
    loop.call_later(3600, update)


@app.before_serving
async def before_serving() -> None:
    register_update_loop()


@app.route('/')
async def index() -> None:
    update()  # TODO: Remove when done debugging.
    return await render_template('index.html', **context)


connect(settings.database)
app.run(HOST, PORT)
