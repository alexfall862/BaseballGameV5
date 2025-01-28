from ast import Pass
import Team
import Rules 
import Action
import Baselines
import json 
import csv 
import Stats as stats
import pandas as pd

class Game():
    def __init__(self, gamedict):
        self.gname = gamedict.get("gameid")
        self.baselines = Baselines.Baselines(gamedict.get("Rules"))
        self.hometeam = Team.Team(gamedict.get("Home"), "Home", gamedict.get("Rotation"), self.baselines)
        self.awayteam = Team.Team(gamedict.get("Away"), "Away", gamedict.get("Rotation"), self.baselines)
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
        self.is_pickoff = False
        self.is_stealattempt = False
        self.is_stealsuccess = False
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
        self.batted_ball = None
        self.air_or_ground = None
        self.targeted_defender = None
        self.skip_bool = None
        self.actions = []
        self.overallresults = []
        self.meta = Game.GameResult(self.gname, self.hometeam, self.awayteam, self.actions)

    class GameResult():
        def __init__(self, gname, hometeam, awayteam, actions):
            self.id = gname
            self.hometeam = hometeam
            self.awayteam = awayteam
            self.actions = actions
        def to_dict(self):
            return {
                "id":self.id,
                "hometeam":self.hometeam.name,
                "hometeam score": self.hometeam.score,
                "awayteam":self.awayteam.name,
                "awayteam score": self.awayteam.score,
            }

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
        #print(self.overallresults)
        thing = stats.create_score_table(self.overallresults)
        #print(thing)
        #stats.Inning_Tabulator(self.overallresults)
        
        stats.FieldStatPullSave(self.hometeam, self.gname)
        stats.FieldStatPullSave(self.awayteam, self.gname)
        stats.BattingStatPullSave(self.hometeam, self.gname)
        stats.BattingStatPullSave(self.awayteam, self.gname)
        stats.PitchStatPullSave(self.hometeam, self.gname)
        stats.PitchStatPullSave(self.awayteam, self.gname)

        for player in self.hometeam.roster.playerlist:
            if player.pitchingstats.pitches_thrown > 0:
                pass
                #print(f"Pitching: {player.pitchingstats.pid}")

        for player in self.hometeam.roster.playerlist:
            if player.battingstats.plate_appearances> 0:
                pass
                #print(f"Batting: {player.pitchingstats.pid}")        

        for action in self.actions:
            #print(action)
            listofactions.append(action)    
        export_dataframe = pd.DataFrame(listofactions)
        export_dataframe.replace({"None": ""}, inplace=True)
        #print(export_dataframe['Error List'])
        export_dataframe.to_csv(f"{self.gname}.csv", na_rep="", index=False)

        actions_string = listofactions

        test = stats.StatJSONConverter(self)

        stats.SaveJSON(test, "full_json_test")
        exit()
        
        with open(f"testoutput_{self.gname}.json", "w") as outfile:
            json.dump(actions_string, outfile)
        
        # with open(f"testoutput_{self.gname}.csv", "w", newline="") as outputfile:
        #     dict_writer = csv.DictWriter(outputfile, listofactions[0].keys())
        #     dict_writer.writeheader()
        #     dict_writer.writerows(listofactions)
        ##print("DONE")
        #print(listofactions)