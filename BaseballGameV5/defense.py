from ast import Pass
import random

distweights = {
    "barrel": [ .50, .28, .10, .05, .00, .00, .00, .00, .00],
    "solid":  [ .10, .20, .25, .20, .15, .10, .00, .00, .00],
    "flare":  [ .00, .00, .25, .35, .25, .10, .05, .00, .00],
    "burner": [ .00, .00, .00, .00, .20, .60, .20, .00, .00],
    "under":  [ .00, .00, .00, .05, .15, .25, .35, .15, .05],
    "topped": [ .00, .00, .00, .00, .00, .20, .40, .30, .10],
    "weak":   [ .00, .00, .00, .00, .00, .00, .30, .40, .30]
    }

distoutcomes = [
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

fieldingweights = {
    "barrel": [ .25, .28, .10, .05],
    "solid":  [ .72, .20, .15, .01],
    "flare":  [ .52, .28, .20, .00],
    "burner": [ .52, .38, .10, .00],
    "under":  [ .92, .08, .00, .00],
    "topped": [ .88, .12, .00, .00],
    "weak":   [ .88, .12, .00, .00]
    }

fieldingoutcomes = [
    'out',
    'single',
    'double',
    'triple'
    ]

fieldingerrorrate = 0.01
throwingerrorrate = 0.01

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
        self.distweights = distweights
        self.distoutcomes = distoutcomes
        self.defensivealignment = defensivealignment
        self.fieldingweights = fieldingweights
        self.fieldingoutcomes = fieldingoutcomes
        self.defenseoutcome = self.SpecificLocationGenerator()
        
    def SpecificLocationGenerator(self):
        contacttype = self.gamestate.outcome[0]
        direction = self.gamestate.outcome[1]
        distweights = self.distweights[contacttype]
        distoutcomes = self.distoutcomes
        depth = random.choices(distoutcomes, distweights, k=1)[0]
        
            
        if depth == 'homerun':
            self.gamestate.game.is_homerun = True
            batted_ball_outcome = 'homerun'
            adjusted_weights = ["",""]
            primarydefender = [] 
            
            alreadyhome = []
            alreadyhome.append(self.gamestate.game.battingteam.currentbatter)
            if self.gamestate.game.on_firstbase != None:
                alreadyhome.append(self.gamestate.game.on_firstbase)                    
            if self.gamestate.game.on_secondbase != None:
                alreadyhome.append(self.gamestate.game.on_secondbase)                    
            if self.gamestate.game.on_thirdbase != None:
                alreadyhome.append(self.gamestate.game.on_thirdbase)                    

            headingtofirst = None
            headingtosecond = None
            headingtothird = None
            headingtohome = None

            base_situation = headingtofirst, headingtosecond, headingtothird, alreadyhome

        else:
            defenderlist = defensivealignment[direction][depth]

            primarydefender = [player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup==defenderlist[0]]
            if primarydefender == []:
                primarydefender = [self.gamestate.game.pitchingteam.currentpitcher]

            adjusted_weights = self.CatchAttempt(self.fieldingweights, contacttype, depth, primarydefender)
            batted_ball_outcome =  random.choices(self.fieldingoutcomes, adjusted_weights[0], k=1)[0]
            base_situation, errortype = self.ThrowDeterminer(direction, depth, batted_ball_outcome, adjusted_weights[1], primarydefender)
            if self.gamestate.game.error_count>0:
                batted_ball_outcome = errortype
            #[headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome]
            #print(f"Throw Outcome Test: {base_situation}")
        

        defenseoutcome = (contacttype, direction, primarydefender, batted_ball_outcome, base_situation)



        return defenseoutcome
        
    def CatchAttempt(self, fieldingweights, contacttype, depth, primarydefender):
        if depth == 'deep_of':
            weights = [1, 0]
        elif depth == 'middle_of':
            weights = [1, 0]
        elif depth == 'shallow_of':
            weights = [1, 0]
        elif depth == 'deep_if':
            weights = [.5, .5]
        elif depth == 'middle_if':
            weights = [.5, .5]
        elif depth == 'shallow_if':
            weights = [.25, .75]
        elif depth == 'mound':
            weights = [.25, .75]
        elif depth == 'catcher':
            weights = [.1, .9]

        air_or_ground = random.choices(['airball', 'groundball'], weights, k=1)[0]

        return (fieldingweights[contacttype], air_or_ground)

    def ThrowDeterminer(self, direction, depth, batted_ball_outcome, air_or_ground, primarydefender):
        needthrow, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, error_state = self.RunDeterminer(batted_ball_outcome, air_or_ground, primarydefender)
        #self.gamestate.game.current_runners_home = alreadyhome
        #print(f"Need? {needthrow} From Batter: {headingtofirst} From 1st: {headingtosecond} From 2nd: {headingtothird} From 3rd: {headingtohome} HOME: {alreadyhome}")
        if needthrow == True:
            target = ''
            if headingtohome == None:
                pass
                #print(f'{batted_ball_outcome} {direction}/{depth} {primarydefender[0]}: no one heading to home')
            if headingtothird == None:
                pass 
                #print(f'{batted_ball_outcome} {direction}/{depth} {primarydefender[0]}: no one heading to third')
            if headingtosecond == None:
                pass
                #print(f'{batted_ball_outcome} {direction}/{depth} {primarydefender[0]}: no one heading to second')
            if headingtofirst == None:
                pass
                #print(f'{batted_ball_outcome} {direction}/{depth} {primarydefender[0]}: no one heading to first')
            if (batted_ball_outcome== 'out'):
                if (self.gamestate.game.currentouts == self.gamestate.game.rules.outs-1):
                    if primarydefender[0].lineup == 'firstbase':
                        target = 'pitcher'
                    else: 
                        target = 'firstbase'
                elif (self.gamestate.game.currentouts == self.gamestate.game.rules.outs-2 and headingtosecond != None):                    
                    if primarydefender[0].lineup == 'secondbase':
                        target = 'shortstop'
                    else:
                        target = 'secondbase'
                    #try for double play
                elif headingtohome != None:
                    if primarydefender[0].lineup == 'catcher':
                        target = 'pitcher'
                    else:
                        target = 'catcher'
                else:
                    target = 'firstbase'
            else:
                target = 'firstbase'
            #print(target)
            ballcatcher = [player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup==target]
            if ballcatcher == []:
                ballcatcher = self.gamestate.game.pitchingteam.currentpitcher
            else:
                ballcatcher = ballcatcher[0]
            #print(f"Ball Catcher: {ballcatcher}")

            #need to match target with the runner
            if target == 'catcher':
                target_baserunner = headingtohome
            elif target == 'pitcher':
                target_baserunner = headingtofirst
            elif target == 'firstbase':
                target_baserunner = headingtofirst
            elif target == 'secondbase':
                target_baserunner = headingtosecond
            elif target == 'thirdbase':
                target_baserunner = headingtothird
            elif target == 'shortstop':
                target_baserunner = headingtosecond

            if (target == 'firstbase' and primarydefender[0].lineup == 'firstbase') or (target == 'secondbase' and primarydefender[0].lineup == 'secondbase') or (target == 'thirdbase' and primarydefender[0].lineup == 'thirdbase') or (target == 'catcher' and primarydefender[0].lineup == 'catcher'):
                if headingtohome != None:
                    alreadyhome.append(headingtohome)
                    headingtohome = None
                errors = []
                if error_state != None:
                    errors.append(error_state)                
                return [headingtofirst, headingtosecond, headingtothird, alreadyhome], errors 

            print(f"DEFENSIVE PLAY: {primarydefender[0].lineup} {target} {ballcatcher.lineup}")
            post_catch_error, errortype, error_text = self.Throw_V_Run(primarydefender[0], ballcatcher, target, target_baserunner)
            
            if post_catch_error == True:
                headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome = self.ErrorDeterminer(errortype, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, batted_ball_outcome)

                #print(f"NEXT LEVEL UP CHECK FOR ERROR: {batted_ball_outcome} {headingtofirst} {headingtosecond} {headingtothird} {headingtohome} {alreadyhome}")    
            
            #makeshift third base handler
            if headingtohome != None:
                alreadyhome.append(headingtohome)
                headingtohome = None
            errors = []
            if errortype != None:
                errors.append(error_text)
            if error_state != None:
                errors.append(error_state)
            return [headingtofirst, headingtosecond, headingtothird, alreadyhome], errors #errortype

        else: 
            print("Is this it?")
            post_catch_error, errortype, error_text = self.Throw_V_Run(primarydefender[0], None, None, None)
            if post_catch_error == True:
                headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome = self.ErrorDeterminer(errortype, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, batted_ball_outcome)
                #print(f"NEXT LEVEL UP CHECK FOR ERROR OUTS: {batted_ball_outcome} {headingtofirst} {headingtosecond} {headingtothird} {headingtohome} {alreadyhome}")    
            else:
                self.gamestate.game.outcount+=1

            
            #makeshift third base handler
            if headingtohome != None:
                alreadyhome.append(headingtohome)
                headingtohome = None
            errors = []                
            if errortype != None:
                errors.append(error_text)
            if error_state != None:
                errors.append(error_state)
            return [headingtofirst, headingtosecond, headingtothird, alreadyhome], errors#[]errortype

    def Throw_V_Run(self, primarydefender, ballcatcher, target, target_baserunner):
        print(f"DEFENSIVE PLAY: {primarydefender.lineup} {target} {ballcatcher.lineup}")
        fieldingerror = False
        throwingerror = False
        
        throwingerror, fieldingerror = self.gamestate.game.baselines.Throw_Catch(primarydefender, ballcatcher)

        if (fieldingerror == False and throwingerror == False):
            is_error = False
        if (fieldingerror == True or throwingerror == True):
            is_error = True

        if fieldingerror == True:
            self.gamestate.game.error_count+=1
        if throwingerror == True:
            self.gamestate.game.error_count+=1
            
        if (fieldingerror == False and throwingerror == False):
            errortype = None
        if (fieldingerror == True and throwingerror == False):
            errortype = f"fielding error"#" by {ballcatcher.lineup} {ballcatcher.name}"
            errortext = f"fielding error by {ballcatcher.lineup} {ballcatcher.name}"
            #can assign player specific error here as well if needed eventually.            
        if (fieldingerror == False and throwingerror == True):
            errortype = f"throwing error"#" by {primarydefender.lineup} {primarydefender.name}"
            errortext = f"throwing error by {primarydefender.lineup} {primarydefender.name}"
            #can assign player specific error here as well if needed eventually.
        if (fieldingerror == True and throwingerror == True):
            errortype = f"double error"#" by {primarydefender.lineup} {primarydefender.name} followed by a fielding error by {ballcatcher.lineup} {ballcatcher.name}"
            errortext = f"throwing error by {primarydefender.lineup} {primarydefender.name} followed by a fielding error by {ballcatcher.lineup} {ballcatcher.name}"
            print(errortext)
            #can assign player specific error here as well if needed eventually.

        if (fieldingerror == False and throwingerror == False) and (target_baserunner != None):
            primarydefender.fieldingstats.assists += 1
            ballcatcher.fieldingstats.putouts += 1
            #print(f"THROWN OUT RUNNING TO BASES: {self.gamestate.id} {target_baserunner}")
            self.gamestate.game.outcount += 1
            target_baserunner = None

        return is_error, errortype, errortext

    def ErrorDeterminer(self, error_state, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, batted_ball_outcome):     
        #print(f"PREPROCESS CHECK FOR ERROR: {batted_ball_outcome} {headingtofirst} {headingtosecond} {headingtothird} {headingtohome} {alreadyhome}")    
        if error_state == 'fielding error':
            if headingtohome != None:
                alreadyhome.append(headingtohome)
                headingtohome = None
            if headingtothird != None:
                headingtohome = headingtothird
                headingtothird = None
            if headingtosecond != None:
                headingtothird = headingtosecond                
                headingtosecond = None
            if headingtofirst != None:
                headingtosecond = headingtofirst
                headingtofirst = None
            #if batted_ball_outcome == 'out':
            #    headingtofirst = self.gamestate.game.battingteam.currentbatter
            #    self.gamestate.game.battingteam.currentbatter = None
            
        if error_state == 'throwing error':
            if headingtohome != None:
                alreadyhome.append(headingtohome)
                headingtohome = None
            if headingtothird != None:
                headingtohome = headingtothird
                headingtothird = None
            if headingtosecond != None:
                headingtothird = headingtosecond
                headingtosecond = None
            if headingtofirst != None:
                headingtosecond = headingtofirst
                headingtofirst = None
            #if batted_ball_outcome == 'out':
            #    headingtofirst = self.gamestate.game.battingteam.currentbatter
            #    self.gamestate.game.battingteam.currentbatter = None

        if error_state == 'double error':
            if headingtohome != None:
                alreadyhome.append(headingtohome)
                headingtohome = None
            if headingtothird != None:
                alreadyhome.append(headingtothird)
                headingtothird = None
            if headingtosecond != None:
                headingtohome = headingtosecond
                headingtosecond = None
            if headingtofirst != None:
                headingtothird = headingtofirst
                headingtofirst = None
            #if batted_ball_outcome == 'out':
            #    headingtofirst = self.gamestate.game.battingteam.currentbatter
            #   self.gamestate.game.battingteam.currentbatter = None

        #print(f"POSTPROCESS CHECK FOR ERROR: {batted_ball_outcome} {headingtofirst} {headingtosecond} {headingtothird} {headingtohome} {alreadyhome}")    
        return headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome

    def RunDeterminer(self, batted_ball_outcome, air_or_ground, primarydefender):
        strat = self.gamestate.game.battingteam.strategy
        self.gamestate.game.batted_ball = batted_ball_outcome
        self.gamestate.game.air_or_ground = air_or_ground
        self.gamestate.game.targeted_defender = primarydefender[0].lineup


        headingtofirst = None
        headingtosecond = None
        headingtothird = None
        headingtohome = None
        alreadyhome = []
        if batted_ball_outcome == 'single':
            self.gamestate.game.is_single = True
            headingtofirst = self.gamestate.game.battingteam.currentbatter
            if self.gamestate.game.on_firstbase != None:
                headingtosecond = self.gamestate.game.on_firstbase
            if self.gamestate.game.on_secondbase != None:
                headingtothird = self.gamestate.game.on_secondbase
            if self.gamestate.game.on_thirdbase != None:
                headingtohome = self.gamestate.game.on_thirdbase
        elif batted_ball_outcome == 'double':
            self.gamestate.game.is_double = True
            headingtosecond = self.gamestate.game.battingteam.currentbatter
            if self.gamestate.game.on_firstbase != None:
                headingtothird = self.gamestate.game.on_firstbase
            if self.gamestate.game.on_secondbase != None:            
                headingtohome = self.gamestate.game.on_secondbase
            if self.gamestate.game.on_thirdbase != None:            
                alreadyhome.append(self.gamestate.game.on_thirdbase)
        elif batted_ball_outcome == 'triple':
            self.gamestate.game.is_triple = True
            headingtothird = self.gamestate.game.battingteam.currentbatter
            if self.gamestate.game.on_firstbase != None:            
                headingtohome = self.gamestate.game.on_firstbase
            if self.gamestate.game.on_secondbase != None:
                alreadyhome.append(self.gamestate.game.on_secondbase)
            if self.gamestate.game.on_thirdbase != None:
                alreadyhome.append(self.gamestate.game.on_thirdbase)
        elif batted_ball_outcome == 'homerun':
            self.gamestate.game.is_homerun = True
            alreadyhome.append(self.gamestate.game.battingteam.currentbatter)            
            if self.gamestate.game.on_firstbase != None:
                alreadyhome.append(self.gamestate.game.on_firstbase)            
            if self.gamestate.game.on_secondbase != None:
                alreadyhome.append(self.gamestate.game.on_secondbase)            
            if self.gamestate.game.on_thirdbase != None:
                alreadyhome.append(self.gamestate.game.on_thirdbase)  
            return False, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, None

        elif batted_ball_outcome == 'out':
            print(f"{primarydefender[0].name} {primarydefender[0].lineup}")
            is_error = self.gamestate.game.baselines.CatchErrorEval(None, primarydefender[0])

            if is_error == True:
                self.gamestate.game.error_count += 1
                headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome = self.ErrorDeterminer('fielding error', self.gamestate.game.battingteam.currentbatter, self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, [], batted_ball_outcome)
                return True, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, f"XX fielding error by {primarydefender[0].name}"

            primarydefender[0].fieldingstats.putouts +=1
            if air_or_ground == 'airball':
                #need to add getting current batter out 
                if (self.gamestate.game.currentouts + self.gamestate.game.outcount)-1 >= self.gamestate.game.rules.outs:
                    return False, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, None
                if ([self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase]) == [None, None, None]:
                    return False, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, None                
                if primarydefender[0].throwpower < 40:
                    if self.gamestate.game.on_secondbase != None:
                        headingtothird = self.gamestate.game.on_secondbase
                    if self.gamestate.game.on_thirdbase != None:
                        headingtohome = self.gamestate.game.on_thirdbase
                    if primarydefender[0].throwpower <30:
                        if self.gamestate.game.on_firstbase != None:
                            headingtosecond = self.gamestate.game.on_firstbase
                else:
                    return False, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, None

            elif air_or_ground == 'groundball':
                if (self.gamestate.game.currentouts + self.gamestate.game.outcount) -1 >= self.gamestate.game.rules.outs:
                    if self.gamestate.game.battingteam.currentbatter != None:
                        headingtofirst = self.gamestate.game.battingteam.currentbatter
                    if self.gamestate.game.on_firstbase != None:
                        headingtosecond = self.gamestate.game.on_firstbase
                    if self.gamestate.game.on_secondbase != None:
                        headingtothird = self.gamestate.game.on_secondbase
                    if self.gamestate.game.on_thirdbase != None:
                        headingtohome = self.gamestate.game.on_thirdbase

                if self.gamestate.game.on_firstbase != None:
                    headingtosecond = self.gamestate.game.on_firstbase 

                if self.gamestate.game.on_secondbase != None:
                    if self.gamestate.game.on_firstbase != None:
                        headingtothird = self.gamestate.game.on_secondbase
                    else:
                        pass
                if self.gamestate.game.on_thirdbase != None:
                    if (self.gamestate.game.on_secondbase !=None and self.gamestate.game.on_firstbase !=None):
                        headingtohome = self.gamestate.game.on_thirdbase
                    else:                      
                        pass

        return True, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, None