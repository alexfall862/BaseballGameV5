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
        print(self.batted_ball_outcome)
        self.basepaths = fielding.BasePaths(self, self.gamestate.game.battingteam.currentbatter, self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase)
        print(f"BASES BEFORE RUNNING: {self.gamestate.game.battingteam.currentbatter, self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase}")


        if self.batted_ball_outcome == 'homerun':
            self.target, self.targetbase = None, None
            self.basepaths.HandleHomeRun()
        else:
            if self.batted_ball_outcome == 'out':
                error_on_catch = fielding.Error_Catch(self, None, self.fieldingdefender)
                #if (fielding.DefenseChoice(self) == False ):
                #    pass

                if error_on_catch == True:
                    #print("after error on intial catch")
                    self.basepaths.RunnerMover("fielding error")
                    for runner in self.basepaths.baserunner_eval_list:
                        print(f"EVAL CHECK: {runner} {runner.base}")


                    self.target, self.targetbase = self.basepaths.WhereToThrow()

                    self.basepaths.RunnerCheck(self.target, self.targetbase)
                    self.target, self.targetbase = self.basepaths.WhereToThrow()

                    if len([runner for runner in self.basepaths.baserunner_eval_list if runner.running == True])>0:
                        fielding.ExecuteThrow(self)
                        
                elif error_on_catch != False:
                    print("NON ERROR IS FIRING")
                    self.basepaths.RunnerOut(self.basepaths.batter)

    #                if len([runner for runner in self.basepaths.baserunner_eval_list if runner.running == True])<=0:
    #                    fielding.ExecuteThrow(self)


            if self.batted_ball_outcome != 'out':
                self.basepaths.RunnerMover(self.batted_ball_outcome)

                self.target, self.targetbase = self.basepaths.WhereToThrow()
                self.basepaths.RunnerCheck(self.target, self.targetbase)

                if len([runner for runner in self.basepaths.baserunner_eval_list if runner.running == True])>0:
                    #print("After non-out play")
                    self.target, self.targetbase = self.basepaths.WhereToThrow()
                    fielding.ExecuteThrow(self)
                    self.basepaths.RunnerMover("single")
                    
                
        self.base_situation = self.basepaths.RunnerConverter()
        
        self.defenseoutcome = (self.contacttype, self.direction, self.fieldingdefender, self.batted_ball_outcome, self.base_situation, self.errorlist, self.defensiveactions)

    class BasePaths():
        #should go in order of establishing initial positions, check to see whether they'd run before or after the catch (if there's a catch or not as well) - move basemen according to speed and bsrn ability if so, and then eval whether there's a catch or not and move again.
        def __init__(self, defense, batter, firstbase, secondbase, thirdbase):
            print(f"INSIDE OF BASEPATH OBJECT INIT: {batter, firstbase, secondbase, thirdbase}")            

            self.defense = defense
            self.batter = batter
            self.firstbase = firstbase
            self.secondbase = secondbase
            self.thirdbase = thirdbase

            self.baserunner_eval_list = []
            if self.batter != None:
                self.baserunner_eval_list.append(batter)
                self.batter.base = 0
                self.batter.running = True
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
            #print(player)
            player.base = None
            player.running = None
            player.out = True
            self.gamestate.game.outcount +=1
            #print(self.baserunner_eval_list)
            self.baserunner_eval_list.remove(player)
            #print(self.baserunner_eval_list)

        def RunnerMover(self, outcome):
            print(f"Inside Runner Mover: {self.batter, self.firstbase, self.secondbase, self.thirdbase}")
            print(f"{self.baserunner_eval_list}")
            def AdvanceRunners(self):
                #this is the place to add speed as a modifier
                for runner in self.baserunner_eval_list:
                    #print(f"RUNNER {runner.base} {runner}")


                    runner.base+=1
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
            print(f" |||||||| BEFORE: {self.batter, self.firstbase, self.secondbase, self.thirdbase}")            
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
            print(f" |||||||| AFTER: {None, self.firstbase, self.secondbase, self.thirdbase, self.at_home}")
            return [ self.firstbase, self.secondbase, self.thirdbase, self.at_home]

        def RunnerCheck(self, target, targetbase):
            print(f"DEFENDER {self.defense.fieldingdefender.lineup} {self.defense.fieldingdefender.throwpower} {self.defense.fieldingdefender.throwacc}")
            for runner in self.baserunner_eval_list:
                print(runner.base, runner.name, runner.speed, runner.baserunning)
                runner.running = None

            if self.batter.base == 0:
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

            #Return highest base having number
            #If outs aren't 1 less than total outs needed, 
                #Take player with that base
                #else throw to first
        def HandleHomeRun(self):
            for runner in self.baserunner_eval_list:
                self.at_home.append(runner)
                runner.base = None
                runner.running = None
            self.baserunner_eval_list = []

        def DecideToRun(self):
            for baserunner in self.baserunner_eval_list:
                #print(f"If Forced Eval: {baserunner}")
                print(f"{self.baserunner_eval_list}")
                needadvance = [baserunner for runner in self.baserunner_eval_list if (baserunner.base - 1) == runner.base]
                #print(f"Output: {needadvance}")
                if needadvance != []:
                    baserunner.running = True
                #print(f"{baserunner.running}")
            if (self.gamestate.game.currentouts + self.gamestate.game.outcount) == self.gamestate.game.rules.outs -1:
                for baserunner in self.baserunner_eval_list:
                    baserunner.running = True
                #print(f"Whether to Run Criteria: Def {self.defense.fieldingdefender} Depth {self.defense.depth} Direction {self.defense.direction} Airtime {self.defense.ball_airtime} Baserunner {baserunner}")

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

        #print(f"Target: {self.target}")
        #print(f"Target Base: {self.targetbase}")
        #print(f"Defender: {self.fieldingdefender}")
        #print(f"Catcher: {catcher}")

        throw, catch = fielding.Error_Throw_Catch(self, self.fieldingdefender, catcher)
        if throw == False:
            pass
        if catch == False:
            pass
        if throw and catch == True:
            fielding.PickRunnerToRemove(self)
        self.fieldingdefender = catcher
        

    def PickRunnerToRemove(self):
        #TEMP SOLUTION TO ADD TRY EXCEPT HERE
        #for runner in self.basepaths.baserunner_eval_list:
            #print(f"{runner.base} {runner}")
        #print(self.targetbase)
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
        #print(f"Skills {skills}")
        skillsweight = mod[ab][d]
        #print(f"Weights {skillsweight}")
        modifier = (((np.average(skills, weights=skillsweight))/50)+multiplier)/(multiplier+1)
        #print(f"Mod {modifier}")
        #print(f"OG Odds {fieldingodds}")
        outodds *= modifier
        singleodds /= modifier
        doubleodds /= modifier
        tripleodds /= modifier
        listofodds = [outodds, singleodds, doubleodds, tripleodds]
        #print(f"Output Odds {listofodds}")
        processedodds = [x / sum(listofodds) for x in listofodds]
        outodds = processedodds[0]
        singleodds = processedodds[1]
        doubleodds = processedodds[2]
        tripleodds = processedodds[3]
        processedlistofodds = [outodds, singleodds, doubleodds, tripleodds]        
        #print(f"Processed Odds {processedlistofodds}")
        return processedlistofodds

    # def TimeStep(self):
    #     test = random.randint(0,2)
    #     if test >= 2:
    #         self.liveball = False

    # def Air_TimeTick(self):
    #     location = [self.direction, self.depth]
    #     if location in self.gamestate.game.baselines.directlyat:
    #         distancefromdefender = 0
    #     if location in self.gamestate.game.baselines.onestepaway:
    #         distancefromdefender = 1        
    #     if location in self.gamestate.game.baselines.twostepaway:
    #         distancefromdefender = 2        
    #     if location in self.gamestate.game.baselines.threestepaway:
    #         distancefromdefender = 3
    #     if location in self.gamestate.game.baselines.homerun:
    #         distancefromdefender = 4

    #     if self.contacttype == "barrel" or "solid" or "flare" or "under" or "homerun":
    #         hit_ground = False
    #     else:
    #         hit_ground = True
    #     if self.depth == "homerun":
    #         timetoground = None
    #     else:
    #         timetoground = self.gamestate.game.baselines.timetoground[self.contacttype][self.depth]
       
    #     return distancefromdefender, hit_ground, timetoground

    def OutcomeChooser(self):
        if self.depth == 'homerun':
            outcome = 'homerun'
        else:
            #print(f"{self.gamestate.game.baselines.fieldingoutcomes} {self.adjustedfieldingweights}")
            outcome = random.choices(self.gamestate.game.baselines.fieldingoutcomes, self.adjustedfieldingweights, k=1)[0]
        #print(f"Outcome Picked {outcome}")
        return outcome 
    
    def Error_Throw_Catch(self, thrower, catcher):
        throw = fielding.Error_Catch(self, thrower, catcher)
        catch = fielding.Error_Throw(self, thrower, catcher)
        return throw, catch

    def Error_Catch(self, thrower, catcher):
        print("catch error")
        baselines = self.gamestate.game.baselines        
        if thrower != None:
            depth = fielding.Throw_CatchDepth(thrower)
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
            self.basepaths.RunnerMover("throwing error")
            self.errorlist.append(f"{catcher} catching error!")
            catcher.fieldingstats.Adder("catching_errors", 1)
            return True 
        else: 
            return False        

    def Error_Throw(self, thrower, catcher):
        print("throw error")
        baselines = self.gamestate.game.baselines        
        if thrower != None:
            depth = fielding.Throw_CatchDepth(thrower)
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
            return True 
        else: 
            return False        

    def Throw_CatchDepth(thrower):
        if thrower.lineup == 'leftfield' or thrower.lineup == 'centerfield' or thrower.lineup == 'rightfield':
            return 'outfield'
        else:
            return 'infield'

