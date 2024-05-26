import random

class Action():
    def __init__(self, game):
        self.game = game
        Action.PrePitch(self)        
        Action.Processing(self)

    def PrePitch(self):
        #print(f"other stuff here")
        Action.AtBat(self)
    
    def AtBat(self):
        print(f"{self.game.currentinning} | {self.game.currentouts} | {self.game.hometeam.name} {self.game.hometeam.score} / {self.game.awayteam.name} {self.game.awayteam.score}")
        x = random.choices(['ball', 'strike', 'hit'], [2,3, 0], k=1)[0]
        if x=='hit':
            Action.PostPitch(self)



    def PostPitch(self):
        print(f"baserunning and fielding attempt")
        
    def Processing(self):
        if self.game.currentouts < int(self.game.rules.outs)-1:
            self.game.currentouts+=1        
        else:
            self.game.currentinning+=1
            self.game.currentouts = 0
            
        if self.game.currentinning > int(self.game.rules.innings) and self.game.hometeam.score != self.game.awayteam.score:
            self.game.gamedone = True
        elif self.game.currentinning > int(self.game.rules.innings): 
            self.game.hometeam.score += 1