from pathlib import Path
import json

class PersistentJSON:
    def __init__(self, filename, default={}):
        self.filename = filename
        self.db = default

        # Creates empty json if file doesn't already exist.
        if Path(self.filename).exists():
            self._load()
        else:
            self._save()
    
    def _load(self):
        file = open(self.filename, 'r')
        d = json.load(file)
        self.db = self.unstringify(d)
        file.close()
    
    def _save(self):
        d = self.stringify(self.db)
        file = open(self.filename, 'w')
        json.dump(d, file, indent=4)
        file.close()

    # Internal Python functions allow the object to be treated like a dict.
    # Integers are converted to strings to preserve precision.
    def __getitem__(self, key):
        return self.db[key]

    def stringify(self, obj):
        if type(obj) is int:
            return f'int-{obj}'
        
        if type(obj) is list:
            return [self.stringify(x) for x in obj]
        
        if type(obj) is dict:
            return {self.stringify(k): self.stringify(v)
                    for k, v in obj.items()}
        
        return obj
    
    def unstringify(self, obj):
        if type(obj) is str and obj.startswith('int-'):
            return int(obj[4:])
        
        if type(obj) is list:
            for i, item in enumerate(obj):
                obj[i] = self.unstringify(item)
            return obj

        if type(obj) is dict:
            d = {}
            for k, v in obj.items():
                d[self.unstringify(k)] = self.unstringify(v)
            return d
        
        return obj

    def __setitem__(self, key, val):
        self.db[key] = val
        self._save()
    
    def get(self, key, defval=None):
        try:
            return self[key]
        except KeyError as e:
            return defval

    # Object represented as a string of the dictionary.
    def __repr__(self):
        return str(self.db)

    def __str__(self):
        return str(self.db)
    
    def __iter__(self):
        yield from self.db

config = PersistentJSON('config.json', default={
    'token': '',
    'guild_ids': [],
    'permissions': {}
})
print(config['permissions'])