# class ballmoving():
#     def __init__(self, gamestate):
#         self.gamestate = gamestate
#         self.specificlocation = None
#         self.fieldingdefender = None
#         self.fieldingdefenderbackup = None
#         self.distweights = self.gamestate.game.baselines.distweights
#         self.distoutcomes = self.gamestate.game.baselines.distoutcomes
#         self.defensivealignment = self.gamestate.game.baselines.defensivealignment
#         self.fieldingweights = self.gamestate.game.baselines.fieldingweights
#         self.fieldingoutcomes = self.gamestate.game.baselines.fieldingoutcomes
#         self.defenseoutcome = self.SpecificLocationGenerator()
        
#     def SpecificLocationGenerator(self):
#         contacttype = self.gamestate.outcome[0]
#         direction = self.gamestate.outcome[1]
#         distweights = self.distweights[contacttype]
#         distoutcomes = self.distoutcomes
#         depth = random.choices(distoutcomes, distweights, k=1)[0]
        
            
#         if depth == 'homerun':
#             self.gamestate.game.is_homerun = True
#             stats.SetPitcherStatus(self.gamestate.game.battingteam.currentbatter, self.gamestate.game.pitchingteam.currentpitcher, True)
#             self.gamestate.game.battingteam.currentbatter.battingstats.Adder("homeruns", 1)
#             self.gamestate.game.battingteam.currentbatter.battingstats.Adder("bases", 4)
#             batted_ball_outcome = 'homerun'
#             self.gamestate.game.batted_ball = batted_ball_outcome
#             adjusted_weights = ["",""]
#             primarydefender = [] 
            
