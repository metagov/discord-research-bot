import json
import discord
from pathlib import Path

class PersistentJSON:
    def __init__(self, filename, default_db={}):
        self.filename = filename
        self.db = default_db

        # Creates empty json if file doesn't already exist
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
        json.dump(self.db, file, indent=4)
        file.close()

    # Internal Python functions allow the object to be interacted with like a dictionary using []
    def __getitem__(self, key):
        return self.db[key]

    def __setitem__(self, key, val):
        self.db[key] = val
        self._save()
    
    # Object represented as a string of the dictionary
    def __repr__(self):
        return str(self.db)

    def __str__(self):
        return str(self.db)

def user_to_color(user: discord.User):
    '''Maps discord discriminator to a hex color value.'''
    return int(int(user.discriminator) / 9999 * 0xffffff)
