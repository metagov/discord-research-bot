import json


class Settings:
    DEFAULT_FILENAME = 'settings.json'
    DEFAULT_SETTINGS = {
        'database': 'development',
        'observatory': 0,
        'guilds': [],
        'global': False,
        'base_id': '',
        'table_name': '',
        'sync_time': 10
    }

    def __init__(self) -> None:
        self.load()

    def load(self) -> None:
        self.clear()

        try:
            # Ask for forgiveness, not permission.
            with open(self.DEFAULT_FILENAME, 'r') as file:
                changes = json.load(file)
                self.__dict__.update(changes)
        except FileNotFoundError:
            self.save()

    def save(self) -> None:
        with open(self.DEFAULT_FILENAME, 'w') as file:
            json.dump(self.__dict__, file, indent=4)

    def clear(self) -> None:
        self.__dict__ = self.DEFAULT_SETTINGS.copy()

    def __enter__(self) -> 'Settings':
        return self

    def __exit__(self, type, value, traceback) -> None:
        self.save()