#             alreadyhome = []
#             alreadyhome.append(self.gamestate.game.battingteam.currentbatter)
#             if self.gamestate.game.on_firstbase != None:
#                 self.gamestate.game.on_firstbase.battingstats.Adder("bases", 3)
#                 alreadyhome.append(self.gamestate.game.on_firstbase)     
#             if self.gamestate.game.on_secondbase != None:
#                 self.gamestate.game.on_secondbase.battingstats.Adder("bases", 2)
#                 alreadyhome.append(self.gamestate.game.on_secondbase)                    
#             if self.gamestate.game.on_thirdbase != None:
#                 self.gamestate.game.on_thirdbase.battingstats.Adder("bases", 1)
#                 alreadyhome.append(self.gamestate.game.on_thirdbase)                    

#             headingtofirst = None
#             headingtosecond = None
#             headingtothird = None
#             headingtohome = None

#             base_situation = headingtofirst, headingtosecond, headingtothird, alreadyhome

#         else:
#             defenderlist = self.defensivealignment[direction][depth]

#             primarydefender = [player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup==defenderlist[0]]
#             if primarydefender == []:
#                 primarydefender = [self.gamestate.game.pitchingteam.currentpitcher]

#             adjusted_weights = self.CatchAttempt(self.fieldingweights, contacttype, depth, primarydefender)
#             batted_ball_outcome =  random.choices(self.fieldingoutcomes, adjusted_weights[0], k=1)[0]
#             base_situation, errortype = self.ThrowDeterminer(direction, depth, batted_ball_outcome, adjusted_weights[1], primarydefender)
#             if self.gamestate.game.error_count>0:
#                 batted_ball_outcome = errortype
        

