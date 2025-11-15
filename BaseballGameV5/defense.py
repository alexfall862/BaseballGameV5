from ast import Pass
import random
import Stats as stats
import numpy as np
from operator import attrgetter

class fielding():
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.test = self.gamestate.game.baselines.threestepaway
        self.distweights = self.gamestate.game.baselines.distweights
        self.distoutcomes = self.gamestate.game.baselines.distoutcomes
        self.defensivealignment = self.gamestate.game.baselines.defensivealignment
        self.fieldingweights = self.gamestate.game.baselines.fieldingweights
        self.fieldingoutcomes = self.gamestate.game.baselines.fieldingoutcomes
        self.errorlist = []
        self.defensiveactions = []

        self.contacttype = self.gamestate.outcome[0]
        self.direction = self.gamestate.outcome[1]

        self.specificweights = self.distweights[self.contacttype]
        self.depth = fielding.PickDepth(self)
        self.fieldingdefender = fielding.PickDefender(self)
        self.airball_bool = fielding.AirballBool(self.contacttype)
        self.adjustedfieldingweights = fielding.ModWeights(self.fieldingdefender, self.fieldingweights[self.contacttype], self.depth, self.airball_bool, self.gamestate.game.baselines.fieldingmod, self.gamestate.game.baselines.fieldingmultiplier)
        self.batted_ball_outcome = fielding.OutcomeChooser(self)
        self.basepaths = BasePaths(self, self.gamestate.game.battingteam.currentbatter, self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game)


        if self.batted_ball_outcome == 'homerun':
            self.target, self.targetbase = None, None
            self.basepaths.HandleHomeRun()
        else:
            if self.batted_ball_outcome == 'out':
                error_on_catch, d_action = Error_Catch(self, None, self.fieldingdefender)
                self.defensiveactions.append(d_action)
                if error_on_catch == True:
                    self.basepaths.RunnerMover("fielding error")

                    self.target, self.targetbase = self.basepaths.WhereToThrow()

                    self.basepaths.RunnerCheck(self.target, self.targetbase)
                    self.target, self.targetbase = self.basepaths.WhereToThrow()

                    if len([runner for runner in self.basepaths.baserunner_eval_list if runner.running == True])>0:
                        fielding.ExecuteThrow(self)
                        
                elif error_on_catch == False:
                    self.basepaths.RunnerOut(self.basepaths.batter)


            if self.batted_ball_outcome != 'out':
                self.basepaths.RunnerMover(self.batted_ball_outcome)

                self.target, self.targetbase = self.basepaths.WhereToThrow()
                self.basepaths.RunnerCheck(self.target, self.targetbase)

                if len([runner for runner in self.basepaths.baserunner_eval_list if runner.running == True])>0:
                    print("RUNNING")
                    #print("After non-out play")
                    self.target, self.targetbase = self.basepaths.WhereToThrow()
                    fielding.ExecuteThrow(self)
                    self.basepaths.RunnerMover("single")
                    
                
        self.base_situation = self.basepaths.RunnerConverter()
        
        self.defenseoutcome = (self.contacttype, self.direction, self.fieldingdefender, self.batted_ball_outcome, self.base_situation, self.errorlist, self.defensiveactions)


    def DefenseChoice(self):
        if (self.gamestate.game.outcount + self.gamestate.game.currentouts) >= self.gamestate.game.rules.outs:
            throw_it_bool = False
        elif (self.gamestate.game.outcount + self.gamestate.game.currentouts) < self.gamestate.game.rules.outs:
            throw_it_bool = True
        return throw_it_bool

    def ExecuteThrow(self):
        def PickCatchingDefender(self):
            if self.targetbase == 0:
                position = "firstbase"            
            elif self.targetbase == 1:
                position = "secondbase"            
            elif self.targetbase == 2:
                position = "thirdbase"            
            elif self.targetbase == 3:
                position = "catcher"            

            catching_defender = [player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup==position][0]

            if catching_defender == self.fieldingdefender:
                if self.fieldingdefender.lineup == "firstbase":
                    catching_defender = self.gamestate.game.pitchingteam.currentpitcher# [player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup=="pitcher"][0]
                if self.fieldingdefender.lineup == "secondbase":
                    catching_defender = [player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup=="shortstop"][0]
                if self.fieldingdefender.lineup == "thirdbase":
                    catching_defender = [player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup=="shortstop"][0]
                if self.fieldingdefender.lineup == "catcher":
                    catching_defender = self.gamestate.game.pitchingteam.currentpitcher #[player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup=="pitcher"][0]
            return catching_defender
    
        catcher = PickCatchingDefender(self)

        throw, catch, d_action = Error_Throw_Catch(self, self.fieldingdefender, catcher)
        self.defensiveactions.append(d_action)
        if throw == True:
            pass
        if catch == True:
            pass
        if throw and catch == False:
            fielding.PickRunnerToRemove(self)
        self.fieldingdefender = catcher
        

    def PickRunnerToRemove(self):
        if self.targetbase == 0: 
            runner = [runner for runner in self.basepaths.baserunner_eval_list if runner.base == 0][0]
            self.basepaths.RunnerOut(runner)
        elif self.targetbase == 1:
            runner = [runner for runner in self.basepaths.baserunner_eval_list if runner.base == 1][0]            
            self.basepaths.RunnerOut(runner)
        elif self.targetbase == 2:
            runner = [runner for runner in self.basepaths.baserunner_eval_list if runner.base == 2][0]
            self.basepaths.RunnerOut(runner)
        elif self.targetbase == 3:
            runner = [runner for runner in self.basepaths.baserunner_eval_list if runner.base == 3][0]
            self.basepaths.RunnerOut(runner)
            

    def PickDepth(self):
        depth = random.choices(self.distoutcomes, self.specificweights, k=1)[0]
        return depth
        
    def PickDefender(self):        
        if self.depth == 'homerun':
            primary_defender = None
        else:
            weight = 1
            listofweights = []
            defenderlist = self.defensivealignment[self.direction][self.depth]
            
            for item in range(0, len(defenderlist)):
                listofweights.append(weight)
                weight = (weight *.5)

            defenderposition = random.choices(defenderlist, listofweights, k=1)[0]

            try:
                primary_defender = [player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup==defenderposition][0]
            except:
                primary_defender = self.gamestate.game.pitchingteam.currentpitcher

        return primary_defender

    def AirballBool(contacttype):
        if contacttype == "homerun":
            airball_bool = None
        elif contacttype == "barrel" or "solid" or "flare" or "under":
            airball_bool = True
        else:
            airball_bool = False
        return airball_bool

    def ModWeights(defender, fieldingodds, depth, airball_bool, mod, multiplier):
        if defender == None:
            return [0,0,0,0]
        
        if airball_bool == True:
            ab = 'air'
        else:
            ab = 'ground'
        if '_of' in depth:
            d = 'outfield'
        else:
            d = 'infield'

        #print(f"Type:{ab} In/Out:{d}")

        outodds = fieldingodds[0]
        singleodds = fieldingodds[1]
        doubleodds = fieldingodds[2]
        tripleodds = fieldingodds[3]
        sumvalue = sum([outodds, singleodds, doubleodds, tripleodds])
        skills = [defender.fieldcatch, defender.fieldreact, defender.fieldspot, defender.speed]
        skillsweight = mod[ab][d]

        modifier = (((np.average(skills, weights=skillsweight))/50)+multiplier)/(multiplier+1)

        outodds *= modifier
        singleodds /= modifier
        doubleodds /= modifier
        tripleodds /= modifier
        listofodds = [outodds, singleodds, doubleodds, tripleodds]
        processedodds = [x / sum(listofodds) for x in listofodds]
        outodds = processedodds[0]
        singleodds = processedodds[1]
        doubleodds = processedodds[2]
        tripleodds = processedodds[3]
        processedlistofodds = [outodds, singleodds, doubleodds, tripleodds]        
        return processedlistofodds

    def OutcomeChooser(self):
        if self.depth == 'homerun':
            outcome = 'homerun'
        else:
            #print(f"{self.gamestate.game.baselines.fieldingoutcomes} {self.adjustedfieldingweights}")
            outcome = random.choices(self.gamestate.game.baselines.fieldingoutcomes, self.adjustedfieldingweights, k=1)[0]
        #print(f"Outcome Picked {outcome}")
        return outcome 
    
