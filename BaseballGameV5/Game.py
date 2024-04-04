class Game():
    def __init__(self, gamedict):
        self.gname = gamedict.get("gameid")
        self.hometeam = gamedict.get("Home")
        self.awayteam = gamedict.get("Away")
        self.hometeamscore = 0
        self.awayteamscore = 0

    def __repr__(self):
        return f"{str(self.gname)} {str(self.hometeam)} {str(self.awayteam)}"

    def loadroster(self):
        pass