#         defenseoutcome = (contacttype, direction, primarydefender, batted_ball_outcome, base_situation)



#         return defenseoutcome
        
#     def CatchAttempt(self, fieldingweights, contacttype, depth, primarydefender):
#         if depth == 'deep_of':
#             weights = [1, 0]
#         elif depth == 'middle_of':
#             weights = [1, 0]
#         elif depth == 'shallow_of':
#             weights = [1, 0]
#         elif depth == 'deep_if':
#             weights = [.5, .5]
#         elif depth == 'middle_if':
#             weights = [.5, .5]
#         elif depth == 'shallow_if':
#             weights = [.25, .75]
#         elif depth == 'mound':
#             weights = [.25, .75]
#         elif depth == 'catcher':
#             weights = [.1, .9]

#         # "catchable": {
#         #         "deep_of": [1, 0],
#         #         "middle_of": [1, 0],
#         #         "shallow_of": [1, 0],
#         #         "deep_if": [.5, .5],
#         #         "deep_if": [.5, .5],
#         #         "deep_if": [.25, .75],
#         #         "mound": [1, 0],
#         #         "catcher": [1, 0]
#         #     }

#         air_or_ground = random.choices(['airball', 'groundball'], weights, k=1)[0]

#         return (fieldingweights[contacttype], air_or_ground)

#     def ThrowDeterminer(self, direction, depth, batted_ball_outcome, air_or_ground, primarydefender):
#         needthrow, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, error_state = self.RunDeterminer(batted_ball_outcome, air_or_ground, primarydefender)
#         #self.gamestate.game.current_runners_home = alreadyhome
#         #print(f"Need? {needthrow} From Batter: {headingtofirst} From 1st: {headingtosecond} From 2nd: {headingtothird} From 3rd: {headingtohome} HOME: {alreadyhome}")
#         if (headingtofirst == None and headingtosecond == None and headingtothird == None and headingtohome == None) and needthrow == False:
#             self.gamestate.game.outcount+=1
#             return [headingtofirst, headingtosecond, headingtothird, alreadyhome], [error_state]
#         elif needthrow == True:
#             target = ''
#             if headingtohome == None:
#                 pass
#                 #print(f'{batted_ball_outcome} {direction}/{depth} {primarydefender[0]}: no one heading to home')
#             if headingtothird == None:
#                 pass 
#                 #print(f'{batted_ball_outcome} {direction}/{depth} {primarydefender[0]}: no one heading to third')
#             if headingtosecond == None:
#                 pass
#                 #print(f'{batted_ball_outcome} {direction}/{depth} {primarydefender[0]}: no one heading to second')
#             if headingtofirst == None:
#                 pass
#                 #print(f'{batted_ball_outcome} {direction}/{depth} {primarydefender[0]}: no one heading to first')

#             if (batted_ball_outcome== 'out'):
#                 if (self.gamestate.game.currentouts == self.gamestate.game.rules.outs-1):
#                     if primarydefender[0].lineup == 'firstbase':
#                         target = 'pitcher'
#                     else: 
#                         target = 'firstbase'
#                 elif (self.gamestate.game.currentouts == self.gamestate.game.rules.outs-2 and headingtosecond != None):                    
#                     if primarydefender[0].lineup == 'secondbase':
#                         target = 'shortstop'
#                     else:
#                         target = 'secondbase'
#                     #try for double play
#                 elif headingtohome != None:
#                     if primarydefender[0].lineup == 'catcher':
#                         target = 'pitcher'
#                     else:
#                         target = 'catcher'
#                 else:
#                     target = 'firstbase'
#             else:
#                 target = 'firstbase'
#             #print(target)
#             ballcatcher = [player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup==target]
#             if ballcatcher == []:
#                 ballcatcher = self.gamestate.game.pitchingteam.currentpitcher
#             else:
#                 ballcatcher = ballcatcher[0]
#             #print(f"Ball Catcher: {ballcatcher}")

