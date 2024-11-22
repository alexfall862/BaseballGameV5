import os
import csv
import json

class Rules():
    def __init__(self, ruletype):
        self.ruletype = ruletype
        rulesload = Rules.LoadRules(ruletype)        
        self.innings = int(rulesload["Innings"])        
        self.outs = int(rulesload["Outs"])
        self.balls = int(rulesload["Balls"])
        self.strikes = int(rulesload["Strikes"])

    def __repr__(self):
        return f"{self.ruletype} {self.innings} {self.outs}"

    def LoadBaselineJSON(directory):
        with open(str(directory)) as f:
            data=json.load(f)
        return data

    def LoadRules(ruletype):
        directory = f'..\\Rules\\'
        keyword = "_" + "rules" + "_.json"
        for fname in os.listdir(directory):
            if keyword in fname:
                #print(fname, "has the keyword")
                #rules = Baselines.pullbaseline(directory+fname)
                rules = Rules.LoadBaselineJSON(directory+fname)
                #print(rules)
                return rules[0][ruletype]