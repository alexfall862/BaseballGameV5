import random
import InteractionEngine as ie
import copy
import Fatigue as f
import defense as d
import Steals as steals
import itertools
import Stats as stats


def player_ref(player):
    """Convert a player object to a serializable reference dict."""
    if player is None:
        return None
    return {
        "player_id": getattr(player, 'id', None),
        "player_name": f"{getattr(player, 'firstname', '')} {getattr(player, 'lastname', '')}"
    }


def player_list_ref(players):
    """Convert a list of players to serializable reference dicts."""
    if not players:
        return []
    return [player_ref(p) for p in players if p is not None]


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

        # Check for in-game injuries if injury system is available
        if hasattr(self.game, 'injury_adapter') and self.game.injury_adapter:
            from injury_system import InjurySystem
            if not hasattr(self.game, '_injury_system'):
                self.game._injury_system = InjurySystem(self.game.injury_adapter)

            # Check batter for injury
            batter = self.game.battingteam.currentbatter
            injury = self.game._injury_system.check_for_injury(batter, "atbat")
            if injury:
                if not hasattr(self.game, 'ingame_injury_reports'):
                    self.game.ingame_injury_reports = []
                self.game.ingame_injury_reports.append(injury)

            # Check pitcher for injury
            pitcher = self.game.pitchingteam.currentpitcher
            injury = self.game._injury_system.check_for_injury(pitcher, "pitch")
            if injury:
                if not hasattr(self.game, 'ingame_injury_reports'):
                    self.game.ingame_injury_reports = []
                self.game.ingame_injury_reports.append(injury)

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
        self.pitch_event = ie.PitchEvent(self)
        self.outcome = self.pitch_event.outcome
        #print(f"{self.game.currentinning:<3}{self.game.topofinning}|{self.game.currentouts:<1}-{self.game.outcount}| {self.game.hometeam.name:<3}{self.game.hometeam.score:>2} / {self.game.awayteam.name:<3}{self.game.awayteam.score:>2} ||| B: {self.game.battingteam.name:>3}{self.game.battingteam.currentbatspot} P: {self.game.pitchingteam.name:>3}{self.game.pitchingteam.currentbatspot}  CAB:{self.game.currentstrikes}/{self.game.currentballs} {self.outcome}")
        #print(self.outcome)
        #outcome = random.choices(['ball', 'strike', 'contact', 'hbp'], [0, 3, 1, 0], k=1)[0]
        AtBatOutcomeParser(self)
        Action.PostPitch(self)
        #print(f"{self.game.skip_bool} {self.id}{self.defensiveoutcome}")

    def ActionPrint(self):
        # Get modifier snapshot if ball was put in play
        at_bat_modifiers = None
        if (hasattr(self, 'pitch_event') and
            self.pitch_event is not None and
            self.pitch_event.batted_ball_event is not None):
            at_bat_modifiers = self.pitch_event.batted_ball_event.get_modifier_snapshot()

        # Get interaction phase data
        interaction_data = None
        if hasattr(self, 'pitch_event') and self.pitch_event is not None:
            interaction_data = self.pitch_event.get_phase_snapshot()

        return {
            "ID": self.id,
            "Inning": self.game.currentinning,
            "Inning Half": "Top" if self.game.topofinning else "Bottom",
            "Home Team": self.game.hometeam.name,
            "Home Score": self.game.hometeam.score,
            "Away Team": self.game.awayteam.name,
            "Away Score": self.game.awayteam.score,
            "Ball Count": self.game.currentballs,
            "Strike Count": self.game.currentstrikes,
            "Out Count": self.game.currentouts,
            "Outs this Action": self.game.outcount,
            "Batter": player_ref(self.game.battingteam.currentbatter),
            "Pitcher": player_ref(self.game.pitchingteam.currentpitcher),
            "Outcomes": str(self.outcome),
            "Batted Ball": str(self.game.batted_ball),
            "Air or Ground": str(self.game.air_or_ground),
            "Hit Depth": str(getattr(self.game, 'hit_depth', None)),
            "Hit Direction": str(getattr(self.game, 'hit_direction', None)),
            "Hit Situation": str(getattr(self.game, 'hit_situation', None)),
            "Catch Probability": getattr(self.game, 'catch_probability', None),
            "Targeted Defender": player_ref(self.game.targeted_defender) if hasattr(self.game.targeted_defender, 'id') else str(self.game.targeted_defender),
            "Defensive Outcome": str(self.defensiveoutcome[3] if self.defensiveoutcome != None else None),
            "Error List": str(self.defensiveoutcome[5] if self.defensiveoutcome != None else None),
            "Defensive Actions": str(self.defensiveoutcome[6] if self.defensiveoutcome != None else None),
            "On First": player_ref(self.game.on_firstbase),
            "On Second": player_ref(self.game.on_secondbase),
            "On Third": player_ref(self.game.on_thirdbase),
            "Home": player_list_ref(self.game.current_runners_home),
            "Is_Walk": self.game.is_walk,
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
            "Catcher": player_ref(self.game.pitchingteam.catcher),
            "First Base": player_ref(self.game.pitchingteam.firstbase),
            "Second Base": player_ref(self.game.pitchingteam.secondbase),
            "Third Base": player_ref(self.game.pitchingteam.thirdbase),
            "Shortstop": player_ref(self.game.pitchingteam.shortstop),
            "Left Field": player_ref(self.game.pitchingteam.leftfield),
            "Center Field": player_ref(self.game.pitchingteam.centerfield),
            "Right Field": player_ref(self.game.pitchingteam.rightfield),
            "At_Bat_Modifiers": at_bat_modifiers,
            "Interaction_Data": interaction_data,
        }


        

    def PostPitch(self):
        if self.game.is_strikeout == False:
            WalkEval(self) 
            if self.defensiveoutcome != None:
                HitEval(self)        

    def Processing(self):
        self.game.battingteam.score += len(self.game.current_runners_home)
        for runners in self.game.current_runners_home:
            stats.RunScorer(runners)
        self.game.actions.append(self.ActionPrint())#[self.game.error_count, self.game.currentinning, self.game.topofinning, self.game.currentouts, self.game.outcount, self.game.hometeam.name, self.game.hometeam.score, self.game.awayteam.name, self.game.awayteam.score, self.game.battingteam.name, self.game.battingteam.currentbatspot, self.game.pitchingteam.name, self.game.pitchingteam.currentbatspot, self.game.currentstrikes, self.game.currentballs, self.game.battingteam.currentbatter, self.outcome, self.game.on_firstbase, self.game.on_secondbase, self.game.on_thirdbase, len(self.game.current_runners_home), self.defensiveoutcome, self.game.skip_bool, [self.game.is_single, self.game.is_double, self.game.is_triple, self.game.is_homerun]])
        print(self.ActionPrint())
        NextAction(self)
        NextAtBat(self)        

        if self.game.outcount > 0:
            OutProcessor(self)
        #fi.Fatigue()
        