#             #need to match target with the runner
#             if target == 'catcher':
#                 target_baserunner = headingtohome
#             elif target == 'pitcher':
#                 target_baserunner = headingtofirst
#             elif target == 'firstbase':
#                 target_baserunner = headingtofirst
#             elif target == 'secondbase':
#                 target_baserunner = headingtosecond
#             elif target == 'thirdbase':
#                 target_baserunner = headingtothird
#             elif target == 'shortstop':
#                 target_baserunner = headingtosecond

#             if (target == 'firstbase' and primarydefender[0].lineup == 'firstbase') or (target == 'secondbase' and primarydefender[0].lineup == 'secondbase') or (target == 'thirdbase' and primarydefender[0].lineup == 'thirdbase') or (target == 'catcher' and primarydefender[0].lineup == 'catcher'):
#                 if headingtohome != None:
#                     alreadyhome.append(headingtohome)
#                     headingtohome = None
#                 errors = []
#                 if error_state != None:
#                     errors.append(error_state)                
#                 return [headingtofirst, headingtosecond, headingtothird, alreadyhome], errors 

#             #print(f"DEFENSIVE PLAY: {primarydefender[0].lineup} {target} {ballcatcher.lineup}")
#             post_catch_error, errortype, error_text = self.Throw_V_Run(primarydefender[0], ballcatcher, target, target_baserunner)
            
#             if post_catch_error == False:
#                 target_baserunner = None
#                 self.gamestate.game.outcount+=1
                
#             if post_catch_error == True:
#                 if headingtofirst != None:
#                     stats.SetPitcherStatus(headingtofirst, self.gamestate.game.pitchingteam.currentpitcher, False)
#                 headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome = self.ErrorDeterminer(errortype, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, batted_ball_outcome)

#                 #print(f"NEXT LEVEL UP CHECK FOR ERROR: {batted_ball_outcome} {headingtofirst} {headingtosecond} {headingtothird} {headingtohome} {alreadyhome}")    
            
#             #makeshift third base handler
#             if headingtohome != None:
#                 alreadyhome.append(headingtohome)
#                 headingtohome = None
#             errors = []
#             if errortype != None:
#                 errors.append(error_text)
#             if error_state != None:
#                 errors.append(error_state)
#             return [headingtofirst, headingtosecond, headingtothird, alreadyhome], errors #errortype

#         else: 
#             #print("Is this it?")
#             post_catch_error, errortype, error_text = self.Throw_V_Run(None, primarydefender[0], None, None)
#             if post_catch_error == False:
#                 self.gamestate.game.outcount+=1
#             if post_catch_error == True:
#                 stats.SetPitcherStatus(headingtofirst, self.gamestate.game.pitchingteam.currentpitcher, False)
#                 headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome = self.ErrorDeterminer(errortype, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, batted_ball_outcome)
#                 #print(f"NEXT LEVEL UP CHECK FOR ERROR OUTS: {batted_ball_outcome} {headingtofirst} {headingtosecond} {headingtothird} {headingtohome} {alreadyhome}")    
            
#             #makeshift third base handler
#             if headingtohome != None:
#                 alreadyhome.append(headingtohome)
#                 headingtohome = None
#             errors = []                
#             if errortype != None:
#                 errors.append(error_text)
#             if error_state != None:
#                 errors.append(error_state)
#             return [headingtofirst, headingtosecond, headingtothird, alreadyhome], errors#[]errortype

#     def Throw_V_Run(self, primarydefender, ballcatcher, target, target_baserunner):
#         #print(f"DEFENSIVE PLAY: {primarydefender.lineup} {target} {ballcatcher.lineup}")
#         fieldingerror = False
#         throwingerror = False
        
