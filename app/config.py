from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import List
from pathlib import Path
from datetime import datetime
import logging
import json

DEFAULT_TOKEN = 'INSERT TOKEN HERE'

@dataclass
class SupplementalConfig:
    guild_ids: List[int]

@dataclass
class PerGuildConfig:
    pending_id: int
    approved_id: int

def parse_config(config) -> SupplementalConfig:
    """Transform user-friendly format into programmer-friendly format."""
    guild_ids = config['guild_ids'].copy()
    for guild_id in config['guild_configs']:
        guild_id = int(guild_id) # Convert strings to integers.
        guild_ids.append(guild_id)
    return SupplementalConfig(guild_ids=guild_ids)

class Config(MutableMapping):
    """A mutable and persistent configuration store that acts like a
    dictionary."""

    def __init__(self, filename='config.json', default=None):
        self.filename = filename
        self.data = default or {} # Top-level structure is a dictionary.

        # Load from disk or save default.
        if Path(self.filename).exists():
            self.load()
        else:
            self.save()
    
    def load(self):
        """Loads current config file.
        
        If the file is ill-formatted, it is backed up and the current data is
        saved to disk. If this happens, the current data will most likely be
        the default data."""
        try:
            with open(self.filename, 'r') as file:
                self.data = json.load(file)
        except json.JSONDecodeError as e:
            logging.error('Failed to load config from disk. Making backup'
                ' and overwriting with default.')
            logging.error(e) # Show information about exception.

            self.backup()
            self.save()

    def backup(self):
        """Renames current config file to include the current time."""
        path = Path(self.filename)
        if path.exists():
            timestamp = datetime.utcnow().isoformat()
            path.rename(f'{timestamp}-{self.filename}')
    
    def save(self):
        """Saves the current data to the config file."""
        with open(self.filename, 'w') as file:
            json.dump(self.data, file, indent=4)
    
    def get(self, key, initval=None):
        """Gets the current value stored at key.
        
        If the key does not exist, then it is initialized with `initval` and
        `initval` is returned. If this occurs then the config is saved."""
        if key not in self.data:
            self.data[key] = initval
        return self.data[key]
    
    def get(self, key, defval=None):
        """Gets the current value stored at key.
        
        If the key does not exist, then `defval` is returned."""
        if key not in self:
            return defval
        return self.data[key]

    # The following five methods are required by the base class.

    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
        self.save() # Assignment causes a save.
    
    def __delitem__(self, key):
        del self.data[key]
        self.save() # So does deletion.
    
    def __iter__(self):
        return iter(self.data)
    
    def __len__(self):
        return len(self.data)

default = {
    'token': DEFAULT_TOKEN,
    'guild_ids': [],
    'guild_configs': {},
    'command_prefix': '.',
    'db_fname': 'messages.json',
    'role_name': 'Curator',
    'comment_status': {},
    'emoji': '🔭',
    'bridges': {
        'groups': {},
        'channels': {}
    },
    'deploys_wip': {},
    'admins': []
}

# Import these into extensions to access config.
config = Config(default=default)
