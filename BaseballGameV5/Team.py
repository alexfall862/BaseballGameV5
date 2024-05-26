from Roster import Roster as r
from Strategy import Strategy as s
import os

class Team():
    def __init__(self, name, travelstatus, pitchervalue):
        self.name = name
        self.travelstatus = travelstatus
        self.roster = r(self.name)
        self.strategy = s(self.name)
        self.score = 0
        self.currentbatspot = 1
        self.currentbatter = ''
        self.currentpitcher = ''
        self.catcher = Team.GrabPositionPlayer(self, 'catcher')
        self.firstbaseman = Team.GrabPositionPlayer(self, 'firstbase')
        self.secondbaseman = Team.GrabPositionPlayer(self, 'secondbase')
        self.thirdbaseman = Team.GrabPositionPlayer(self, 'thirdbase')
        self.shortstop = Team.GrabPositionPlayer(self, 'shortstop')
        self.leftfielder = Team.GrabPositionPlayer(self, 'leftfield')
        self.centerfielder = Team.GrabPositionPlayer(self, 'centerfield')
        self.rightfielder = Team.GrabPositionPlayer(self, 'rightfield')
        self.designatedhitter = Team.GrabPositionPlayer(self, 'designatedhitter')
        self.battinglist = [
            self.catcher, 
            self.firstbaseman, 
            self.secondbaseman, 
            self.thirdbaseman, 
            self.shortstop, 
            self.leftfielder, 
            self.centerfielder, 
            self.rightfielder, 
            self.designatedhitter, 
            ]
        self.startingpitcher = Team.GrabStartingPitcher(self, pitchervalue)
    def GrabPositionPlayer(self, position):
        return [player for player in self.roster.playerlist if player.lineup==position][0]
       
    def GrabStartingPitcher(self, pitchervalue):
        return [player for player in self.roster.playerlist if player.lineup=="starter" and player.pitchingorder==int(pitchervalue)][0]