#         throwingerror, fieldingerror = self.gamestate.game.baselines.Throw_Catch(primarydefender, ballcatcher)

#         if (fieldingerror == False and throwingerror == False):
#             is_error = False
#         if (fieldingerror == True or throwingerror == True):
#             is_error = True

#         if fieldingerror == True:
#             self.gamestate.game.error_count+=1
#         if throwingerror == True:
#             self.gamestate.game.error_count+=1
            
#         if (fieldingerror == False and throwingerror == False):
#             errortype = None
#             errortext = None
#         if (fieldingerror == True and throwingerror == False):
#             stats
#             errortype = f"fielding error"#" by {ballcatcher.lineup} {ballcatcher.name}"
#             errortext = f"fielding error by {ballcatcher.lineup} {ballcatcher.name}"
#             #can assign player specific error here as well if needed eventually.            
#         if (fieldingerror == False and throwingerror == True):
#             errortype = f"throwing error"#" by {primarydefender.lineup} {primarydefender.name}"
#             errortext = f"throwing error by {primarydefender.lineup} {primarydefender.name}"
#             #can assign player specific error here as well if needed eventually.
#         if (fieldingerror == True and throwingerror == True):
#             errortype = f"double error"#" by {primarydefender.lineup} {primarydefender.name} followed by a fielding error by {ballcatcher.lineup} {ballcatcher.name}"
#             errortext = f"throwing error by {primarydefender.lineup} {primarydefender.name} followed by a fielding error by {ballcatcher.lineup} {ballcatcher.name}"
#             #print(errortext)
#             #can assign player specific error here as well if needed eventually.

#         if (fieldingerror == False and throwingerror == False):
#             primarydefender.fieldingstats.Adder("assists", 1)
#             #primarydefender.fieldingstats.assists += 1
#             ballcatcher.fieldingstats.Adder("putouts", 1)
#             #ballcatcher.fieldingstats.putouts += 1
#             #print(f"THROWN OUT RUNNING TO BASES: {self.gamestate.id} {target_baserunner}")
#             self.gamestate.game.outcount += 1
#             target_baserunner = None
            


#         return is_error, errortype, errortext

#     def ErrorDeterminer(self, error_state, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, batted_ball_outcome):     
#         #print(f"PREPROCESS CHECK FOR ERROR: {batted_ball_outcome} {headingtofirst} {headingtosecond} {headingtothird} {headingtohome} {alreadyhome}")    
#         if error_state == 'fielding error':
#             if headingtohome != None:
#                 alreadyhome.append(headingtohome)
#                 headingtohome = None
#             if headingtothird != None:
#                 headingtohome = headingtothird
#                 headingtothird = None
#             if headingtosecond != None:
#                 headingtothird = headingtosecond                
#                 headingtosecond = None
#             if headingtofirst != None:
#                 headingtosecond = headingtofirst
#                 headingtofirst = None
#             #if batted_ball_outcome == 'out':
#             #    headingtofirst = self.gamestate.game.battingteam.currentbatter
#             #    self.gamestate.game.battingteam.currentbatter = None
            
#         if error_state == 'throwing error':
#             if headingtohome != None:
#                 alreadyhome.append(headingtohome)
#                 headingtohome = None
#             if headingtothird != None:
#                 headingtohome = headingtothird
#                 headingtothird = None
#             if headingtosecond != None:
#                 headingtothird = headingtosecond
#                 headingtosecond = None
#             if headingtofirst != None:
#                 headingtosecond = headingtofirst
#                 headingtofirst = None
#             #if batted_ball_outcome == 'out':
#             #    headingtofirst = self.gamestate.game.battingteam.currentbatter
#             #    self.gamestate.game.battingteam.currentbatter = None

#         if error_state == 'double error':
#             if headingtohome != None:
#                 alreadyhome.append(headingtohome)
#                 headingtohome = None
#             if headingtothird != None:
#                 alreadyhome.append(headingtothird)
#                 headingtothird = None
#             if headingtosecond != None:
#                 headingtohome = headingtosecond
#                 headingtosecond = None
#             if headingtofirst != None:
#                 headingtothird = headingtofirst
#                 headingtofirst = None
#             #if batted_ball_outcome == 'out':
#             #    headingtofirst = self.gamestate.game.battingteam.currentbatter
#             #   self.gamestate.game.battingteam.currentbatter = None

