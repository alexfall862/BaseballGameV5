class Steals():
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.firstbase = self.gamestate.game.on_firstbase
        self.secondbase = self.gamestate.game.on_secondbase 
        self.thirdbase = self.gamestate.game.on_thirdbase
        self.strategy =  self.gamestate.game.battingteam.strategy
        attemptoutcome = self.steal_eval(self.firstbase, self.secondbase, self.thirdbase)
                
    def steal_eval(self, firstbase, secondbase, thirdbase):
        if firstbase == None and secondbase == None and thirdbase == None:
            pass
        elif firstbase != None:
            test = [player for player in self.strategy.playerstrategy if player.id == firstbase.id]
            print(f"{test}")
            


