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
    
    def steal_eval(self, firstbase, secondbase, thirdbase):
        if firstbase == None and secondbase == None and thirdbase == None:
            pass
        else:
            if thirdbase != None:
                stealrating = Steals.pull_stealfreq(self.thirdbase, self.strategy.playerstrategy)
                print(f"{stealrating}")
            if secondbase != None and thirdbase == None:
                stealrating = Steals.pull_stealfreq(self.secondbase, self.strategy.playerstrategy)
                print(f"{stealrating}")
            if firstbase != None and secondbase == None:
                stealrating = Steals.pull_stealfreq(self.firstbase, self.strategy.playerstrategy)
                print(f"{stealrating}")
                                    
    def calc_baserunning_math(stealsuccess, pickoffsuccess, baserunner_speed, baserunner_baserunning, baserunner_reaction, catcher_throwpower, catcher_throwacc, catcher_fieldreact, catcher_catch_sequence, pitcher_sequence, pitcher_pickoff, baseman_react, baseman_catch):
        bsp = (baserunner_speed - 50)/50
        bbr = (baserunner_baserunning - 50)/50
        brr = (baserunner_baserunning - 50)/5
        baserunner_scores = [bsp, bbr]
        baserunner_weights = [6, 3]
        baserunner  = ((1+np.average(baserunner_scores, weights=baserunner_weights))*50)+brr

        ctp = (catcher_throwpower - 50)/50
        cta = (catcher_throwacc - 50)/50
        ccs = (catcher_catch_sequence - 50)/50
        pps = (pitcher_sequence - 50)/50
        cfr = (catcher_fieldreact - 50)/5
        battery_scores = [ctp, cta, ccs, pps]
        battery_weights = [15, 3, 1, 1]
        battery = ((1+np.average(battery_scores, weights=battery_weights))*50)+cfr

        pickoffmod = (pitcher_pickoff - 50)/50
        pickoffchances = (1+pickoffmod)*pickoffsuccess

        comp_score = baserunner/battery
        steal_outcome_odds = comp_score*stealsuccess

        diceroll = np.random.rand()
        
        if (steal_outcome_odds > diceroll):
            print(f"STEAL SUCCESS: {round(steal_outcome_odds, 2)} {round( diceroll, 2)}")
        else:
            print(f"STEAL FAILURE: {round(steal_outcome_odds, 2)} {round( diceroll, 2)}")
        
        bmr = (baseman_react - 50)/50
        bmc = (baseman_catch - 50)/50
        
        cta = cta
        
