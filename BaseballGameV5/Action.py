import random
import InteractionEngine as ie
import copy
import Fatigue as f
import defense as d
import Steals as steals
import itertools
import Stats as stats


class Action():
    counter = 0
    def __init__(self, game):
        self.id = Action.counter
        Action.counter+=1
        self.game = game
        self.outcome = None
        self.defensiveoutcome = None
        Action.AttributeInjuryCheck(self)
        Action.PrePitch(self)        
        Action.Processing(self)


    def __repr__(self):
        return f"I{self.game.currentinning}{self.game.topofinning}O{self.game.currentouts}HT{self.game.hometeam.name}HS{self.game.hometeam.score}AT{self.game.awayteam.name:<3}AS{self.game.awayteam.score:>2}BT{self.game.battingteam.name:>3}{self.game.battingteam.currentbatspot}PT{self.game.pitchingteam.name}{self.game.pitchingteam.currentbatspot}AB{self.game.currentstrikes}/{self.game.currentballs}"

    def AttributeInjuryCheck(self):
        self.game.hometeam.ActionAdjustments()
        self.game.awayteam.ActionAdjustments()

    def PrePitch(self):
        self.game.error_count=0
        skip = steals.Steals(self).skippitch 
        #print(f"{skip} {self.id}{self.defensiveoutcome}")
        
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
        #print(f"{self.game.skip_bool} {self.id}{self.defensiveoutcome}")

    def ActionPrint(self):
        return {
            "ID": self.id,
            "Inning": self.game.currentinning,
            "Inning Half": self.game.topofinning,
            "Home Team": self.game.hometeam.name,
            "Home Score": self.game.hometeam.score,
            "Away Team": self.game.awayteam.name,
            "Away Score": self.game.awayteam.score,
            "Ball Count": self.game.currentballs,
            "Strike Count": self.game.currentstrikes,  
            "Out Count": self.game.currentouts,   
            "Outs this Action": self.game.outcount,
            "Current Home Pitcher": str(self.game.hometeam.currentpitcher),
            "Current Away Pitcher": str(self.game.awayteam.currentpitcher),
            "Current Home Batter": str(self.game.hometeam.currentbatter),
            "Current Away Batter": str(self.game.awayteam.currentbatter),
            "Outcomes": str(self.outcome),
            "Batted Ball": str(self.game.batted_ball),
            "Air or Ground": str(self.game.air_or_ground),
            "Targeted Defender": str(self.game.targeted_defender),
            "Defensive Outcome": str(self.defensiveoutcome[3] if self.defensiveoutcome != None else None), #str(self.defensiveoutcome), 
            "Error List": str(self.defensiveoutcome[5] if self.defensiveoutcome != None else None),
            "Defensive Actions": str(self.defensiveoutcome[6] if self.defensiveoutcome != None else None),
            "On First": str(self.game.on_firstbase),
            "On Second": str(self.game.on_secondbase),
            "On Third": str(self.game.on_thirdbase),
            "Home": str(self.game.current_runners_home),
            "Is_Walk": self.game.is_walk ,
            "Is_Strikeout": self.game.is_strikeout,
            "Is_InPlay": self.game.is_inplay,
            "Is_Hit": self.game.is_hit,
            "Is_HBP": self.game.is_hbp,
            "Is_Pickoff": self.game.is_pickoff,
            "Is_StealAttempt": self.game.is_stealattempt,
            "Is_StealSuccess": self.game.is_stealsuccess,
            "Error_Count": self.game.error_count,
            "Is_Liveball": self.game.is_liveball,
            "Is_Single": self.game.is_single,
            "Is_Double": self.game.is_double,
            "Is_Triple": self.game.is_triple,
            "Is_Homerun": self.game.is_homerun,
            "AB_Over": self.game.ab_over,
            "GameDone": self.game.gamedone,
            "Batting Team": str(self.game.battingteam.currentbatter),
            "Current Pitcher":str(self.game.pitchingteam.currentpitcher),
            "Catcher":str(self.game.pitchingteam.catcher),
            "First Base":str(self.game.pitchingteam.firstbase),
            "Second Base":str(self.game.pitchingteam.secondbase),
            "Third Base":str(self.game.pitchingteam.thirdbase),
            "Shortstop":str(self.game.pitchingteam.shortstop),
            "Left Field":str(self.game.pitchingteam.leftfield),
            "Center Field":str(self.game.pitchingteam.centerfield),
            "Right Field":str(self.game.pitchingteam.rightfield),
            "Skip_Bool": self.game.skip_bool,
            "Baselines": str(self.game.baselines)
            }


        

    def PostPitch(self):
        #print(f"{self.id}{self.defensiveoutcome}")
        if self.game.is_strikeout == False:
            WalkEval(self) 
            if self.defensiveoutcome != None:
                HitEval(self)        

    def Processing(self):
        #print(self.game.outcount)
        self.game.currentouts += self.game.outcount
        #print(f"Runners Home: {len([])}")#{len(self.game.current_runners_home)}")
        self.game.battingteam.score += len(self.game.current_runners_home)
        for runners in self.game.current_runners_home:
            runners.battingstats.Adder("runs", 1)
            #print(f"RUNNERS CHECK: {runners.earned_bool} {runners.on_base_pitcher}")
            
        self.game.actions.append(self.ActionPrint())#[self.game.error_count, self.game.currentinning, self.game.topofinning, self.game.currentouts, self.game.outcount, self.game.hometeam.name, self.game.hometeam.score, self.game.awayteam.name, self.game.awayteam.score, self.game.battingteam.name, self.game.battingteam.currentbatspot, self.game.pitchingteam.name, self.game.pitchingteam.currentbatspot, self.game.currentstrikes, self.game.currentballs, self.game.battingteam.currentbatter, self.outcome, self.game.on_firstbase, self.game.on_secondbase, self.game.on_thirdbase, len(self.game.current_runners_home), self.defensiveoutcome, self.game.skip_bool, [self.game.is_single, self.game.is_double, self.game.is_triple, self.game.is_homerun]])
        NextAction(self)
        NextAtBat(self)        

        if self.game.outcount > 0:
            OutProcessor(self)
        #fi.Fatigue()
        