def Error_Throw_Catch(self, thrower, catcher):
    throw, t_action = Error_Catch(self, thrower, catcher)
    catch, c_action = Error_Throw(self, thrower, catcher)
    defensiveaction = str(t_action) + " " + str(c_action)
    return throw, catch, defensiveaction

def Error_Catch(self, thrower, catcher):
    #print("catch error")
    baselines = self.gamestate.game.baselines        
    if thrower != None:
        depth = Throw_CatchDepth(thrower)
    elif thrower == None:
        if catcher.lineup == 'leftfield' or catcher.lineup == 'centerfield' or catcher.lineup == 'rightfield':
            depth = 'outfield'
        else:
            depth = 'infield'
                
    diceroll = np.random.rand()
    cfs = (catcher.fieldspot - 50)/50
    cfr = (catcher.fieldreact - 50)/50
    cfc = (catcher.fieldcatch - 50)/50
    cscores = [cfs, cfr, cfc]
    if depth == 'outfield':
        cweights = [4, 2, 3]
    elif depth == 'infield':
        cweights = [1, 2, 3]   
    error_rate = (1+np.average(cscores, weights=cweights))*baselines.error_rate
    if error_rate > diceroll:
        self.basepaths.RunnerMover("fielding error")
        self.errorlist.append(f"{catcher} catching error!")
        catcher.fieldingstats.Adder("catching_errors", 1)
        return True, f"error by {catcher.lineup} {catcher.name}"
    else: 
        if thrower == None:
            return False, f"Ball caught by {catcher.lineup} {catcher.name}"        
        else:
            return False, f"{thrower.lineup} {thrower.name}'s throw caught by {catcher.lineup} {catcher.name}"        

