from dataclasses import dataclass
import os
import csv
import json

class Strategy():
    
    class PlayerStrat():
        def __init__(self, playerstrat):
            #print(playerstrat)
            self.id = playerstrat['id']
            self.stealfreq = playerstrat['stealfreq']
            self.pickofffreq = playerstrat['pickofffreq']
            self.pitchpull = playerstrat['pitchpull']
            self.plateapproach = playerstrat['plateapproach']
            self.pitchchoices = playerstrat['pitchchoices']
            
        def __repr__(self):
            return f"{self.id}/{self.stealfreq}/{self.pitchpull}/{self.plateapproach}/{self.pitchchoices}"

    class TeamStrat():
        def __init__(self, teamstrat):
            self.outfieldspacing = teamstrat['outfieldspacing']
            self.infieldspacing = teamstrat['infieldspacing']
            self.bullpencutoff = teamstrat['bullpencutoff']
            self.bullpenpriority = teamstrat['bullpenpriority']
            self.emergencypitcher = teamstrat['emergencypitcher']
            self.walklist = teamstrat['intentional walk list']

        def __repr__(self):
            return f"{self.outfieldspacing}/{self.infieldspacing}/{self.bullpencutoff}/{self.bullpenpriority}/{self.emergencypitcher}"            

    def __init__(self, teamname):
        self.teamname = teamname
        self.playerstrategy, self.teamstrategy = Strategy.FindFile(teamname)

    def __repr__(self):
        return f"{self.playerstrategy} {self.teamstrategy}"

    def FindFile(teamname):
        directory = f'..\\Strategy\\'
        keyword = '_'+teamname+'_strat.json'
        for fname in os.listdir(directory):
            if keyword in fname:
                #print(fname, "has the keyword")
                return Strategy.Load(directory+fname)

    # def LoadStrategy(teamname):
    #     directory = f'..\\Strategy\\'
    #     keyword = "_" + teamname + "_strat.csv"
    #     for fname in os.listdir(directory):
    #         if keyword in fname:
    #             #print(fname, "has the keyword")
    #             strategy = Strategy.pullStrategy(directory+fname)
    #             #print(strategy)
    #             return strategy[0]

    def Load(directoryjson):
        #print(directoryjson)
        with open(str(directoryjson)) as f:
            data=json.load(f)

        temp_playerlist = data[0]['playerstrat']
        temp_teamlist = data[1]['teamstrat']

        playerstrategy = []
        
        
        for player in temp_playerlist:
            #print(player)
            playerstrategy.append(
                    Strategy.PlayerStrat(
                            player                        
                        )
                )
            
        teamstrategy = Strategy.TeamStrat(temp_teamlist)
        
        return playerstrategy, teamstrategy

    # def pullStrategy(directory):
    #     _strategy = []
    #     with open(directory, 'r', newline='') as csvfile:
    #         reader = csv.DictReader(csvfile, delimiter=',', )
    #         for row in reader:
    #             _strategy.append(row)
    #     return _strategy