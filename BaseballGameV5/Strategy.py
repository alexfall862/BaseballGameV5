import os
import csv

class Strategy():
    def __init__(self, teamname):
        self.teamname = teamname
        strategyload = Strategy.LoadStrategy(teamname)        
        self.StealFreq = strategyload.get("StealFreq")        
        self.PitcherPull = strategyload.get("PitcherPull")        

    def __repr__(self):
        return f"{self.ruletype} {self.innings} {self.outs}"

    def LoadStrategy(teamname):
        directory = f'..\\Strategy\\'
        keyword = "_" + teamname + "_strat.csv"
        for fname in os.listdir(directory):
            if keyword in fname:
                print(fname, "has the keyword")
                strategy = Strategy.pullStrategy(directory+fname)
                print(strategy)
                return strategy[0]

    def pullStrategy(directory):
        _strategy = []
        with open(directory, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', )
            for row in reader:
                _strategy.append(row)
        return _strategy