def HitEval(self):
    #print(f"DEFENSIVE OUTCOME: {self.defensiveoutcome[4]}")
   
    self.game.on_firstbase = self.defensiveoutcome[4][0]
    self.game.on_secondbase = self.defensiveoutcome[4][1]
    self.game.on_thirdbase = self.defensiveoutcome[4][2]
    if self.defensiveoutcome[4][3] != None:
        listofrunners = self.defensiveoutcome[4][3]#.copy()
        #print(f"SELF DEFENSIVEOUTCOME: ::: {len(listofrunners)}")
        for runner in listofrunners:
            self.game.current_runners_home.append(runner)

                
def WalkEval(self):
    if self.game.is_walk == True:
        self.game.battingteam.currentbatter.battingstats.Adder("walks", 1)

    if self.game.is_hbp == True:
        self.game.battingteam.currentbatter.battingstats.Adder("hbp", 1)        

    if self.game.is_walk == True or self.game.is_hbp == True:
        if self.game.on_firstbase == None:
            self.game.on_firstbase = self.game.battingteam.currentbatter
            self.game.on_firstbase.battingstats.Adder("bases", 1)
            return
        if self.game.on_firstbase != None:
            if self.game.on_secondbase == None:
                self.game.on_secondbase = self.game.on_firstbase
                self.game.on_firstbase = self.game.battingteam.currentbatter
                self.game.on_firstbase.battingstats.Adder("bases", 1)
                self.game.on_secondbase.battingstats.Adder("bases", 1)
                return
            if self.game.on_secondbase != None:
                if self.game.on_thirdbase == None:
                    self.game.on_thirdbase = self.game.on_secondbase
                    self.game.on_secondbase = self.game.on_firstbase
                    self.game.on_firstbase = self.game.battingteam.currentbatter
                    self.game.on_thirdbase.battingstats.Adder("bases", 1)
                    self.game.on_secondbase.battingstats.Adder("bases", 1)
                    self.game.on_firstbase.battingstats.Adder("bases", 1)
                    return
                if self.game.on_thirdbase != None:
                    self.game.current_runners_home.append(self.game.on_thirdbase)
                    self.game.on_thirdbase.battingstats.Adder("bases", 1)
                    self.game.on_thirdbase = self.game.on_secondbase
                    self.game.on_secondbase = self.game.on_firstbase
                    self.game.on_firstbase = self.game.battingteam.currentbatter
                    self.game.on_thirdbase.battingstats.Adder("bases", 1)
                    self.game.on_secondbase.battingstats.Adder("bases", 1)
                    self.game.on_firstbase.battingstats.Adder("bases", 1)
                    return

        


    else:
        pass    

def NextAction(self):
    self.game.pitchingteam.TickPitcherStamina()
    self.game.is_pickoff = False
    self.game.is_stealattempt = False
    self.game.is_stealsuccess = False
    self.game.batted_ball = None
    self.game.air_or_ground = None
    self.game.targeted_defender = None
    self.game.current_runners_home = []
  
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
        self.game.pitchingteam.currentpitcher.pitchingstats.Adder("strikeouts", 1)
        self.game.outcount+=1
        
    if self.outcome[0] == 'Ball':
        self.game.currentballs +=1
    
    if self.game.currentballs >= self.game.rules.balls:
        stats.SetPitcherStatus(self.game.battingteam.currentbatter, self.game.pitchingteam.currentpitcher, True)        
        self.game.ab_over = True
        self.game.is_walk = True
        

    #print(outcome[1])
    #print(f"input: {self.outcome[1]}")
    #print(f"{self.outcome[1] in ('far left' or 'left' or 'center left' or 'dead center' or 'center right' or 'right' or 'far right')} | {self.outcome[1]}")
    if self.outcome[1] in ('far left', 'left', 'center left', 'dead center', 'center right', 'right', 'far right'):
        #print("event fired")
        self.defensiveoutcome = d.fielding(self).defenseoutcome
        #print(f"{self.id}{self.defensiveoutcome}")
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
    self.game.pitchingteam.TickInningsPlayed()
    WalkoffCheck(self)  
    if (self.game.currentouts) < self.game.rules.outs:
        #self.game.currentouts += self.game.outcount 
        self.game.outcount = 0
    elif (self.game.currentouts + self.game.outcount) >= self.game.rules.outs:
        InningFlip(self)    

def InningFlip(self):
    for player in self.game.battingteam.roster.playerlist:
        stats.ResetPitcherStatus(player)

    if self.game.topofinning == True:
        score = self.game.awayteam.score
    else:
        score = self.game.hometeam.score
    self.game.overallresults.append(stats.InningStats(self.game.currentinning, self.game.battingteam.name, score))    
    
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
    
