import Team
import Rules 

class Game():
    def __init__(self, gamedict):
        self.gname = gamedict.get("gameid")
        self.hometeamname = gamedict.get("Home")
        self.awayteamname = gamedict.get("Away")
        self.hometeam = Team.Team(self.hometeamname, "Home")
        self.awayteam = Team.Team(self.awayteamname, "Away")
        self.rules = Rules.Rules(gamedict.get("Rules"))

    def __repr__(self):
        return f"{str(self.gname)} {str(self.hometeam)} {str(self.awayteam)} {str(self.rules)}"
    
