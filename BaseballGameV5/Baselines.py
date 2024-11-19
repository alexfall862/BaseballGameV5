import csv 
import os 
import numpy as np

class Baselines():
    def __init__(self, leaguetype):
        self.leaguetype = leaguetype
        ltypeload = Baselines.LoadLeagueType(self.leaguetype)
        self.outsideswing = float(ltypeload.get("OutsideSwing"))
        self.outsidelook = float(1 - self.outsideswing)
        self.outsidecontact = float(ltypeload.get("OutsideContact"))
        self.insideswing = float(ltypeload.get("InsideSwing"))
        self.insidelook = float(1 - self.insideswing)
        self.insidecontact = float(ltypeload.get("InsideContact"))
        self.barrelodds = float(ltypeload.get("c_barrelodds"))
        self.solidodds = float(ltypeload.get("c_solidodds"))
        self.flareodds = float(ltypeload.get("c_flareodds"))
        self.burnerodds = float(ltypeload.get("c_burnerodds"))
        self.underodds = float(ltypeload.get("c_underodds"))
        self.toppedodds = float(ltypeload.get("c_toppedodds"))
        self.weakodds = float(ltypeload.get("c_weakodds"))
        self.modexp = float(ltypeload.get("modexp"))
        
        self.steal_success = float(ltypeload.get("steal_success"))
        self.pickoff_success = float(ltypeload.get("pickoff_success"))	
        self.error_rate = float(ltypeload.get("error_rate"))

        self.spread_leftline = 14
        self.spread_left = 14
        self.spread_centerleft = 14
        self.spread_center = 16
        self.spread_centerright = 14
        self.spread_right = 14
        self.spread_rightline = 14

    def __repr__(self):
        return f"{self.leaguetype}"

    def Throw_Catch(self, thrower, catcher, depth):
        throw = self.ThrowErrorEval(thrower, depth)
        catch = self.CatchErrorEval(catcher, depth)
        return throw, catch

    def ThrowErrorEval(self, thrower, depth):
        diceroll = np.random.rand()
        tta = (thrower.throwacc - 50)/50
        ttp = (thrower.throwpower - 50)/50
        cscores = [tta, ttp]
        if depth == 'outfield':
            cweights = [2, 1]
        elif depth == 'infield':
            cweights = [1, 0]

        error_rate = 1 - (1+np.average(cscores, weights=cweights))*self.error_rate
        if error_rate > diceroll:
            return True 
        else: 
            return False

    def CatchErrorEval(self, catcher, depth):
        diceroll = np.random.rand()
        cfs = (catcher.fieldspot - 50)/50
        cfr = (catcher.fieldreact - 50)/50
        cfc = (catcher.fieldcatch - 50)/50
        cscores = [cfs, cfr, cfc]
        if depth == 'outfield':
            cweights = [4, 2, 3]
        elif depth == 'infield':
            cweights = [1, 2, 3]

        error_rate = 1 - (1+np.average(cscores, weights=cweights))*self.error_rate
        if error_rate > diceroll:
            return True 
        else: 
            return False

    def LoadLeagueType(ruletype):
        directory = f'..\\Baselines\\'
        keyword = "_" + ruletype + "_.csv"
        for fname in os.listdir(directory):
            if keyword in fname:
                #print(fname, "has the keyword")
                rules = Baselines.pullbaseline(directory+fname)
                #print(rules)
                return rules[0]
            
    def pullbaseline(directory):
        _baselines = []
        #print(directory)
        with open(directory, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', )
            for row in reader:
                _baselines.append(row)
        #print(_baselines)
        return _baselines