def Error_Throw(self, thrower, catcher):
    #print("throw error")
    baselines = self.gamestate.game.baselines        
    if thrower != None:
        depth = Throw_CatchDepth(thrower)
    elif thrower == None:
        if thrower.lineup == 'leftfield' or thrower.lineup == 'centerfield' or thrower.lineup == 'rightfield':
            depth = 'outfield'
        else:
            depth = 'infield'        

    diceroll = np.random.rand()
    tta = (thrower.throwacc - 50)/50
    ttp = (thrower.throwpower - 50)/50
    cscores = [tta, ttp]
    if depth  == 'outfield':
        cweights = [2, 1]
    elif depth == 'infield':
        cweights = [1, 0]

    error_rate = (1+np.average(cscores, weights=cweights))*baselines.error_rate
    #print(f"BASELINE ERROR FORM CHECK THROW: {error_rate}/{diceroll}")
    if error_rate > diceroll:
        #print(True)
        self.basepaths.RunnerMover("throwing error")
        self.errorlist.append(f"{thrower} throws it wide!")
        thrower.fieldingstats.Adder("throwing_errors", 1)
        return True, f"error by {thrower.lineup} {thrower.name}"
    else: 
        return False, f"{thrower.lineup} {thrower.name} throws it to {catcher.lineup} {catcher.name}"        

def Throw_CatchDepth(thrower):
    if thrower.lineup == 'leftfield' or thrower.lineup == 'centerfield' or thrower.lineup == 'rightfield':
        return 'outfield'
    else:
        return 'infield'