def HitEval(self):   
    self.game.on_firstbase = self.defensiveoutcome[4][0]
    self.game.on_secondbase = self.defensiveoutcome[4][1]
    self.game.on_thirdbase = self.defensiveoutcome[4][2]
    if self.defensiveoutcome[3] == "single" or self.defensiveoutcome[3] == "double" or self.defensiveoutcome[3] == "triple" or self.defensiveoutcome[3] == "homerun":
        listofrunners = self.defensiveoutcome[4][3]#.copy()
        for runner in listofrunners:
            self.game.current_runners_home.append(runner)

def WalkEval(self):
    if self.game.is_walk == True:
        self.game.battingteam.currentbatter.battingstats.Adder("walks", 1)
        self.game.battingteam.currentbatter.on_base_pitcher = self.game.pitchingteam.currentpitcher
        self.game.pitchingteam.currentpitcher.pitchingstats.Adder("walks", 1)
        walk_descript = f"{self.game.pitchingteam.currentpitcher.lineup} {self.game.pitchingteam.currentpitcher.name} walks {self.game.battingteam.currentbatter.lineup} {self.game.battingteam.currentbatter.name}"
        outcome = 'walk'

    if self.game.is_hbp == True:
        self.game.battingteam.currentbatter.battingstats.Adder("hbp", 1)        
        self.game.battingteam.currentbatter.on_base_pitcher = self.game.pitchingteam.currentpitcher
        self.game.pitchingteam.currentpitcher.pitchingstats.Adder("hbp", 1)
        walk_descript = f"{self.game.pitchingteam.currentpitcher.lineup} {self.game.pitchingteam.currentpitcher.name} hits {self.game.battingteam.currentbatter.lineup} {self.game.battingteam.currentbatter.name}"
        outcome = 'hbp'

    if self.game.is_walk == True or self.game.is_hbp == True:
        if self.game.on_firstbase == None:
            self.game.on_firstbase = self.game.battingteam.currentbatter
            self.game.on_firstbase.battingstats.Adder("bases", 1)
            self.defensiveoutcome = [None, None, None, outcome, [self.game.on_firstbase, self.game.on_secondbase, self.game.on_thirdbase, self.game.current_runners_home], [], [walk_descript]]
            return
        if self.game.on_firstbase != None:
            if self.game.on_secondbase == None:
                self.game.on_secondbase = self.game.on_firstbase
                self.game.on_firstbase = self.game.battingteam.currentbatter
                self.game.on_firstbase.battingstats.Adder("bases", 1)
                self.game.on_secondbase.battingstats.Adder("bases", 1)
                self.defensiveoutcome = [None, None, None, outcome, [self.game.on_firstbase, self.game.on_secondbase, self.game.on_thirdbase, self.game.current_runners_home], [], [walk_descript]]
                return
            if self.game.on_secondbase != None:
                if self.game.on_thirdbase == None:
                    self.game.on_thirdbase = self.game.on_secondbase
                    self.game.on_secondbase = self.game.on_firstbase
                    self.game.on_firstbase = self.game.battingteam.currentbatter
                    self.game.on_thirdbase.battingstats.Adder("bases", 1)
                    self.game.on_secondbase.battingstats.Adder("bases", 1)
                    self.game.on_firstbase.battingstats.Adder("bases", 1)
                    self.defensiveoutcome = [None, None, None, outcome, [self.game.on_firstbase, self.game.on_secondbase, self.game.on_thirdbase, self.game.current_runners_home], [], [walk_descript]]
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
                    self.defensiveoutcome = [None, None, None, outcome, [self.game.on_firstbase, self.game.on_secondbase, self.game.on_thirdbase, self.game.current_runners_home], [], [walk_descript]]
                    return

        


    else:
        pass    

