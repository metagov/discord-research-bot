import json

class Responses:
    DEFAULT_FILENAME = 'responses.json'
    
    def __init__(self) -> None:
        try:
            with open(self.DEFAULT_FILENAME, 'r') as file:
                responses = json.load(file)
                self.__dict__ = responses

        except FileNotFoundError:
            print("Error: couldn't find responses.json")
        
        except json.JSONDecodeError:
            print("Error: responses.json is not a valid json")

responses = Responses()