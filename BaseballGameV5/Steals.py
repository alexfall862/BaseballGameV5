import math
import random
from defense import fielding as f
from defense import BasePaths as b
from defense import Error_Throw_Catch
from defense import Error_Catch
from defense import Error_Throw
from defense import Throw_CatchDepth

class Steals():
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.firstbase = self.gamestate.game.on_firstbase
        self.secondbase = self.gamestate.game.on_secondbase 
        self.thirdbase = self.gamestate.game.on_thirdbase
        self.runnerstrategy =  self.gamestate.game.battingteam.strategy
        self.defensestrategy =  self.gamestate.game.pitchingteam.strategy
        self.defensiveactions = []
        self.defense = self.gamestate.game.pitchingteam
        self.errorlist = []
        self.basepaths = b(self, self.gamestate.game.battingteam.currentbatter, self.firstbase, self.secondbase, self.thirdbase, self.gamestate.game)
        self.skippitch = self.steal_eval(self.firstbase, self.secondbase, self.thirdbase)
                
    def pull_stealfreq(runner, stratlist):
        #print(f"Running Pull Steal Freq")
        freq = [player.stealfreq for player in stratlist if player.id == runner.id][0]
        return freq     
    
    def pull_pickofffreq(pitcher, stratlist):
        #print(f"Running Pull Pickoff Freq")
        freq = [player.pickofffreq for player in stratlist if player.id == pitcher.id][0]
        return freq     
    
    def steal_eval(self, firstbase, secondbase, thirdbase):
        #print(f"Running Steal Eval")
        if firstbase == None and secondbase == None and thirdbase == None:
            return False
        else:
            pickofffreqrating = Steals.pull_pickofffreq(self.gamestate.game.pitchingteam.currentpitcher, self.defensestrategy.playerstrategy)
            diceroll = random.random() * 100
            if pickofffreqrating > diceroll:
                if firstbase != None:
                    self.gamestate.game.is_pickoff = True
                    pickoff, baserunner, throwerror, catcherror = Steals.pickoff_math(self, self.gamestate.game.baselines.pickoff_success, firstbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.firstbase)
                    if pickoff == True:
                        if (throwerror == False and catcherror == False):
                            self.gamestate.defensiveoutcome = (None, None, None, "successful pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                            self.gamestate.game.on_firstbase = None
                            self.gamestate.game.outcount+=1
                            return True
                    elif pickoff == False:
                        if throwerror == True:
                            self.gamestate.defensiveoutcome = (None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                            self.gamestate.game.error_count+=1
                            if thirdbase != None:
                                self.gamestate.game.current_runners_home.append(thirdbase)
                                self.gamestate.game.on_thirdbase = None                                
                            if secondbase != None:
                                self.gamestate.game.on_thirdbase = self.gamestate.game.on_secondbase
                                self.gamestate.game.on_secondbase = None
                            if firstbase != None:
                                self.gamestate.game.on_secondbase = self.gamestate.game.on_firstbase
                                self.gamestate.game.on_firstbase = None      
                            return True
                        elif catcherror == True:
                            self.gamestate.defensiveoutcome = (None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                            self.gamestate.game.error_count+=1
                            #need to assign error eventually
                            return True
                        self.gamestate.defensiveoutcome = (None, None, None, "unsuccessful pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                        return True
            else:
                pass

            diceroll = random.random() * 100
            if pickofffreqrating > diceroll:
                if secondbase != None:
                    self.gamestate.game.is_pickoff = True
                    pickoff, baserunner, throwerror, catcherror = Steals.pickoff_math(self, self.gamestate.game.baselines.pickoff_success, secondbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.secondbase)
                    if pickoff == True:
                        if throwerror == False and catcherror == False:
                            self.gamestate.defensiveoutcome = (None, None, None, "successful pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                            self.gamestate.game.on_secondbase = None
                            self.gamestate.game.outcount+=1
                            return True
                    elif pickoff == False:
                        if throwerror == True:
                            self.gamestate.defensiveoutcome = (None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                            self.gamestate.game.error_count+=1
                            if thirdbase != None:
                                self.gamestate.game.current_runners_home.append(thirdbase)
                                self.gamestate.game.on_thirdbase = None                                
                            if secondbase != None:
                                self.gamestate.game.on_thirdbase = self.gamestate.game.on_secondbase
                                self.gamestate.game.on_secondbase = None
                            if firstbase != None:
                                self.gamestate.game.on_secondbase = self.gamestate.game.on_firstbase
                                self.gamestate.game.on_firstbase = None      
                            return True
                        elif catcherror == True:
                            self.gamestate.defensiveoutcome = (None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                            self.gamestate.game.error_count+=1
                            #need to assign error eventually
                            return True
                        self.gamestate.defensiveoutcome = (None, None, None, "unsuccessful pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                        return True
            else:
                pass

            diceroll = random.random() * 100
            if pickofffreqrating > diceroll:
                if thirdbase != None:
                    self.gamestate.game.is_pickoff = True
                    pickoff, baserunner, throwerror, catcherror = Steals.pickoff_math(self, self.gamestate.game.baselines.pickoff_success, thirdbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.thirdbase)
                    if pickoff == True:
                        if throwerror == False and catcherror == False:
                            self.gamestate.defensiveoutcome = (None, None, None, "successful pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                            self.gamestate.game.on_thirdbase = None
                            self.gamestate.game.outcount+=1
                            return True
                    elif pickoff == False:
                        if throwerror == True:
                            self.gamestate.defensiveoutcome = (None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                            self.gamestate.game.error_count+=1
                            if thirdbase != None:
                                self.gamestate.game.current_runners_home.append(thirdbase)
                                self.gamestate.game.on_thirdbase = None                                
                            if secondbase != None:
                                self.gamestate.game.on_thirdbase = self.gamestate.game.on_secondbase
                                self.gamestate.game.on_secondbase = None
                            if firstbase != None:
                                self.gamestate.game.on_secondbase = self.gamestate.game.on_firstbase
                                self.gamestate.game.on_firstbase = None      
                            return True
                        elif catcherror == True:
                            self.gamestate.defensiveoutcome = (None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                            self.gamestate.game.error_count+=1
                            return True
                        self.gamestate.defensiveoutcome = (None, None, None, "unsuccessful pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                        return True
            else:
                pass

            if self.gamestate.game.is_pickoff != True:
                if thirdbase != None:
                    stealfreqrating = Steals.pull_stealfreq(self.thirdbase, self.runnerstrategy.playerstrategy)
                    diceroll = random.random() * 100
                    if (stealfreqrating > diceroll):
                        self.gamestate.game.is_stealattempt = True
                        thirdbase.energy = max(0, thirdbase.energy - 0.5)
                        thirdbase.abilitymodifierscore = (math.sqrt(math.sqrt(thirdbase.energy)) / 3.16227766)
                        outcome, error_check = Steals.calc_baserunning_math(self, self.gamestate.game.baselines.steal_success, self.gamestate.game.baselines.stealawareness_max, thirdbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.catcher, self.gamestate.game.pitchingteam.thirdbase, stealfreqrating)

                        if (error_check[0] == True and error_check[1] == True) or error_check[0] == True:
                            self.gamestate.game.error_count+=1
                            self.gamestate.game.current_runners_home.append(thirdbase)
                            thirdbase.battingstats.Adder("stolen_bases", 1)
                            self.gamestate.game.on_thirdbase = None
                            if secondbase != None:
                                self.gamestate.game.on_thirdbase = self.gamestate.game.on_secondbase                                
                                self.gamestate.game.on_secondbase = None
                            if firstbase != None:
                                self.gamestate.game.on_secondbase = self.gamestate.game.on_firstbase
                                self.gamestate.game.on_firstbase = None
                            self.gamestate.defensiveoutcome = (None, None, None, "error on steal", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)                        
                        elif error_check[1] == True:
                            self.gamestate.game.error_count+=1
                            thirdbase.battingstats.Adder("stolen_bases", 1)
                            self.gamestate.game.current_runners_home.append(thirdbase)
                            self.gamestate.game.on_thirdbase = None
                            self.gamestate.defensiveoutcome = (None, None, None, "error on steal", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)                        
                        elif error_check[0] == False and error_check[1] == False:
                            if outcome == True:
                                self.gamestate.game.is_stealsuccess = True
                                self.gamestate.game.current_runners_home.append(thirdbase)
                                thirdbase.battingstats.Adder("stolen_bases", 1)
                                self.gamestate.game.on_thirdbase = None
                                self.gamestate.defensiveoutcome = (None, None, None, "stolen base", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                                return True
                            if outcome == False:
                                thirdbase.battingstats.Adder("caught_stealing", 1)
                                self.gamestate.game.on_thirdbase = None
                                self.gamestate.game.outcount += 1
                                self.gamestate.defensiveoutcome = (None, None, None, "caught stealing", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                                return True
                else:
                    pass
                        #return True

                if secondbase != None:
                    stealfreqrating = Steals.pull_stealfreq(self.secondbase, self.runnerstrategy.playerstrategy)
                    diceroll = random.random() * 100
                    if (stealfreqrating > diceroll):
                        self.gamestate.game.is_stealattempt = True
                        secondbase.energy = max(0, secondbase.energy - 0.5)
                        secondbase.abilitymodifierscore = (math.sqrt(math.sqrt(secondbase.energy)) / 3.16227766)
                        outcome, error_check = Steals.calc_baserunning_math(self, self.gamestate.game.baselines.steal_success, self.gamestate.game.baselines.stealawareness_max, secondbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.catcher, self.gamestate.game.pitchingteam.secondbase, stealfreqrating)

                        if (error_check[0] == True and error_check[1] == True) or error_check[0] == True:
                            self.gamestate.game.error_count+=1
                            if thirdbase != None:
                                self.gamestate.game.current_runners_home.append(thirdbase)
                                self.gamestate.game.on_thirdbase = None
                            secondbase.battingstats.Adder("stolen_bases", 1)
                            self.gamestate.game.on_thirdbase = self.gamestate.game.on_secondbase
                            self.gamestate.game.on_secondbase = None
                            if firstbase != None:
                                self.gamestate.game.on_secondbase = self.gamestate.game.on_firstbase
                                self.gamestate.game.on_firstbase = None
                            self.gamestate.defensiveoutcome = (None, None, None, "error on steal", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)                        
                        elif error_check[1] == True:
                            self.gamestate.game.error_count+=1
                            secondbase.battingstats.Adder("stolen_bases", 1)
                            self.gamestate.game.on_thirdbase = self.gamestate.game.on_secondbase
                            self.gamestate.game.on_secondbase = None
                            self.gamestate.defensiveoutcome = (None, None, None, "error on steal", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)                        
                        elif error_check[0] == False and error_check[1] == False:
                            if outcome == True:
                                self.gamestate.game.is_stealsuccess = True
                                secondbase.battingstats.Adder("stolen_bases", 1)
                                self.gamestate.game.on_thirdbase = secondbase
                                self.gamestate.game.on_secondbase = None
                                self.gamestate.defensiveoutcome = (None, None, None, "stolen base", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)                        
                                return True           
                            if outcome == False:
                                self.gamestate.game.on_secondbase = None
                                secondbase.battingstats.Adder("caught_stealing", 1)
                                self.gamestate.game.outcount += 1
                                self.gamestate.defensiveoutcome = (None, None, None, "caught stealing", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                                return True
                else:
                    pass

                if firstbase != None:
                    stealfreqrating = Steals.pull_stealfreq(self.firstbase, self.runnerstrategy.playerstrategy)
                    diceroll = random.random() * 100
                    if (stealfreqrating > diceroll):
                        self.gamestate.game.is_stealattempt = True
                        firstbase.energy = max(0, firstbase.energy - 0.5)
                        firstbase.abilitymodifierscore = (math.sqrt(math.sqrt(firstbase.energy)) / 3.16227766)
                        outcome, error_check = Steals.calc_baserunning_math(self, self.gamestate.game.baselines.steal_success, self.gamestate.game.baselines.stealawareness_max, firstbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.catcher, self.gamestate.game.pitchingteam.firstbase, stealfreqrating)

                        if (error_check[0] == True and error_check[1] == True) or error_check[0] == True:
                            self.gamestate.game.error_count+=1
                            if thirdbase != None:
                                self.gamestate.game.current_runners_home.append(thirdbase)
                                self.gamestate.game.on_thirdbase = None
                            if secondbase != None:
                                self.gamestate.game.on_thirdbase = secondbase
                                self.gamestate.game.on_secondbase = None
                            firstbase.battingstats.Adder("stolen_bases", 1)
                            self.gamestate.game.on_secondbase = self.gamestate.game.on_firstbase
                            self.gamestate.game.on_firstbase = None
                            self.gamestate.defensiveoutcome = (None, None, None, "error on steal", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)                        
                        elif error_check[1] == True:
                            self.gamestate.game.error_count+=1
                            firstbase.battingstats.Adder("stolen_bases", 1)
                            self.gamestate.game.on_secondbase = self.gamestate.game.on_firstbase
                            self.gamestate.game.on_firstbase = None
                            self.gamestate.defensiveoutcome = (None, None, None, "error on steal", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)                        
                        elif error_check[0] == False and error_check[1] == False:
                            if outcome == True:
                                self.gamestate.game.is_stealsuccess = True
                                self.gamestate.game.on_secondbase = firstbase
                                firstbase.battingstats.Adder("stolen_bases", 1)
                                self.gamestate.game.on_firstbase = None
                                self.gamestate.defensiveoutcome = (None, None, None, "stolen base", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)                        
                                return True           
                            if outcome == False:
                                self.gamestate.game.on_firstbase = None
                                firstbase.battingstats.Adder("caught_stealing", 1)
                                self.gamestate.game.outcount += 1
                                self.gamestate.defensiveoutcome = (None, None, None, "caught stealing", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
                                return True
                else:
                    pass
        return False
            
    def pickoff_math(self, pickoffsuccess, baserunner, pitcher, baseman):
        diceroll = random.random() * 100

        pickoffmod = (pitcher.pickoff - 50)/50
        pickoffchances = (1+pickoffmod)*50

        bsp = (baserunner.speed - 50)/50
        bbr = (baserunner.baserunning - 50)/50
        brr = (baserunner.basereaction - 50)/50
        baserunner  = ((1 + (brr*4 + bbr*2 + bsp*4) / 10) * 50)

        error_check_t, error_check_c, d_action = Error_Throw_Catch(self, pitcher, baseman)     #self.gamestate.game.baselines.Throw_Catch(pitcher, baseman)
        error_check = [error_check_t, error_check_c]
        self.defensiveactions.append(d_action)


        if error_check[0] or error_check[1] == True:
            self.gamestate.defensiveoutcome = (None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
            return False, baserunner, error_check[0], error_check[1]

        pickoffscore = (pickoffchances / baserunner) * pickoffsuccess if baserunner > 0 else 1.0
        diceroll = random.random()
        if pickoffscore > diceroll:
            self.gamestate.defensiveoutcome = (None, None, None, "pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
            return True, None, error_check[0], error_check[1]
        else:
            self.gamestate.defensiveoutcome = (None, None, None, "failed pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
            return False, baserunner, error_check[0], error_check[1]
        
    def calc_baserunning_math(self, stealsuccess, stealawareness_max, baserunner, pitcher, catcher, baseman, stealfreq):
        bsp = (baserunner.speed - 50)/50
        bbr = (baserunner.baserunning - 50)/50
        brr = (baserunner.basereaction - 50)/50
        baserunner  = ((1 + (brr*3 + bbr*2 + bsp*5) / 10) * 50)

        ctp = (catcher.throwpower - 50)/50
        cta = (catcher.throwacc - 50)/50
        ccs = (catcher.catchsequence - 50)/50
        pps = (pitcher.psequencing - 50)/50
        cfr = (catcher.fieldreact - 50)/5
        battery = ((1 + (ctp*15 + cta*3 + ccs*1 + pps*1) / 20) * 50) + cfr
        comp_score = baserunner / battery if battery > 0 else 1.0

        SOFT_THRESHOLD = 2.0
        HARD_THRESHOLD = 5.0
        STEEP_THRESHOLD = 10.0
        awareness_exponent = self.gamestate.game.baselines.steal_awareness_exponent
        if stealfreq <= SOFT_THRESHOLD:
            awareness_penalty = 0.0
        elif stealfreq <= HARD_THRESHOLD:
            awareness_penalty = 0.03 * (stealfreq - SOFT_THRESHOLD) / (HARD_THRESHOLD - SOFT_THRESHOLD)
        elif stealfreq <= STEEP_THRESHOLD:
            # Steep initial ramp: 3% → 20% over just 5 frequency units
            t = (stealfreq - HARD_THRESHOLD) / (STEEP_THRESHOLD - HARD_THRESHOLD)
            awareness_penalty = 0.03 + 0.17 * t
        else:
            # Slightly convex ramp from 20% to ceiling across remaining range
            t = (stealfreq - STEEP_THRESHOLD) / (100.0 - STEEP_THRESHOLD)
            awareness_penalty = 0.20 + (stealawareness_max - 0.20) * (t ** awareness_exponent)

        steal_outcome_odds = comp_score * stealsuccess * (1 - awareness_penalty)

        diceroll = random.random()
        
        
        error_check_t, error_check_c,  d_action = Error_Throw_Catch(self, catcher, baseman) #self.gamestate.game.baselines.Throw_Catch(pitcher, baseman) 
        error_check = [error_check_t, error_check_c]
        self.defensiveactions.append(d_action)
        

        if (steal_outcome_odds > diceroll):
            self.gamestate.defensiveoutcome = (None, None, None, "stolen base", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
            return True, error_check
        else:
            self.gamestate.defensiveoutcome = (None, None, None, "caught stealing", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
            return False, error_check