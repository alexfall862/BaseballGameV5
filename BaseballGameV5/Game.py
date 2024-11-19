from ast import Pass
import Team
import Rules 
import Action
import Baselines
import json 

class Game():
    def __init__(self, gamedict):
        self.gname = gamedict.get("gameid")
        self.hometeam = Team.Team(gamedict.get("Home"), "Home", gamedict.get("Rotation"))
        self.awayteam = Team.Team(gamedict.get("Away"), "Away", gamedict.get("Rotation"))
        self.rules = Rules.Rules(gamedict.get("Rules"))
        self.currentinning = 1
        self.currentouts = 0
        self.currentballs = 0
        self.currentstrikes = 0
        self.outcount = 0
        self.on_firstbase = None
        self.on_secondbase = None
        self.on_thirdbase = None
        self.current_runners_home = []
        self.is_walk = False
        self.is_strikeout = False
        self.is_inplay = False
        self.is_hit = False #temp
        self.is_hbp = False
        self.error_count = 0
        self.is_single = False
        self.is_double = False
        self.is_triple = False
        self.is_homerun = False
        self.is_liveball = False
        self.ab_over = False
        self.topofinning = True
        self.gamedone = False
        self.battingteam = self.awayteam
        self.pitchingteam = self.hometeam
        self.skip_bool = None
        self.actions = []
        self.baselines = Baselines.Baselines(gamedict.get("Rules"))

    def __repr__(self):
        return f"{str(self.gname)} {str(self.hometeam)} {str(self.awayteam)} {str(self.rules)}"
    
    def RunGame(self):
        #print(self.hometeam.battinglist)
        #print(self.hometeam.currentpitcher)
        #print(self.awayteam.battinglist)
        #print(self.awayteam.currentpitcher)       

        while self.gamedone == False:
            x = Action.Action(self)
        Action.Action.counter = 0
        listofactions = []
        for action in self.actions:
            print(action)
            listofactions.append(action)    
        json_string = listofactions
        with open("testoutput.json", "w") as outfile:
            json.dump(json_string, outfile)
        ##print("DONE")
        #print(listofactions)