import csv
import json
from email.charset import Charset


class Batch():
    def __init__(self, directory, rules):
        self.directory = directory + "\\games.json"
        self.listofgames = Batch.pullgamesJSON(self.directory)
        print(Batch.pullgamesJSON(self.directory))


    def pullgames(directory):
        _pggames = []
        with open(directory, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', )
            for row in reader:
                _pggames.append(row)
        return _pggames

    def pullgamesJSON(directory):
        _pggames = []
        with open(str(directory)) as f:
            data=json.load(f)
        print(data['games'])
        for game in data['games'].values():
            print(game)
            _pggames.append(game)
        return _pggames