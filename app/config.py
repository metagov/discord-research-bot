from collections.abc import MutableMapping
from pathlib import Path
import json

class Config(MutableMapping):
    """Mutable and persistent configuration store."""

    def __init__(self, filename, default=None):
        self.filename = filename
        self.data = default or {}

        # Load from disk or save default.
        if Path(self.filename).exists():
            self.load()

    def load(self):
        with open(self.filename, 'r') as file:
            self.data = json.load(file)
    
    def save(self):
        with open(self.filename, 'w') as file:
            json.dump(self.data, file, indent=4)

    def get(self, key, defval=None):
        if key not in self:
            return defval
        else:
            return self[key]

    # The next five methods are required by the base class.

    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
        self.save() # Save on every assignment.
    
    def __delitem__(self, key):
        del self.data[key]
        self.save() # Or deletion.
    
    def __len__(self):
        return len(self.data)
    
    def __iter__(self):
        return iter(self.data)

def to_slash_perms(arr):
    """Slash command library requires different format of permissions: a
    dictionary with integer guild IDs as the keys."""
    result = {}
    for obj in arr:
        result[obj['guild_id']] = [{
            'id': obj['role_id'],
            'type': 1, # 1 means role.
            'permission': True
        }]
    return result

config = Config('config.json')
perms = to_slash_perms(config['guilds']) # Make sure to use this instead.
