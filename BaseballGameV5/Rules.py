import os
import csv
import json

class Rules():
    def __init__(self, ruletype):
        self.ruletype = ruletype
        rulesload = Rules.LoadRules(ruletype)
        self.innings = 9# int(rulesload["Innings"])
        self.outs = int(rulesload["Outs"])
        self.balls = int(rulesload["Balls"])
        self.strikes = int(rulesload["Strikes"])
        self.dh = True  # Default to DH enabled

    def __repr__(self):
        return f"{self.ruletype} {self.innings} {self.outs}"

    @classmethod
    def from_dict(cls, data: dict, ruletype: str = "endpoint"):
        """
        Create a Rules instance from a pre-adapted dictionary.

        Args:
            data: Dict containing rules data (from RulesAdapter.adapt())
            ruletype: Label for this ruleset

        Returns:
            Rules instance
        """
        instance = object.__new__(cls)
        instance.ruletype = ruletype
        instance.innings = int(data.get("Innings", 9))
        instance.outs = int(data.get("Outs", 3))
        instance.balls = int(data.get("Balls", 4))
        instance.strikes = int(data.get("Strikes", 3))
        instance.dh = data.get("DH", True)
        return instance

    def LoadBaselineJSON(directory):
        with open(str(directory)) as f:
            data=json.load(f)
        return data

    def LoadRules(ruletype):
        directory = f'..\\Rules\\'
        keyword = "_" + "rules" + "_.json"
        for fname in os.listdir(directory):
            if keyword in fname:
                rules = Rules.LoadBaselineJSON(directory+fname)
                return rules[0][ruletype]