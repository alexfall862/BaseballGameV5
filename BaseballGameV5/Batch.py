import csv
from email.charset import Charset


class Batch():
    def __init__(self, directory, rules):
        self.directory = directory + "\\games.csv"
        self.listofgames = Batch.pullgames(self.directory)

    def pullgames(directory):
        _pggames = []
        with open(directory, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', )
            for row in reader:
                _pggames.append(row)
        return _pggames