#         #print(f"POSTPROCESS CHECK FOR ERROR: {batted_ball_outcome} {headingtofirst} {headingtosecond} {headingtothird} {headingtohome} {alreadyhome}")    
#         return headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome

#     def RunDeterminer(self, batted_ball_outcome, air_or_ground, primarydefender):
#         strat = self.gamestate.game.battingteam.strategy
#         #print(f"HOME RUN CHECK: {batted_ball_outcome}")
#         self.gamestate.game.batted_ball = batted_ball_outcome
#         self.gamestate.game.air_or_ground = air_or_ground
#         self.gamestate.game.targeted_defender = primarydefender[0].lineup


#         headingtofirst = None
#         headingtosecond = None
#         headingtothird = None
#         headingtohome = None
#         alreadyhome = []
#         if batted_ball_outcome == 'single':
#             stats.SetPitcherStatus(self.gamestate.game.battingteam.currentbatter, self.gamestate.game.pitchingteam.currentpitcher, True)
#             self.gamestate.game.battingteam.currentbatter.battingstats.Adder("singles", 1)
#             self.gamestate.game.battingteam.currentbatter.battingstats.Adder("bases", 1)
#             self.gamestate.game.is_single = True
#             headingtofirst = self.gamestate.game.battingteam.currentbatter
#             if self.gamestate.game.on_firstbase != None:
#                 self.gamestate.game.on_firstbase.battingstats.Adder("bases", 1)
#                 headingtosecond = self.gamestate.game.on_firstbase
#             if self.gamestate.game.on_secondbase != None:
#                 self.gamestate.game.on_secondbase.battingstats.Adder("bases", 1)
#                 headingtothird = self.gamestate.game.on_secondbase
#             if self.gamestate.game.on_thirdbase != None:
#                 self.gamestate.game.on_thirdbase.battingstats.Adder("bases", 1)
#                 headingtohome = self.gamestate.game.on_thirdbase
#         elif batted_ball_outcome == 'double':
#             stats.SetPitcherStatus(self.gamestate.game.battingteam.currentbatter, self.gamestate.game.pitchingteam.currentpitcher, True)
#             self.gamestate.game.battingteam.currentbatter.battingstats.Adder("doubles", 1)
#             self.gamestate.game.battingteam.currentbatter.battingstats.Adder("bases", 2)
#             self.gamestate.game.is_double = True
#             headingtosecond = self.gamestate.game.battingteam.currentbatter
#             if self.gamestate.game.on_firstbase != None:
#                 self.gamestate.game.on_firstbase.battingstats.Adder("bases", 2)
#                 headingtothird = self.gamestate.game.on_firstbase
#             if self.gamestate.game.on_secondbase != None:            
#                 self.gamestate.game.on_secondbase.battingstats.Adder("bases", 2)
#                 headingtohome = self.gamestate.game.on_secondbase
#             if self.gamestate.game.on_thirdbase != None:            
#                 self.gamestate.game.on_thirdbase.battingstats.Adder("bases", 1)
#                 alreadyhome.append(self.gamestate.game.on_thirdbase)
#         elif batted_ball_outcome == 'triple':
#             stats.SetPitcherStatus(self.gamestate.game.battingteam.currentbatter, self.gamestate.game.pitchingteam.currentpitcher, True)
#             self.gamestate.game.battingteam.currentbatter.battingstats.Adder("triples", 1)
#             self.gamestate.game.battingteam.currentbatter.battingstats.Adder("bases", 3)
#             self.gamestate.game.is_triple = True
#             headingtothird = self.gamestate.game.battingteam.currentbatter
#             if self.gamestate.game.on_firstbase != None:            
#                 self.gamestate.game.on_firstbase.battingstats.Adder("bases", 3)
#                 headingtohome = self.gamestate.game.on_firstbase
#             if self.gamestate.game.on_secondbase != None:
#                 self.gamestate.game.on_secondbase.battingstats.Adder("bases", 3)
#                 alreadyhome.append(self.gamestate.game.on_secondbase)
#             if self.gamestate.game.on_thirdbase != None:
#                 self.gamestate.game.on_thirdbase.battingstats.Adder("bases", 3)
#                 alreadyhome.append(self.gamestate.game.on_thirdbase)
#         # elif batted_ball_outcome == 'homerun':
#              #print("Does this ever fire?")
#         #     input()
#         #     self.gamestate.game.is_homerun = True
#         #     alreadyhome.append(self.gamestate.game.battingteam.currentbatter)            
#         #     if self.gamestate.game.on_firstbase != None:
#         #         alreadyhome.append(self.gamestate.game.on_firstbase)            
#         #     if self.gamestate.game.on_secondbase != None:
#         #         alreadyhome.append(self.gamestate.game.on_secondbase)            
#         #     if self.gamestate.game.on_thirdbase != None:
#         #         alreadyhome.append(self.gamestate.game.on_thirdbase)  
#         #     return False, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, None