def NextAction(self):
    self.game.pitchingteam.TickPitcherStamina()
    self.game.is_pickoff = False
    self.game.is_stealattempt = False
    self.game.is_stealsuccess = False
    self.game.is_inplay = False
    self.game.batted_ball = None
    self.game.air_or_ground = None
    self.game.targeted_defender = None
    self.game.hit_depth = None
    self.game.hit_direction = None
    self.game.hit_situation = None
    self.game.catch_probability = None
    self.game.current_runners_home = []
  
def NextAtBat(self):
    #print(self.game.ab_over)
    if self.game.ab_over == True:
        if self.game.is_walk  == True or self.game.is_hbp == True:
            pass
        else: 
            self.game.battingteam.currentbatter.battingstats.Adder("at_bats", 1)
        self.game.currentstrikes = 0
        self.game.currentballs = 0
        self.game.is_hit = False
        self.game.is_single = False        
        self.game.is_double = False
        self.game.is_triple = False
        self.game.is_homerun = False        
        self.game.is_walk = False
        self.game.is_hbp = False
        self.game.is_strikeout = False
        self.game.ab_over = False
        if self.game.on_firstbase != None:
            self.game.on_firstbase.earned_bool = True
        if self.game.on_secondbase != None:
            self.game.on_secondbase.earned_bool = True
        if self.game.on_thirdbase != None:
            self.game.on_thirdbase.earned_bool = True
        self.game.current_runners_home = []
        self.game.battingteam.TickBatter()
        self.game.pitchingteam.DecidePitchingChange()    

