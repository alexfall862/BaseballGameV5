import math

class Steals():
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.firstbase = self.gamestate.game.on_firstbase
        self.secondbase = self.gamestate.game.on_secondbase 
        self.thirdbase = self.gamestate.game.on_thirdbase
        self.strategy =  self.gamestate.game.battingteam.strategy
        self.defense = self.gamestate.game.pitchingteam
        attemptoutcome = self.steal_eval(self.firstbase, self.secondbase, self.thirdbase)
                
    def pull_stealfreq(runner, stratlist):
        freq = [player.stealfreq for player in stratlist if player.id == runner.id][0]
        return freq     
    
    def steal_eval(self, firstbase, secondbase, thirdbase):
        if firstbase == None and secondbase == None and thirdbase == None:
            pass
        else:
            print(f"Baserunner Speed: {self.defense.firstbase.speed}")
            print(f"Baserunner Baserunning: {self.defense.firstbase.baserunning}")
            print(f"Baserunner Base reaction: {self.defense.firstbase.basereaction}")
            print(f"Catcher Throw Power: {self.defense.catcher.throwpower}")
            print(f"Catcher Throw Acc:{self.defense.catcher.throwacc}")
            print(f"Catcher Reaction: {self.defense.catcher.fieldreact}")
            print(f"Catcher Sequence: {self.defense.catcher.catchsequence}")
            print(f"Pitcher Pickoff: {self.defense.currentpitcher.pickoff}")
            print(f"Pitcher Sequence: {self.defense.currentpitcher.psequencing}")            
            if thirdbase != None:
                stealrating = Steals.pull_stealfreq(self.thirdbase, self.strategy.playerstrategy)
                print(f"{stealrating}")
            if secondbase != None and thirdbase == None:
                stealrating = Steals.pull_stealfreq(self.secondbase, self.strategy.playerstrategy)
                print(f"{stealrating}")
            if firstbase != None and secondbase == None:
                stealrating = Steals.pull_stealfreq(self.firstbase, self.strategy.playerstrategy)
                print(f"{stealrating}")
                                    


