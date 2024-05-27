import random
import InteractionEngine as ie
import copy

class Action():
    def __init__(self, game):
        self.game = game
        Action.PrePitch(self)        
        Action.Processing(self)
        NextAtBat(self)

#    def __repr__(self):
#        return f"I{self.game.currentinning}{self.game.topofinning}O{self.game.currentouts}HT{self.game.hometeam.name}HS{self.game.hometeam.score}AT{self.game.awayteam.name:<3}AS{self.game.awayteam.score:>2}BT{self.game.battingteam.name:>3}{self.game.battingteam.currentbatspot}PT{self.game.pitchingteam.name}{self.game.pitchingteam.currentbatspot}AB{self.game.currentstrikes}/{self.game.currentballs}"

    def PrePitch(self):
        #print(f"other stuff here")
        Action.AtBat(self)
    
    def AtBat(self):
        #print(f"{self.game.currentinning:<3}{self.game.topofinning}|{self.game.currentouts:<1}| {self.game.hometeam.name:<3}{self.game.hometeam.score:>2} / {self.game.awayteam.name:<3}{self.game.awayteam.score:>2} ||| B: {self.game.battingteam.name:>3}{self.game.battingteam.currentbatspot} P: {self.game.pitchingteam.name:>3}{self.game.pitchingteam.currentbatspot}  CAB:{self.game.currentstrikes}/{self.game.currentballs}")
        ie.PitchEvent(self)
        outcome = random.choices(['ball', 'strike', 'contact', 'hbp'], [0, 3, 1, 0], k=1)[0]
        AtBatOutcomeParser(self, outcome)
        Action.PostPitch(self)
        

    def PostPitch(self):
        if self.game.is_strikeout == False:
            WalkEval(self) 
            HitEval(self)        

    def Processing(self):
        #print(self.game.outcount)
        self.game.currentouts += self.game.outcount
        #print(f"Runners Home: {len([])}")#{len(self.game.current_runners_home)}")
        self.game.battingteam.score += self.game.current_runners_home
        self.game.actions.append([self.game.currentinning, self.game.topofinning, self.game.currentouts, self.game.hometeam.name, self.game.hometeam.score, self.game.awayteam.name, self.game.awayteam.score, self.game.battingteam.name, self.game.battingteam.currentbatspot, self.game.pitchingteam.name, self.game.pitchingteam.currentbatspot, self.game.currentstrikes, self.game.currentballs])
        if self.game.outcount > 0:
            OutProcessor(self)

def HitEval(self):
    if self.game.is_hit == True:
        #print("Hit Registered")
        if self.game.on_firstbase == None:
            self.game.on_firstbase = self.game.battingteam.currentbatter
            #print(f"{self.game.on_firstbase} on first")
        if self.game.on_firstbase != None:
            if self.game.on_secondbase == None:
                self.game.on_secondbase = self.game.on_firstbase
                self.game.on_firstbase = self.game.battingteam.currentbatter
                #print(f"{self.game.on_secondbase} on second, {self.game.on_firstbase} on first.")
            if self.game.on_secondbase != None:
                if self.game.on_thirdbase == None:
                    self.game.on_thirdbase = self.game.on_secondbase
                    self.game.on_secondbase = self.game.on_firstbase
                    self.game.on_firstbase = self.game.battingteam.currentbatter
                    #print(f"{self.game.on_thirdbase} on third, {self.game.on_secondbase} on second, {self.game.on_firstbase} on first.")
                if self.game.on_thirdbase != None:
                    #print("RUNNERS HOME")
                    self.game.current_runners_home += 1
                    self.game.on_thirdbase = self.game.on_secondbase
                    self.game.on_secondbase = self.game.on_firstbase
                    self.game.on_firstbase = self.game.battingteam.currentbatter
    else:
        pass    

def WalkEval(self):
    if self.game.is_walk == True or self.game.is_hbp == True:
        if self.game.on_firstbase == None:
            self.game.on_firstbase = self.game.battingteam.currentbatter
        if self.game.on_firstbase != None:
            if self.game.on_secondbase == None:
                self.game.on_secondbase = self.game.on_firstbase
                self.game.on_firstbase = self.game.battingteam.currentbatter
            if self.game.on_secondbase != None:
                if self.game.on_thirdbase == None:
                    self.game.on_thirdbase = self.game.on_secondbase
                    self.game.on_secondbase = self.game.on_firstbase
                    self.game.on_firstbase = self.game.battingteam.currentbatter
                if self.game.on_thirdbase != None:
                    self.game.current_runners_home += 1
                    self.game.on_thirdbase = self.game.on_secondbase
                    self.game.on_secondbase = self.game.on_firstbase
                    self.game.on_firstbase = self.game.battingteam.currentbatter
    else:
        pass    
  
def NextAtBat(self):
    if self.game.ab_over == True:
        self.game.currentstrikes = 0
        self.game.currentballs = 0
        self.game.is_hit = False
        self.game.is_walk = False
        self.game.is_strikeout = False
        self.game.ab_over = 0
        self.game.outcount = 0
        self.game.current_runners_home = 0
    

def CountRunners(self):
    f = (self.game.on_firstbase == None)
    s = (self.game.on_secondbase == None)
    t = (self.game.on_thirdbase == None)
    countofbases = f+s+t
    return int(countofbases)

def AtBatOutcomeParser(self, outcome):
    if outcome == 'strike':
        self.game.currentstrikes += 1
    elif outcome == 'ball':
        self.game.currentballs += 1
    elif outcome == 'contact':
        self.game.ab_over = True
        self.game.is_hit = True
    elif outcome == 'hbp':
        self.game.is_hbp = True
    if self.game.currentstrikes >= self.game.rules.strikes:
        self.game.ab_over = True
        self.game.is_strikeout = True
        self.game.outcount += 1
    if self.game.currentballs >= self.game.rules.balls or self.game.is_hbp == True:
        self.game.ab_over = True
        self.game.is_walk = True

#GAME STATE
def GameFinishedCheck(self):
    if self.game.currentinning >= self.game.rules.innings and self.game.hometeam.score > self.game.awayteam.score:
        self.game.gamedone = True    
    if self.game.currentinning >= self.game.rules.innings and self.game.hometeam.score != self.game.awayteam.score and self.game.topofinning==False:
        self.game.gamedone = True    
        
def WalkoffCheck(self):
    if self.game.currentinning > self.game.rules.innings and self.game.hometeam.score > self.game.awayteam.score:
        self.game.gamedone = True

def OutProcessor(self):
    WalkoffCheck(self)  
    if (self.game.currentouts + self.game.outcount) <= self.game.rules.outs-1:
        self.game.currentouts += self.game.outcount 
        self.game.outcount = 0
    elif (self.game.currentouts + self.game.outcount) >= self.game.rules.outs-1:
        InningFlip(self)    

def InningFlip(self):
    GameFinishedCheck(self)  
    self.game.on_firstbase = None
    self.game.on_secondbase = None
    self.game.on_thirdbase = None
    self.game.outs = 0
    self.game.currentouts = 0
    self.game.outcount = 0
    if self.game.topofinning == False:
        self.game.currentinning+=1
    self.game.topofinning = not self.game.topofinning
    flipholderbat = self.game.battingteam
    flipholderpitch = self.game.pitchingteam
    self.game.battingteam = flipholderpitch
    self.game.pitchingteam = flipholderbat
    