def AtBatOutcomeParser(self):

    if self.outcome[0] == 'Strike':
        self.game.pitchingteam.currentpitcher.pitchingstats.Adder("strikes", 1)
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
        self.game.battingteam.currentbatter.battingstats.Adder("strikeouts", 1)
        so_descript = f"{self.game.pitchingteam.currentpitcher.lineup} {self.game.pitchingteam.currentpitcher.name} strikes out {self.game.battingteam.currentbatter.lineup} {self.game.battingteam.currentbatter.name}"
        self.defensiveoutcome = [None, None, None, "strikeout", [self.game.on_firstbase, self.game.on_secondbase, self.game.on_thirdbase, self.game.current_runners_home], [], [so_descript]]

        self.game.outcount+=1
        
    if self.outcome[0] == 'Ball':
        self.game.pitchingteam.currentpitcher.pitchingstats.Adder("balls", 1)
        self.game.currentballs +=1
    
    if self.game.currentballs >= self.game.rules.balls:
        stats.SetPitcherStatus(self.game.battingteam.currentbatter, self.game.pitchingteam.currentpitcher, True)
        self.game.ab_over = True
        self.game.is_walk = True

    if self.outcome[0] == 'HBP':
        self.game.ab_over = True
        self.game.is_hbp = True
        stats.SetPitcherStatus(self.game.battingteam.currentbatter, self.game.pitchingteam.currentpitcher, True)

    if self.outcome[1] in ('far left', 'left', 'center left', 'dead center', 'center right', 'right', 'far right'):
        fielding_result = d.fielding(self)
        self.defensiveoutcome = fielding_result.defenseoutcome

        # Set game state fields from fielding result
        self.game.batted_ball = fielding_result.contacttype
        self.game.air_or_ground = "air" if fielding_result.airball_bool else "ground"
        self.game.targeted_defender = fielding_result.fieldingdefender
        self.game.is_inplay = True

        # Additional debugging fields from new catch_rates system
        self.game.hit_depth = fielding_result.depth
        self.game.hit_direction = fielding_result.direction
        self.game.hit_situation = fielding_result.situation
        self.game.catch_probability = getattr(fielding_result, 'catch_probability', None)

        # Set hit type flags based on defensive outcome
        outcome = self.defensiveoutcome[3]
        if outcome == "single":
            self.game.is_hit = True
            self.game.is_single = True
        elif outcome == "double":
            self.game.is_hit = True
            self.game.is_double = True
        elif outcome == "triple":
            self.game.is_hit = True
            self.game.is_triple = True
        elif outcome == "homerun":
            self.game.is_hit = True
            self.game.is_homerun = True

        # Set error count from error list
        self.game.error_count = len(self.defensiveoutcome[5]) if self.defensiveoutcome[5] else 0

        stats.OutcomeStatAdder(self.game.battingteam.currentbatter, self.game.pitchingteam.currentpitcher, self.defensiveoutcome[3])
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
    # Calculate how many outs can actually be credited this half-inning
    # Can't credit more outs than needed to end the inning (handles double/triple plays)
    outs_remaining_in_inning = self.game.rules.outs - self.game.currentouts
    outs_to_credit = min(self.game.outcount, outs_remaining_in_inning)

    # Credit innings only for outs that "count"
    for _ in range(outs_to_credit):
        self.game.pitchingteam.TickInningsPlayed()

    # Add the actual outs made to the count
    self.game.currentouts += self.game.outcount
    self.game.outcount = 0

    # Check for walkoff
    WalkoffCheck(self)

    # Check if inning should flip (now correctly triggers at 3 outs, not 4)
    if self.game.currentouts >= self.game.rules.outs:
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
    
