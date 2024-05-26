import os
import csv

class Rules():
    def __init__(self, ruletype):
        self.ruletype = ruletype
        rulesload = Rules.LoadRules(ruletype)        
        self.innings = rulesload.get("Innings")        
        self.outs = rulesload.get("Outs")        

    def __repr__(self):
        return f"{self.ruletype} {self.innings} {self.outs}"

    def LoadRules(ruletype):
        directory = f'..\\Rules\\'
        keyword = "_" + ruletype + "_.csv"
        for fname in os.listdir(directory):
            if keyword in fname:
                #print(fname, "has the keyword")
                rules = Rules.pullrules(directory+fname)
                #print(rules)
                return rules[0]

    def pullrules(directory):
        _rules = []
        with open(directory, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', )
            for row in reader:
                _rules.append(row)
        return _rules


