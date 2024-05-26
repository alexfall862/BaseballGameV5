import Team
import Rules 
import Action

class Game():
    def __init__(self, gamedict):
        self.gname = gamedict.get("gameid")
        self.hometeam = Team.Team(gamedict.get("Home"), "Home", gamedict.get("Rotation"))
        self.awayteam = Team.Team(gamedict.get("Away"), "Away", gamedict.get("Rotation"))
        self.rules = Rules.Rules(gamedict.get("Rules"))
        self.currentinning = 1
        self.currentouts = 0
        self.topofinning = True
        self.gamedone = False



    def __repr__(self):
        return f"{str(self.gname)} {str(self.hometeam)} {str(self.awayteam)} {str(self.rules)}"
    
    def RunGame(self):
        print(self.hometeam.battinglist)
        print(self.hometeam.startingpitcher)
        print(self.awayteam.battinglist)
        print(self.awayteam.startingpitcher)       



        while self.gamedone == False:
            x = Action.Action(self)