import random

weights = {
    "barrel": [ .57, .28, .10, .05, .00, .00, .00, .00, .00],
    "solid":  [ .10, .20, .25, .20, .15, .10, .00, .00, .00],
    "flare":  [ .00, .00, .25, .35, .25, .10, .05, .00, .00],
    "burner": [ .00, .00, .00, .00, .20, .60, .20, .00, .00],
    "under":  [ .00, .00, .00, .05, .15, .25, .35, .15, .05],
    "topped": [ .00, .00, .00, .00, .00, .20, .40, .30, .10],
    "weak":   [ .00, .00, .00, .00, .00, .00, .30, .40, .30]
    }

fieldingerrorrate = 0.01

throwingerrorrate = 0.01

outcomes = [
    'homerun',
    'deep_of',
    'middle_of',
    'shallow_of',
    'deep_if',
    'middle_if',
    'shallow_if',
    'mound',
    'catcher'
    ]

defensivealignment = {
    "far left": {
        'deep_of': ['leftfield'], 
        'middle_of': ['leftfield'], 
        'shallow_of':['leftfield'], 
        'deep_if':['thirdbase'], 
        'middle_if':['thirdbase'], 
        'shallow_if':['thirdbase'], 
        'mound': ['thirdbase', 'pitcher'], 
        'catcher': ['catcher']
        },
    "left": {
        'deep_of': ['leftfield'], 
        'middle_of': ['leftfield'], 
        'shallow_of':['leftfield'], 
        'deep_if':['shortstop'], 
        'middle_if':['shortstop'], 
        'shallow_if':['shortstop', 'thirdbase'], 
        'mound': ['thirdbase', 'shortstop', 'pitcher'], 
        'catcher': ['catcher']
        },
    "center left": {
        'deep_of': ['centerfield', 'leftfield'], 
        'middle_of': ['centerfield', 'leftfield'], 
        'shallow_of':['centerfield', 'leftfield'], 
        'deep_if':['shortstop'], 
        'middle_if':['shortstop'], 
        'shallow_if':['shortstop'], 
        'mound': ['shortstop', 'pitcher'], 
        'catcher': ['catcher']
        },
    "dead center": {
        'deep_of': ['centerfield'], 
        'middle_of': ['centerfield'], 
        'shallow_of':['centerfield'], 
        'deep_if':['shortstop', 'secondbase'], 
        'middle_if':['shortstop', 'secondbase'], 
        'shallow_if':['shortstop', 'secondbase'], 
        'mound': ['pitcher'], 
        'catcher': ['catcher']
        },
    "center right": {
        'deep_of': ['centerfield', 'rightfield'], 
        'middle_of': ['centerfield', 'rightfield'], 
        'shallow_of':['centerfield', 'rightfield'], 
        'deep_if':['secondbase'], 
        'middle_if':['secondbase'], 
        'shallow_if':['secondbase'], 
        'mound': ['secondbase', 'pitcher'], 
        'catcher': ['catcher']
        },
    "right": {
        'deep_of': ['rightfield'], 
        'middle_of': ['rightfield'], 
        'shallow_of':['rightfield'], 
        'deep_if':['secondbase'], 
        'middle_if':['secondbase'], 
        'shallow_if':['secondbase', 'firstbase'], 
        'mound': ['firstbase', 'secondbase', 'pitcher'], 
        'catcher': ['catcher']
        },
    "far right": {
        'deep_of': ['rightfield'], 
        'middle_of': ['rightfield'], 
        'shallow_of':['rightfield'], 
        'deep_if':['firstbase'], 
        'middle_if':['firstbase'], 
        'shallow_if':['firstbase'], 
        'mound': ['firstbase', 'pitcher'], 
        'catcher': ['catcher']
        } 
    }

freehit = [
    ('far left', 'shallow_of'), 
    ('center left', 'shallow_of'), 
    ('center right', 'shallow_of'), 
    ('far right', 'shallow_of'), 
    ('left', 'deep_if'), 
    ('dead center', 'deep_if'), 
    ('right', 'deep_if'), 
    ('left', 'middle_if'), 
    ('dead center', 'middle_if'), 
    ('right', 'middle_if') 
    ]

directlyat = [
    ('left', 'middle_of'),
    ('dead center', 'middle_of'), 
    ('right', 'middle_of'), 
    ('far left', 'middle_if'), 
    ('center left', 'middle_if'), 
    ('center right', 'middle_if'), 
    ('far right', 'middle_if'),
    ('dead center', 'mound'), 
    ('far left', 'catcher'), 
    ('left', 'catcher'), 
    ('center left', 'catcher'), 
    ('dead center', 'catcher'), 
    ('center right', 'catcher'), 
    ('right', 'catcher'),
    ('far right', 'catcher')
    ]

onestepaway = [
    ('far left', 'deep_if'),
    ('center left', 'deep_if'),
    ('center right', 'deep_if'),
    ('far right', 'deep_if'),
    ('left', 'middle_if'),
    ('dead center', 'middle_if'),
    ('right', 'middle_if'),
    ('far left', 'shallow_if'),
    ('left', 'shallow_if'),
    ('center left', 'shallow_if'),
    ('dead center', 'shallow_if'),
    ('center right', 'shallow_if'),
    ('right', 'shallow_if'),
    ('far right', 'shallow_if'),
    ('left', 'mound'),
    ('center left', 'mound'),
    ('center right', 'mound'),
    ('right', 'mound'),
    ('far right', 'mound') 
    ]

