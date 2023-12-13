import json


class Settings:
    DEFAULT_FILENAME = "settings.json"
    DEFAULT_SETTINGS = {
        "database": "telescope",
        "observatory": None,
        "emoji": "🔭"
    }

    def __init__(self):
        self.load()

    def load(self):
        self.clear()

        try:
            with open(self.DEFAULT_FILENAME, 'r') as file:
                changes = json.load(file)
                self.__dict__.update(changes)
        except FileNotFoundError:
            self.save()

    def save(self):
        with open(self.DEFAULT_FILENAME, 'w') as file:
            json.dump(self.__dict__, file, indent=4)

    def clear(self):
        self.__dict__ = self.DEFAULT_SETTINGS.copy()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.save()
