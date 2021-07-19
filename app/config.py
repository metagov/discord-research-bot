from pathlib import Path
import json

class PersistentJSON:
    def __init__(self, filename, default_db={}):
        self.filename = filename
        self.db = default_db

        # Creates empty json if file doesn't already exist.
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

    # Internal Python functions allow the object to be treated like a dict.
    # Integers are converted to strings to preserve precision.
    def __getitem__(self, key):
        val = self.db[key]

        if type(val) == list:
            for c, i in enumerate(val):
                if type(i) is str:
                    if i.startswith("int-"):
                        val[c] = int(i[4:])

        if type(val) == str:
            if val.startswith("int-"):
                val = int(val[4:])

        return val

    def __setitem__(self, key, val):
        if type(val) is list:
            for c, i in enumerate(val):
                if type(i) is int:
                    val[c] = "int-" + str(i)

        if type(val) is int:
            val = "int-" + str(val)
        self.db[key] = val
        self._save()
    
    # Object represented as a string of the dictionary.
    def __repr__(self):
        return str(self.db)

    def __str__(self):
        return str(self.db)

config = PersistentJSON('config.json')
# print(config['guild_ids'])