#         elif batted_ball_outcome == 'out':
#             #print(f"{primarydefender[0].name} {primarydefender[0].lineup}")
#             is_error = self.gamestate.game.baselines.CatchErrorEval(None, primarydefender[0])

#             if is_error == True:
#                 self.gamestate.game.error_count += 1
#                 stats.SetPitcherStatus(self.gamestate.game.battingteam.currentbatter, self.gamestate.game.pitchingteam.currentpitcher, False)
#                 headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome = self.ErrorDeterminer('fielding error', self.gamestate.game.battingteam.currentbatter, self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, [], batted_ball_outcome)
#                 return True, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, f"XX fielding error by {primarydefender[0].name}"

#             primarydefender[0].fieldingstats.Adder("putouts", 1)
#             #primarydefender[0].fieldingstats.putouts +=1
#             if air_or_ground == 'airball':
#                 #need to add getting current batter out 
#                 if (self.gamestate.game.currentouts + self.gamestate.game.outcount)-1 >= self.gamestate.game.rules.outs:
#                     return False, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, None
#                 if ([self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase]) == [None, None, None]:
#                     return False, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, None                
#                 if primarydefender[0].throwpower < 40:
#                     if self.gamestate.game.on_secondbase != None:
#                         headingtothird = self.gamestate.game.on_secondbase
#                     if self.gamestate.game.on_thirdbase != None:
#                         headingtohome = self.gamestate.game.on_thirdbase
#                     if primarydefender[0].throwpower <30:
#                         if self.gamestate.game.on_firstbase != None:
#                             headingtosecond = self.gamestate.game.on_firstbase
#                 else:
#                     return False, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, None

#             elif air_or_ground == 'groundball':
#                 if (self.gamestate.game.currentouts + self.gamestate.game.outcount) -1 >= self.gamestate.game.rules.outs:
#                     if self.gamestate.game.battingteam.currentbatter != None:
#                         stats.SetPitcherStatus(self.gamestate.game.battingteam.currentbatter, self.gamestate.game.pitchingteam.currentpitcher, True)
#                         headingtofirst = self.gamestate.game.battingteam.currentbatter
#                     if self.gamestate.game.on_firstbase != None:
#                         headingtosecond = self.gamestate.game.on_firstbase
#                     if self.gamestate.game.on_secondbase != None:
#                         headingtothird = self.gamestate.game.on_secondbase
#                     if self.gamestate.game.on_thirdbase != None:
#                         headingtohome = self.gamestate.game.on_thirdbase

#                 if self.gamestate.game.on_firstbase != None:
#                     headingtosecond = self.gamestate.game.on_firstbase 

#                 if self.gamestate.game.on_secondbase != None:
#                     if self.gamestate.game.on_firstbase != None:
#                         headingtothird = self.gamestate.game.on_secondbase
#                     else:
#                         pass
#                 if self.gamestate.game.on_thirdbase != None:
#                     if (self.gamestate.game.on_secondbase !=None and self.gamestate.game.on_firstbase !=None):
#                         headingtohome = self.gamestate.game.on_thirdbase
#                     else:                      
#                         pass

#         return True, headingtofirst, headingtosecond, headingtothird, headingtohome, alreadyhome, None