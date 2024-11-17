import math
import numpy as np

class Steals():
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.firstbase = self.gamestate.game.on_firstbase
        self.secondbase = self.gamestate.game.on_secondbase 
        self.thirdbase = self.gamestate.game.on_thirdbase
        self.strategy =  self.gamestate.game.battingteam.strategy
        self.defense = self.gamestate.game.pitchingteam
        attemptoutcome = self.steal_eval(self.firstbase, self.secondbase, self.thirdbase)
                
    def pull_stealfreq(runner, stratlist):
        freq = [player.stealfreq for player in stratlist if player.id == runner.id][0]
        return freq     
    
    def pull_pickofffreq(pitcher, stratlist):
        freq = [player.pickofffreq for player in stratlist if player.id == pitcher.id][0]
        return freq     
    
    def steal_eval(self, firstbase, secondbase, thirdbase):
        if firstbase == None and secondbase == None and thirdbase == None:
            pass
        
        else:
            diceroll = np.random.rand()
            pickofffreqrating = Steals.pull_pickofffreq(self.gamestate.game.pitchingteam.currentpitcher, self.strategy.playerstrategy)
            if pickofffreqrating > diceroll:
                if firstbase != None:
                    outcome = Steals.pickoff_math(self.gamestate.game.baselines.pickoff_success, firstbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.firstbase)
                elif secondbase != None:
                    #attempt pickoff
                    pass
                elif thirdbase != None:
                    pass
                    #attempt pickoff
            else:
                if thirdbase != None:
                    #get steal frequency setting from player
                    stealfreqrating = Steals.pull_stealfreq(self.thirdbase, self.strategy.playerstrategy)
                    #roll to see likelihood of attempt
                    diceroll = np.random.rand()
                    if (stealfreqrating > diceroll):
                        #This should be edited because it's basically a player trying to steal against the catcher throwing it to himself. Might need new formula for just home base evals
                        output = Steals.calc_baserunning_math(self.gamestate.game.baselines.steal_success, self.gamestate.game.baselines.error_rate, self.gamestate.game.baselines.pickoff_success, thirdbase, self.gamestate.game.pitchingteam.currentpitcher, self.gamestate.game.pitchingteam.catcher, self.gamestate.game.pitchingteam.thirdbase)
                    else:
                        pass
                    #return something

                if secondbase != None and thirdbase == None:
                    stealfreqrating = Steals.pull_stealfreq(self.secondbase, self.strategy.playerstrategy)
                    print(f"{stealfreqrating}")
                if firstbase != None and secondbase == None:
                    stealfreqrating = Steals.pull_stealfreq(self.firstbase, self.strategy.playerstrategy)
                    print(f"{stealfreqrating}")
            
    def pickoff_math(pickoffsuccess, errorrate, baserunner, pitcher, baseman):
        bmr = (baseman.fieldreact - 50)/50
        bmc = (baseman.fieldcatch - 50)/50        
        fieldingmod = ((bmr+bmc)/2)
        errorodds = (fieldingmod * errorrate)        
        diceroll = np.random.rand()
        
        
        
        
        
        pickoffmod = (pitcher.pickoff - 50)/50
        pickoffchances = (1+pickoffmod)*50
        
        
        

        bsp = (baserunner.speed - 50)/50
        bbr = (baserunner.baserunning - 50)/50
        brr = (baserunner.baserunning - 50)/5
        baserunner_scores = [bsp, bbr]
        baserunner_weights = [3, 6]
        baserunner  = ((1+np.average(baserunner_scores, weights=baserunner_weights))*50)+brr
        
        pickoffscore = (pickoffchances / baserunner) * pickoffsuccess
        diceroll = np.random.rand()
        if pickoffscore > diceroll:
            return True
        else: 
            return False
        

    def calc_baserunning_math(stealsuccess, errorrate, pickoffsuccess, baserunner, pitcher, catcher, baseman):
        bsp = (baserunner.speed - 50)/50
        bbr = (baserunner.baserunning - 50)/50
        brr = (baserunner.baserunning - 50)/5
        baserunner_scores = [bsp, bbr]
        baserunner_weights = [6, 3]
        baserunner  = ((1+np.average(baserunner_scores, weights=baserunner_weights))*50)+brr

        ctp = (catcher.throwpower - 50)/50
        cta = (catcher.throwacc - 50)/50
        ccs = (catcher.catchsequence - 50)/50
        pps = (pitcher.sequence - 50)/50
        cfr = (catcher.fieldreact - 50)/5
        battery_scores = [ctp, cta, ccs, pps]
        battery_weights = [15, 3, 1, 1]
        battery = ((1+np.average(battery_scores, weights=battery_weights))*50)+cfr



        comp_score = baserunner/battery
        steal_outcome_odds = comp_score*stealsuccess

        diceroll = np.random.rand()
        
        if (steal_outcome_odds > diceroll):
            print(f"STEAL SUCCESS: {round(steal_outcome_odds, 2)} {round( diceroll, 2)}")
            return True
        else:
            print(f"STEAL FAILURE: {round(steal_outcome_odds, 2)} {round( diceroll, 2)}")
            return False
        
        bmr = (baseman.fieldreact - 50)/50
        bmc = (baseman.fieldcatch - 50)/50
        
        #NOT FINISHED, NEED TO FIND WAY TO HANDLE ERRORS AND FIGURE OUT WHAT THE OUTPUT NEEDS TO BE (PROBABLY INCLUDE OUTS OR SOMETHING AS WELL AS BASERUNNER SITUATION)

        cta = cta
        
        
