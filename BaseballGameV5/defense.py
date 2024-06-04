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
        #self.freehit = freehit
        #self.directlyat = directlyat
        #self.onestep = onestepaway
        #self.twostep = twostepaway
        #self.threestep = threestepaway
        #print(self.gamestate.outcome)
        self.defenseoutcome = self.SpecificLocationGenerator()
        
    def SpecificLocationGenerator(self):
        contacttype = self.gamestate.outcome[0]
        direction = self.gamestate.outcome[1]
        distweights = self.distweights[contacttype]
        distoutcomes = self.distoutcomes
        depth = random.choices(distoutcomes, distweights, k=1)[0]
        
        if depth == 'homerun':
            self.gamestate.game.is_hit = True
            self.gamestate.game.is_homerun = True   
            #print(f"HOMERUN {contacttype} {direction} {depth}")
            return depth

        defenderlist = defensivealignment[direction][depth]

        primarydefender = [player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup==defenderlist[0]]
        if primarydefender == []:
            primarydefender = [self.gamestate.game.pitchingteam.currentpitcher]

        adjusted_weights = self.CatchAttempt(self.fieldingweights, contacttype, depth, primarydefender)
        batted_ball_outcome =  random.choices(self.fieldingoutcomes, adjusted_weights[0], k=1)[0]
        
        throw_outcome = self.ThrowDeterminer(direction, depth, batted_ball_outcome, adjusted_weights[1], primarydefender)
        

            


        defenseoutcome = (contacttype, direction, primarydefender, batted_ball_outcome)




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
        needthrow, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome = self.RunDeterminer(batted_ball_outcome, air_or_ground, primarydefender)
        print(f"Need? {needthrow} From Batter: {headingtofirst} From 1st: {headingtosecond} From 2nd: {headingtothird} From 3rd: {headingtohome} HOME: {alreadyhome}")
        if needthrow == True:
            target = ''
            if headingtohome == None:
                print(f'{batted_ball_outcome} {direction}/{depth} {primarydefender[0]}: no one heading to home')
            if headingtothird == None:
                print(f'{batted_ball_outcome} {direction}/{depth} {primarydefender[0]}: no one heading to third')
            if headingtosecond == None:
                print(f'{batted_ball_outcome} {direction}/{depth} {primarydefender[0]}: no one heading to second')
            if headingtofirst == None:
                print(f'{batted_ball_outcome} {direction}/{depth} {primarydefender[0]}: no one heading to first')
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
            print(target)
            ballcatcher = [player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup==target]
            if ballcatcher == []:
                ballcatcher = self.gamestate.game.pitchingteam.currentpitcher
            else:
                ballcatcher = ballcatcher[0]
            #print(f"Ball Catcher: {ballcatcher}")
            is_in_time, is_error, target = self.Throw_V_Run(primarydefender, ballcatcher, target)


        else: 
            pass

        #dostuff


        #isout = []
        #whoout = []
        #return isout, whoout

    def Throw_V_Run(primarydefender, target):
        is_in_time = True
        is_error = False
        return is_in_time, is_error, target

    def RunDeterminer(self, batted_ball_outcome, air_or_ground, primarydefender):
        strat = self.gamestate.game.battingteam.strategy

        headingtofirst = None
        headingtosecond = None
        headingtothird = None
        headingtohome = None
        alreadyhome = []
      
        if batted_ball_outcome == 'single':
            if self.gamestate.game.on_firstbase != None:
                headingtosecond = self.gamestate.game.on_firstbase
            if self.gamestate.game.on_secondbase != None:
                headingtothird = self.gamestate.game.on_secondbase
            if self.gamestate.game.on_thirdbase != None:
                headingtohome = self.gamestate.game.on_thirdbase
        elif batted_ball_outcome == 'double':
            if self.gamestate.game.on_firstbase != None:
                headingtothird = self.gamestate.game.on_firstbase
            if self.gamestate.game.on_secondbase != None:            
                headingtohome = self.gamestate.game.on_secondbase
            if self.gamestate.game.on_thirdbase != None:            
                alreadyhome = alreadyhome.append(self.gamestate.game.on_thirdbase)
        elif batted_ball_outcome == 'triple':
            if self.gamestate.game.on_firstbase != None:            
                headingtohome = self.gamestate.game.on_firstbase
            if self.gamestate.game.on_secondbase != None:
                alreadyhome = alreadyhome.append(self.gamestate.game.on_secondbase)
            if self.gamestate.game.on_thirdbase != None:
                alreadyhome = alreadyhome.append(self.gamestate.game.on_thirdbase)
        elif batted_ball_outcome == 'out':
            if air_or_ground == 'airball':
                #need to add getting current batter out 
                if (self.gamestate.game.currentouts + self.gamestate.game.outcount)-1 >= self.gamestate.game.rules.outs:
                    return False, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome              
                if primarydefender[0].throwpower < 40:
                    if self.gamestate.game.on_secondbase != None:
                        headingtothird = self.gamestate.game.on_secondbase
                    if self.gamestate.game.on_thirdbase != None:
                        headingtohome = self.gamestate.game.on_thirdbase
                    if primarydefender[0].throwpower <30:
                        if self.gamestate.game.on_firstbase != None:
                            headingtosecond = self.gamestate.game.on_firstbase
                else:
                    return False, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome

            elif air_or_ground == 'groundball':
                if (self.gamestate.game.currentouts + self.gamestate.game.outcount) -1 >= self.gamestate.game.rules.outs:
                    if self.gamestate.game.currentbatter != None:
                        headingtofirst = self.gamestate.game.currentbatter
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

        return True, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome

    #def GetToIt(self, dplayer, time):
    #    react = dplayer.fieldreact / 50
    #    speed = dplayer.speed / 50
    #    infield = ((react*3)+(speed))/4
    #    outfield = ((react)+(speed*3))/4 
        

    #def CatchAction(self, playercatch, type):
    #    if type == 'direct':
    #        fieldingmod = playercatch / 50
    #        errorodds = fieldingmod *fieldingerrorrate
    #        is_caught = random.choices([True, False], [(1-errorodds), errorodds], k=1)[0]
    #        return is_caught
    #    if type == 'infield':
    #        pass
    #    if type == 'outfield':
    #        pass
        