from rich.logging import RichHandler
from rich.traceback import install
import logging


def init() -> None:
    install(show_locals=True)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(message)s',
        datefmt='[%X]',
        handlers=[RichHandler(markup=True, rich_tracebacks=True)],
    )

    for name in ['asyncio', 'discord', 'discord_slash']:
        logging.getLogger(name).setLevel(logging.INFO)