class BasePaths():
    def __init__(self, fielding, batter, firstbase, secondbase, thirdbase, game):
        self.fielding = fielding
        self.batter = batter
        self.firstbase = firstbase
        self.secondbase = secondbase
        self.thirdbase = thirdbase
        self.game = game

        self.baserunner_eval_list = []
        if self.batter != None:
            self.baserunner_eval_list.append(batter)
            self.batter.base = 0
            self.batter.running = True
            self.batter.on_base_pitcher = self.game.pitchingteam.currentpitcher
        if self.firstbase != None:
            self.baserunner_eval_list.append(firstbase)
            self.firstbase.base = 1
        if self.secondbase != None:
            self.baserunner_eval_list.append(secondbase)
            self.secondbase.base = 2
        if self.thirdbase != None:
            self.baserunner_eval_list.append(thirdbase)
            self.thirdbase.base = 3
        self.at_home = []
        self.out = []            

    def __repr__(self):
        return f"Baserunners: {self.baserunner_eval_list} Home: {self.at_home} Out: {self.out}"

    def RunnerOut(self, player):   
        player.base = None
        player.running = None
        player.out = True
        self.game.outcount +=1
        self.baserunner_eval_list.remove(player)

    def RunnerMover(self, outcome):

        def AdvanceRunners(self):

            for runner in self.baserunner_eval_list:



                runner.base+=1
                if len(self.fielding.errorlist) >= 1:
                    runner.earned_bool = False
                if runner.base > 3:
                    #runner.base = None
                    runner.running = None


                    self.at_home.append(runner)
                    self.baserunner_eval_list.remove(runner)

        if outcome == "single":
            AdvanceRunners(self)
        if outcome == "double":
            AdvanceRunners(self)
            AdvanceRunners(self)
        if outcome == "triple":
            AdvanceRunners(self)
            AdvanceRunners(self)
            AdvanceRunners(self)
        if outcome == "throwing error":
            AdvanceRunners(self)
        if outcome == "fielding error":
            pass
        for runner in self.baserunner_eval_list:
            runner.running = None               
                
    def RunnerConverter(self):
        try:
            self.firstbase = [runner for runner in self.baserunner_eval_list if runner.base == 1][0]            
        except:
            self.firstbase = None
                               
        try:
            self.secondbase = [runner for runner in self.baserunner_eval_list if runner.base == 2][0]            
        except:
            self.secondbase = None
                               
        try:
            self.thirdbase = [runner for runner in self.baserunner_eval_list if runner.base == 3][0]            
        except:
            self.thirdbase = None
        return [ self.firstbase, self.secondbase, self.thirdbase, self.at_home]

    def RunnerCheck(self, target, targetbase):
        for runner in self.baserunner_eval_list:
            #print(runner.base, runner.name, runner.speed, runner.baserunning)
            runner.running = None

        if self.batter.base == 0:
            #print("RUNNING")
            self.batter.running = True

    def WhereToThrow(self):
        #print(f"Running WHERE TO THROW")
        try: 
            highestbase = max(self.baserunner_eval_list, key=attrgetter('base')).base
        except: 
            return "no runners", None

        def CheckForForce(self, highestbase):
            if (highestbase == None) or (len(self.baserunner_eval_list) == 0):
                return None, None
            else:
                self.baserunner_eval_list.sort(key=lambda runner: runner.base, reverse=True)
                for player in self.baserunner_eval_list:
                    if player.running == True:
                        target = player 
                        highestbase = player.base
                        return target, highestbase     
                    else: 
                        pass
                return None, None
                
        target, targetbase = CheckForForce(self, highestbase)
        return target, targetbase
    def HandleHomeRun(self):
        for runner in self.baserunner_eval_list:
            self.at_home.append(runner)
            runner.base = None
            runner.running = None
        self.baserunner_eval_list = []

    def DecideToRun(self):
        for baserunner in self.baserunner_eval_list:

            needadvance = [baserunner for runner in self.baserunner_eval_list if (baserunner.base - 1) == runner.base]
            if needadvance != []:
                baserunner.running = True
        if (self.gamestate.game.currentouts + self.gamestate.game.outcount) == self.gamestate.game.rules.outs -1:
            for baserunner in self.baserunner_eval_list:
                baserunner.running = True
