from Roster import Roster as r
from Strategy import Strategy as s
import os

class Team():
    def __init__(self, name, travelstatus):
        self.name = name
        self.travelstatus = travelstatus
        self.roster = r(self.name)
        self.score = 0
        self.strategy = s(self.name)