twostepaway = [
    ('left', 'deep_of'),
    ('dead center', 'deep_of'),
    ('right', 'deep_of'),
    ('far left', 'middle_of'),
    ('center left', 'middle_of'),
    ('center right', 'middle_of'),
    ('far right', 'middle_of'),
    ('left', 'shallow_of'),
    ('dead center', 'shallow_of'),
    ('right', 'shallow_of'),
    ('left', 'deep_if'),
    ('dead center', 'deep_if'),
    ('right', 'deep_if')
    ]

threestepaway = [
    ('far left', 'deep_of'),
    ('center left', 'deep_of'),
    ('center right', 'deep_of'),
    ('far right', 'deep_of'),
    ('far left', 'shallow_of'),
    ('center left', 'shallow_of'),
    ('center right', 'shallow_of'),
    ('far right', 'shallow_of')
    ]


class ballmoving():
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.specificlocation = None
        self.fieldingdefender = None
        self.fieldingdefenderbackup = None
        self.weights = weights
        self.outcomes = outcomes
        self.defensivealignment = defensivealignment
        self.freehit = freehit
        self.directlyat = directlyat
        self.onestep = onestepaway
        self.twostep = twostepaway
        self.threestep = threestepaway
        #print(self.gamestate.outcome)
        self.defenseoutcome = self.SpecificLocationGenerator()
        
    def SpecificLocationGenerator(self):
        contacttype = self.gamestate.outcome[0]
        direction = self.gamestate.outcome[1]
        weights = self.weights[contacttype]
        outcomes = self.outcomes
        depth = random.choices(outcomes, weights, k=1)[0]
        
        if depth == 'homerun':
            self.gamestate.game.is_hit = True
            self.gamestate.game.is_homerun = True   
            #print(f"HOMERUN {contacttype} {direction} {depth}")
            return depth

        defenderlist = defensivealignment[direction][depth]

        primarydefender = [player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup==defenderlist[0]]
        if primarydefender == []:
            primarydefender = [self.gamestate.game.pitchingteam.currentpitcher]
        
        if (direction, depth) in freehit:
            self.gamestate.game.is_hit = True
            self.gamestate.game.is_inplay = True            
        else:
            #defensive stuff goes here, for now, auto-out
            self.gamestate.game.outcount+=1

        defenseoutcome = (direction, depth, primarydefender)
        if self.gamestate.game.is_inplay == True:
            self.CatchAttempt(defenseoutcome)
    
        return defenseoutcome
        
    def CatchAttempt(self, defenseoutcome):
        hittype = self.gamestate.outcome[0]
        distance = self.Distance(defenseoutcome)
        ballmoving.CatchEval(self, hittype, distance, defenseoutcome)
        
    def Distance(self, defenseoutcome):
        direction = defenseoutcome[0]
        depth = defenseoutcome[1]
        distance_from = 0

        directlyat = [outcome for outcome in self.directlyat if outcome == (direction, depth)]
        onestep = [outcome for outcome in self.onestep if outcome == (direction, depth)]
        twostep = [outcome for outcome in self.twostep if outcome == (direction, depth)]
        threestep = [outcome for outcome in self.threestep if outcome == (direction, depth)]
        
        #print(f"Test: {direction} {depth}")

        if len(directlyat)>0:
            distancefrom = 0
        elif len(onestep)>0:
            distancefrom = 1
        elif len(twostep)>0:
            distancefrom = 2
        elif len(threestep)>0:
            distancefrom = 3
        else:
            distancefrom = False
        
        return distancefrom

    def CatchEval(self, hittype, distance, defenseoutcome):
        dplayer = defenseoutcome[2]
        
        if hittype == 'barrel':
            distance += 2
        elif hittype == 'solid':
            distance += 1
        # elif hittype == 'flare':
        #     pass
        # elif hittype == 'burner':
        #     pass
        elif hittype == 'under':
            distance = min(0, distance-1)
        # elif hittype == 'topped':
        #     pass
        # elif hittype == 'weak':
        #     pass
        
        time = 0
        while distance > 0:
            time+=1
            distance -=1
        print(f"{hittype} {defenseoutcome} {time} {distance} {self.gamestate.game.battingteam.currentbatter}")
        
        if time==0:     
            self.gamestate.game.is_liveball = self.CatchAction(dplayer.fieldcatch, 'direct')
        else: 
            self.GetToIt(dplayer, time)
         
    def GetToIt(dplayer, time):
        react = dplayer.fieldreaction / 50
        speed = dplayer.speed / 50
        infield = ((react*3)+(speed))/4
        outfield = ((react)+(speed*3))/4 
        

    def CatchAction(playercatch, type):
        if type == 'direct':
            fieldingmod = playercatch / 50
            errorodds = fieldingmod *fieldingerrorrate
            is_caught = random.choices([True, False], [(1-errorodds), errorodds], k=1)[0]
            return is_caught
        if type == 'infield':
            pass
        if type == 'outfield':
            pass
        