import json
import discord
from pathlib import Path

class PersistentJSON:
    def __init__(self, filename):
        self.filename = filename
        self.db = {}

        if Path(self.filename).exists():
            self._load()
        else:
            self._save()

    def _load(self):
        file = open(self.filename, 'r')
        self.db = json.load(file)
        file.close()
    
    def _save(self):
        file = open(self.filename, 'w')
        json.dump(self.db, file)
        file.close()

    def __getitem__(self, key):
        return self.db[key]

    def __setitem__(self, key, val):
        self.db[key] = val
        self._save()

def user_to_color(user: discord.User):
    '''Maps discord discriminator to a hex color value.'''
    return int(int(user.discriminator) / 9999 * 0xffffff)
