import math
import numpy as np

class Steals():
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.firstbase = self.gamestate.game.on_firstbase
        self.secondbase = self.gamestate.game.on_secondbase 
        self.thirdbase = self.gamestate.game.on_thirdbase
        self.runnerstrategy =  self.gamestate.game.battingteam.strategy
        self.defensestrategy =  self.gamestate.game.pitchingteam.strategy
        self.defense = self.gamestate.game.pitchingteam
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
                #print(f"PICKOFF STATE: {pickofffreqrating}>{diceroll} {self.gamestate.counter} {self.gamestate.game.is_pickoff}")
                if firstbase != None:
                    pickoff, baserunner, throwerror, catcherror = Steals.pickoff_math(self, self.gamestate.game.baselines.pickoff_success, firstbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.firstbase)
                    print(f"PICKOFF TEST: {pickoff}+{throwerror}+{catcherror}")
                    if pickoff == True:
                        if (throwerror == False and catcherror == False):
                            self.gamestate.defensiveoutcome = [None, None, None, "successful pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
                            self.gamestate.game.on_firstbase = None
                            self.gamestate.game.outcount+=1
                            return True
                    elif pickoff == False:
                        if throwerror == True:
                            self.gamestate.defensiveoutcome = [None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
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
                            self.gamestate.defensiveoutcome = [None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
                            self.gamestate.game.error_count+=1
                            #need to assign error eventually
                            return True
                        self.gamestate.defensiveoutcome = [None, None, None, "unsuccessful pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
                        return True
            else:
                pass
                #print(f"{self.gamestate.counter} Skipped First Base Eval")

            diceroll = np.random.rand() * 100
            if pickofffreqrating > diceroll:
                self.gamestate.game.is_pickoff = True
                #print(f"PICKOFF STATE: {pickofffreqrating}>{diceroll} {self.gamestate.counter} {self.gamestate.game.is_pickoff}")
                if secondbase != None:
                    pickoff, baserunner, throwerror, catcherror = Steals.pickoff_math(self, self.gamestate.game.baselines.pickoff_success, secondbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.secondbase)
                    print(f"PICKOFF TEST: {throwerror}+{catcherror}")
                    if pickoff == True:
                        if throwerror == False and catcherror == False:
                            self.gamestate.defensiveoutcome = [None, None, None, "successful pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
                            self.gamestate.game.on_secondbase = None
                            self.gamestate.game.outcount+=1
                            return True
                    elif pickoff == False:
                        if throwerror == True:
                            self.gamestate.defensiveoutcome = [None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
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
                            self.gamestate.defensiveoutcome = [None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
                            self.gamestate.game.error_count+=1
                            #need to assign error eventually
                            return True
                        self.gamestate.defensiveoutcome = [None, None, None, "unsuccessful pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
                        return True
            else:
                pass
                #print(f"{self.gamestate.counter} Skipped Second Base Eval")

            diceroll = np.random.rand() * 100
            if pickofffreqrating > diceroll:
                self.gamestate.game.is_pickoff = True
                #print(f"PICKOFF STATE: {pickofffreqrating}>{diceroll} {self.gamestate.counter} {self.gamestate.game.is_pickoff}")
                if thirdbase != None:
                    pickoff, baserunner, throwerror, catcherror = Steals.pickoff_math(self, self.gamestate.game.baselines.pickoff_success, thirdbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.thirdbase)
                    print(f"PICKOFF TEST: {throwerror}+{catcherror}")
                    if pickoff == True:
                        if throwerror == False and catcherror == False:
                            self.gamestate.defensiveoutcome = [None, None, None, "successful pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
                            self.gamestate.game.on_thirdbase = None
                            self.gamestate.game.outcount+=1
                            return True
                    elif pickoff == False:
                        if throwerror == True:
                            self.gamestate.defensiveoutcome = [None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
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
                            self.gamestate.defensiveoutcome = [None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
                            self.gamestate.game.error_count+=1
                            #need to assign error eventually
                            return True
                        self.gamestate.defensiveoutcome = [None, None, None, "unsuccessful pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
                        return True
            else:
                pass
                #print(f"{self.gamestate.counter} Skipped Third Base Eval")

            if self.gamestate.game.is_pickoff != True:
                if thirdbase != None:
                    #get steal frequency setting from player
                    stealfreqrating = Steals.pull_stealfreq(self.thirdbase, self.runnerstrategy.playerstrategy)
                    #roll to see likelihood of attempt
                    diceroll = np.random.rand() * 100
                    if (stealfreqrating > diceroll):
                        self.gamestate.game.is_stealattempt = True
                        #This should be edited because it's basically a player trying to steal against the catcher throwing it to himself. Might need new formula for just home base evals
                        outcome, error_check = Steals.calc_baserunning_math(self, self.gamestate.game.baselines.steal_success, thirdbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.catcher, self.gamestate.game.pitchingteam.thirdbase)
                        if outcome == True:
                            self.gamestate.defensiveoutcome = [None, None, None, "stolen base", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]                        
                            self.gamestate.game.is_stealsuccess = True
                            self.gamestate.game.current_runners_home.append(thirdbase)
                            self.gamestate.game.on_thirdbase = None
                            if (error_check[0] == True and error_check[1] == True) or error_check[0] == True:
                                self.gamestate.defensiveoutcome = [None, None, None, "error on steal", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]                        
                                self.gamestate.game.error_count+=1
                                if secondbase != None:
                                    self.gamestate.game.on_thirdbase = secondbase
                                    self.gamestate.game.on_secondbase = None
                                if firstbase != None:
                                    self.gamestate.game.on_secondbase = firstbase
                                    self.gamestate.game.on_firstbase = None
                            elif error_check[1] == True:
                                self.gamestate.defensiveoutcome = [None, None, None, "error on steal", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]                        
                                self.gamestate.game.error_count+=1
                                pass
                            return True
                        elif outcome == False:
                            return True
                else:
                    pass
                        #return True

                if secondbase != None:
                    #get steal frequency setting from player
                    stealfreqrating = Steals.pull_stealfreq(self.secondbase, self.runnerstrategy.playerstrategy)
                    #roll to see likelihood of attempt
                    diceroll = np.random.rand() * 100
                    if (stealfreqrating > diceroll):
                        self.gamestate.game.is_stealattempt = True
                        #This should be edited because it's basically a player trying to steal against the catcher throwing it to himself. Might need new formula for just home base evals
                        outcome, error_check = Steals.calc_baserunning_math(self, self.gamestate.game.baselines.steal_success, secondbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.catcher, self.gamestate.game.pitchingteam.secondbase)
                        if outcome == True:
                            self.gamestate.defensiveoutcome = [None, None, None, "stolen base", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]                        
                            self.gamestate.game.is_stealsuccess = True
                            self.gamestate.game.on_thirdbase = secondbase
                            self.gamestate.game.on_secondbase = None
                            if (error_check[0] == True and error_check[1] == True) or error_check[0] == True:
                                self.gamestate.defensiveoutcome = [None, None, None, "error on steal", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]                        
                                self.gamestate.game.error_count+=1
                                if thirdbase != None:
                                    self.gamestate.game.current_runners_home.append(thirdbase)
                                    self.gamestate.game.on_thirdbase = None
                                if firstbase != None:
                                    self.gamestate.game.on_secondbase = firstbase
                                    self.gamestate.game.on_firstbase = None
                            elif error_check[1] == True:
                                self.gamestate.defensiveoutcome = [None, None, None, "error on steal", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]                        
                                self.gamestate.game.error_count+=1
                                pass
                            return True               
                        elif outcome == False:
                            return True                    
                else:
                    pass
                    
                if firstbase != None:
                    #get steal frequency setting from player
                    stealfreqrating = Steals.pull_stealfreq(self.firstbase, self.runnerstrategy.playerstrategy)
                    #roll to see likelihood of attempt
                    diceroll = np.random.rand() * 100
                    if (stealfreqrating > diceroll):
                        self.gamestate.game.is_stealattempt = True
                        #This should be edited because it's basically a player trying to steal against the catcher throwing it to himself. Might need new formula for just home base evals
                        outcome, error_check = Steals.calc_baserunning_math(self, self.gamestate.game.baselines.steal_success, firstbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.catcher, self.gamestate.game.pitchingteam.firstbase)
                        if outcome == True:
                            self.gamestate.defensiveoutcome = [None, None, None, "stolen base", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]                        
                            self.gamestate.game.is_stealsuccess = True
                            self.gamestate.game.on_secondbase = firstbase
                            self.gamestate.game.on_firstbase = None
                            if (error_check[0] == True and error_check[1] == True) or error_check[0] == True:
                                self.gamestate.defensiveoutcome = [None, None, None, "error on steal", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]                        
                                self.gamestate.game.error_count+=1
                                if thirdbase != None:
                                    self.gamestate.game.current_runners_home.append(thirdbase)
                                    self.gamestate.game.on_thirdbase = None
                                if secondbase != None:
                                    self.gamestate.game.on_thirdbase = secondbase
                                    self.gamestate.game.on_secondbase = None
                            elif error_check[1] == True:
                                self.gamestate.defensiveoutcome = [None, None, None, "error on steal", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]                        
                                self.gamestate.game.error_count+=1
                                pass
                            return True           
                        elif outcome == False:
                            return True                    
                else:
                    pass
        return False
            
    def pickoff_math(self, pickoffsuccess, baserunner, pitcher, baseman):
        #print(f"Running Pickoff Math")
        diceroll = np.random.rand() * 100
        
        pickoffmod = (pitcher.pickoff - 50)/50
        pickoffchances = (1+pickoffmod)*50
        
        bsp = (baserunner.speed - 50)/50
        bbr = (baserunner.baserunning - 50)/50
        brr = (baserunner.baserunning - 50)/5
        baserunner_scores = [bsp, bbr]
        baserunner_weights = [3, 6]
        baserunner  = ((1+np.average(baserunner_scores, weights=baserunner_weights))*50)+brr
        
        error_check = self.gamestate.game.baselines.Throw_Catch(pitcher, baseman)
        print(f"PICKOFF ERROR_CHECK: {error_check}")

        if error_check[0] or error_check[1] == True:
            self.gamestate.defensiveoutcome = [None, None, None, "error on pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
            return False, baserunner, error_check[0], error_check[1]

        pickoffscore = (pickoffchances / baserunner) * pickoffsuccess
        diceroll = np.random.rand()
        #print(f"TEST OF PICKOFF SCORE: {pickoffscore}/{diceroll}")
        if pickoffscore > diceroll:
            self.gamestate.defensiveoutcome = [None, None, None, "pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
            return True, None, error_check[0], error_check[1]
        else: 
            self.gamestate.defensiveoutcome = [None, None, None, "failed pickoff", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
            return False, baserunner, error_check[0], error_check[1]
        

    def calc_baserunning_math(self, stealsuccess, baserunner, pitcher, catcher, baseman):
        #print(f"Running Calc Baserunning Math")
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
        #print(f"{stealsuccess}")
        #print(f"{baserunner}")
        #print(f"{battery}")
        comp_score = baserunner/battery
        #print(f"{comp_score}")        
        steal_outcome_odds = comp_score*stealsuccess

        diceroll = np.random.rand()
        
        print(f"STEAL MAFFS: {diceroll}/{steal_outcome_odds}")
        
        error_check = self.gamestate.game.baselines.Throw_Catch(pitcher, baseman) 
        
        print(f"STEAL ERROR CHECK {error_check}")

        if (steal_outcome_odds > diceroll):
            #print(f"STEAL SUCCESS: {round(steal_outcome_odds, 2)} {round( diceroll, 2)}")
            self.gamestate.defensiveoutcome = [None, None, None, "stolen base", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
            return True, error_check
        else:
            #print(f"STEAL FAILURE: {round(steal_outcome_odds, 2)} {round( diceroll, 2)}")
            self.gamestate.defensiveoutcome = [None, None, None, "caught stealing", [self.gamestate.game.on_firstbase, self.gamestate.game.on_secondbase, self.gamestate.game.on_thirdbase, self.gamestate.game.current_runners_home]]
            return False, error_check
        
        #NOT FINISHED, NEED TO FIND WAY TO HANDLE ERRORS AND FIGURE OUT WHAT THE OUTPUT NEEDS TO BE (PROBABLY INCLUDE OUTS OR SOMETHING AS WELL AS BASERUNNER SITUATION)

       
        
