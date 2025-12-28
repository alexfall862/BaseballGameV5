import math
import numpy as np
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
            diceroll = np.random.rand() * 100
            if pickofffreqrating > diceroll:
                self.gamestate.game.is_pickoff = True
                if firstbase != None:
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

            diceroll = np.random.rand() * 100
            if pickofffreqrating > diceroll:
                self.gamestate.game.is_pickoff = True
                if secondbase != None:
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

            diceroll = np.random.rand() * 100
            if pickofffreqrating > diceroll:
                self.gamestate.game.is_pickoff = True
                if thirdbase != None:
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
                    diceroll = np.random.rand() * 100
                    if (stealfreqrating > diceroll):
                        self.gamestate.game.is_stealattempt = True
                        outcome, error_check = Steals.calc_baserunning_math(self, self.gamestate.game.baselines.steal_success, thirdbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.catcher, self.gamestate.game.pitchingteam.thirdbase)

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
                        elif error_check[0] and error_check[1] == False:
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
                    diceroll = np.random.rand() * 100
                    if (stealfreqrating > diceroll):
                        self.gamestate.game.is_stealattempt = True
                        outcome, error_check = Steals.calc_baserunning_math(self, self.gamestate.game.baselines.steal_success, secondbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.catcher, self.gamestate.game.pitchingteam.secondbase)

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
                        elif error_check[0] and error_check[1] == False:
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
                    diceroll = np.random.rand() * 100
                    if (stealfreqrating > diceroll):
                        self.gamestate.game.is_stealattempt = True
                        outcome, error_check = Steals.calc_baserunning_math(self, self.gamestate.game.baselines.steal_success, firstbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.catcher, self.gamestate.game.pitchingteam.firstbase)

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
                        elif error_check[0] and error_check[1] == False:
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
        diceroll = np.random.rand() * 100
        
        pickoffmod = (pitcher.pickoff - 50)/50
        pickoffchances = (1+pickoffmod)*50
        
        bsp = (baserunner.speed - 50)/50
        bbr = (baserunner.baserunning - 50)/50
        brr = (baserunner.baserunning - 50)/5
        baserunner_scores = [bsp, bbr]
        baserunner_weights = [3, 6]
        baserunner  = ((1+np.average(baserunner_scores, weights=baserunner_weights))*50)+brr
        
        error_check_t, error_check_c, d_action = Error_Throw_Catch(self, pitcher, baseman)     #self.gamestate.game.baselines.Throw_Catch(pitcher, baseman)
        error_check = [error_check_t, error_check_c]
        self.defensiveactions.append(d_action)


        if error_check[0] or error_check[1] == True:
            self.gamestate.defensiveoutcome = (None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
            return False, baserunner, error_check[0], error_check[1]

        pickoffscore = (pickoffchances / baserunner) * pickoffsuccess
        diceroll = np.random.rand()
        if pickoffscore > diceroll:
            self.gamestate.defensiveoutcome = (None, None, None, "pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
            return True, None, error_check[0], error_check[1]
        else:
            self.gamestate.defensiveoutcome = (None, None, None, "failed pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
            return False, baserunner, error_check[0], error_check[1]
        
    def calc_baserunning_math(self, stealsuccess, baserunner, pitcher, catcher, baseman):
        bsp = (baserunner.speed - 50)/50
        bbr = (baserunner.baserunning - 50)/50
        brr = (baserunner.baserunning - 50)/5
        baserunner_scores = [bsp, bbr]
        baserunner_weights = [6, 3]
        baserunner  = ((1+np.average(baserunner_scores, weights=baserunner_weights))*50)+brr

        ctp = (catcher.throwpower - 50)/50
        cta = (catcher.throwacc - 50)/50
        ccs = (catcher.catchsequence - 50)/50
        pps = (pitcher.psequencing - 50)/50
        cfr = (catcher.fieldreact - 50)/5
        battery_scores = [ctp, cta, ccs, pps]
        battery_weights = [15, 3, 1, 1]
        battery = ((1+np.average(battery_scores, weights=battery_weights))*50)+cfr
        comp_score = baserunner/battery
        steal_outcome_odds = comp_score*stealsuccess

        diceroll = np.random.rand()
        
        
        error_check_t, error_check_c,  d_action = Error_Throw_Catch(self, catcher, baseman) #self.gamestate.game.baselines.Throw_Catch(pitcher, baseman) 
        error_check = [error_check_t, error_check_c]
        self.defensiveactions.append(d_action)
        

        if (steal_outcome_odds > diceroll):
            self.gamestate.defensiveoutcome = (None, None, None, "stolen base", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
            return True, error_check
        else:
            self.gamestate.defensiveoutcome = (None, None, None, "caught stealing", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home], self.errorlist, self.defensiveactions)
            return False, error_check