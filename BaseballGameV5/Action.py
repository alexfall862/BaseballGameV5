import random
import InteractionEngine as ie
import copy
import FatigueInjury as fi
import defense as d
import Steals as steals


class Action():
    def __init__(self, game):
        self.game = game
        self.outcome = None
        self.defensiveoutcome = None
        Action.PrePitch(self)        
        Action.Processing(self)


    def __repr__(self):
        return f"I{self.game.currentinning}{self.game.topofinning}O{self.game.currentouts}HT{self.game.hometeam.name}HS{self.game.hometeam.score}AT{self.game.awayteam.name:<3}AS{self.game.awayteam.score:>2}BT{self.game.battingteam.name:>3}{self.game.battingteam.currentbatspot}PT{self.game.pitchingteam.name}{self.game.pitchingteam.currentbatspot}AB{self.game.currentstrikes}/{self.game.currentballs}"

    def PrePitch(self):
        self.game.error_count=0
        skip = steals.Steals(self).skippitch 
        if skip == True:
            self.game.skip_bool = True
        elif skip == False:
            self.game.skip_bool = False
            Action.AtBat(self)
    
    def AtBat(self):
        self.outcome = ie.PitchEvent(self).outcome
        #print(f"{self.game.currentinning:<3}{self.game.topofinning}|{self.game.currentouts:<1}-{self.game.outcount}| {self.game.hometeam.name:<3}{self.game.hometeam.score:>2} / {self.game.awayteam.name:<3}{self.game.awayteam.score:>2} ||| B: {self.game.battingteam.name:>3}{self.game.battingteam.currentbatspot} P: {self.game.pitchingteam.name:>3}{self.game.pitchingteam.currentbatspot}  CAB:{self.game.currentstrikes}/{self.game.currentballs} {self.outcome}")
        #print(self.outcome)
        #outcome = random.choices(['ball', 'strike', 'contact', 'hbp'], [0, 3, 1, 0], k=1)[0]
        AtBatOutcomeParser(self)
        Action.PostPitch(self)
        

    def PostPitch(self):
        if self.game.is_strikeout == False:
            WalkEval(self) 
            if self.defensiveoutcome != None:
                HitEval(self)        

    def Processing(self):
        #print(self.game.outcount)
        self.game.currentouts += self.game.outcount
        #print(f"Runners Home: {len([])}")#{len(self.game.current_runners_home)}")
        self.game.battingteam.score += len(self.game.current_runners_home)
        self.game.actions.append([self.game.error_count, self.game.currentinning, self.game.topofinning, self.game.currentouts, self.game.outcount, self.game.hometeam.name, self.game.hometeam.score, self.game.awayteam.name, self.game.awayteam.score, self.game.battingteam.name, self.game.battingteam.currentbatspot, self.game.pitchingteam.name, self.game.pitchingteam.currentbatspot, self.game.currentstrikes, self.game.currentballs, self.game.battingteam.currentbatter, self.outcome, self.game.on_firstbase, self.game.on_secondbase, self.game.on_thirdbase, len(self.game.current_runners_home), self.defensiveoutcome, self.game.skip_bool, [self.game.is_single, self.game.is_double, self.game.is_triple, self.game.is_homerun]])
        NextAtBat(self)        

        if self.game.outcount > 0:
            OutProcessor(self)
        #fi.Fatigue()
        

def HitEval(self):
#    print(f"DEFENSIVE OUTCOME: {self.defensiveoutcome[4]}")
    self.game.on_firstbase = self.defensiveoutcome[4][0]
    self.game.on_secondbase = self.defensiveoutcome[4][1]
    self.game.on_thirdbase = self.defensiveoutcome[4][2]
    if self.defensiveoutcome[4][3] != None:
        listofrunners = self.defensiveoutcome[4][3].copy()
        #print(f"SELF DEFENSIVEOUTCOME: ::: {len(listofrunners)}")
        for runner in listofrunners:
            self.game.current_runners_home.append(runner)

                
def WalkEval(self):
    if self.game.is_walk == True or self.game.is_hbp == True:
        if self.game.on_firstbase == None:
            self.game.on_firstbase = self.game.battingteam.currentbatter
            return
        if self.game.on_firstbase != None:
            if self.game.on_secondbase == None:
                self.game.on_secondbase = self.game.on_firstbase
                self.game.on_firstbase = self.game.battingteam.currentbatter
                return
            if self.game.on_secondbase != None:
                if self.game.on_thirdbase == None:
                    self.game.on_thirdbase = self.game.on_secondbase
                    self.game.on_secondbase = self.game.on_firstbase
                    self.game.on_firstbase = self.game.battingteam.currentbatter
                    return
                if self.game.on_thirdbase != None:
                    self.game.current_runners_home.append(self.game.on_thirdbase)
                    self.game.on_thirdbase = self.game.on_secondbase
                    self.game.on_secondbase = self.game.on_firstbase
                    self.game.on_firstbase = self.game.battingteam.currentbatter
                    return

        


    else:
        pass    
  
def NextAtBat(self):
    #print(self.game.ab_over)
    if self.game.ab_over == True:
        self.game.currentstrikes = 0
        self.game.currentballs = 0
        self.game.is_hit = False
        self.game.is_single = False        
        self.game.is_double = False
        self.game.is_triple = False
        self.game.is_homerun = False        
        self.game.is_walk = False
        self.game.is_strikeout = False
        self.game.ab_over = False
        self.game.current_runners_home = []
        self.game.battingteam.TickBatter()
    

def AtBatOutcomeParser(self):
    if self.outcome[0] == 'Strike':
        if self.outcome[1] == "Foul":
            if self.game.currentstrikes == self.game.rules.strikes - 1:
                pass
            else:
                self.game.currentstrikes+=1                      
            #print(self.game.currentstrikes)
        else:
            self.game.currentstrikes+=1
            #print(self.game.currentstrikes)

    if self.game.currentstrikes >= self.game.rules.strikes:
        #print("working")
        self.game.ab_over = True
        self.game.is_strikeout = True
        self.game.outcount+=1
        
    if self.outcome[0] == 'Ball':
        self.game.currentballs +=1
    
    if self.game.currentballs >= self.game.rules.balls:
        self.game.ab_over = True
        self.game.is_walk = True

    #print(outcome[1])
    #print(f"input: {self.outcome[1]}")
    #print(f"{self.outcome[1] in ('far left' or 'left' or 'center left' or 'dead center' or 'center right' or 'right' or 'far right')} | {self.outcome[1]}")
    if self.outcome[1] in ('far left', 'left', 'center left', 'dead center', 'center right', 'right', 'far right'):
        #print("event fired")
        self.defensiveoutcome = d.ballmoving(self).defenseoutcome
        self.game.ab_over = True


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
    if (self.game.currentouts) < self.game.rules.outs:
        #self.game.currentouts += self.game.outcount 
        self.game.outcount = 0
    elif (self.game.currentouts + self.game.outcount) >= self.game.rules.outs:
        InningFlip(self)    

def InningFlip(self):
    GameFinishedCheck(self)  
    self.game.on_firstbase = None
    self.game.on_secondbase = None
    self.game.on_thirdbase = None
    self.game.currentouts = 0
    self.game.outcount = 0
    if self.game.topofinning == False:
        self.game.currentinning+=1
    self.game.topofinning = not self.game.topofinning
    flipholderbat = self.game.battingteam
    flipholderpitch = self.game.pitchingteam
    self.game.battingteam = flipholderpitch
    self.game.pitchingteam = flipholderbat
    