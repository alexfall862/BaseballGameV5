import csv 
import os 
import numpy as np
import json 

class Baselines():
    def __init__(self, leaguetype):
        self.leaguetype = leaguetype
        load = Baselines.LoadLeagueType(self.leaguetype)

        baselines = load["baselines"]
        self.outsideswing = float(baselines["OutsideSwing"])
        self.outsidelook = float(1 - self.outsideswing)
        self.outsidecontact = float(baselines["OutsideContact"])
        self.insideswing = float(baselines["InsideSwing"])
        self.insidelook = float(1 - self.insideswing)
        self.insidecontact = float(baselines["InsideContact"])
        self.barrelodds = float(baselines["c_barrelodds"])
        self.solidodds = float(baselines["c_solidodds"])
        self.flareodds = float(baselines["c_flareodds"])
        self.burnerodds = float(baselines["c_burnerodds"])
        self.underodds = float(baselines["c_underodds"])
        self.toppedodds = float(baselines["c_toppedodds"])
        self.weakodds = float(baselines["c_weakodds"])
        self.modexp = float(baselines["modexp"])    
        self.steal_success = float(baselines["steal_success"])
        self.pickoff_success = float(baselines["pickoff_success"])	
        self.error_rate = float(baselines["error_rate"])

        spread = load["spread"]
        self.spread_leftline = spread["leftline"]
        self.spread_left = spread["left"]
        self.spread_centerleft = spread["centerleft"]
        self.spread_center = spread["center"]
        self.spread_centerright = spread["centerright"]
        self.spread_right = spread["right"]
        self.spread_rightline = spread["rightline"]

        self.distweights = load["distweights"]
        self.distoutcomes = load["distoutcomes"]
        self.fieldingweights = load["fieldingweights"]
        self.fieldingoutcomes = load["fieldingoutcomes"]
        self.defensivealignment = load["defensivealignment"]
        self.fieldingmod = load["fieldingmod"]
        self.fieldingmultiplier = load["fieldingmultiplier"]
        self.directlyat = load["directlyat"]
        self.onestepaway = load["onestepaway"]
        self.twostepaway = load["twostepaway"]
        self.threestepaway = load["threestepaway"]
        self.homerun = load["homerun"]
        self.timetoground = load["timetoground"]

        self.energytickcap = load["energytickcap"]
        self.energystep = load["energystep"]

        self.shortleash = load["shortleash"]
        self.normalleash = load["normalleash"]
        self.longleash = load["longleash"]

    def __repr__(self):
        return f"{self.leaguetype}"

    # def Throw_Catch(self, thrower, catcher):
    #     #print("Is this causing it?")
    #     if thrower == None:
    #         throw = False
    #         catch = self.CatchErrorEval(thrower, catcher)
    #     else:
    #         throw = self.ThrowErrorEval(thrower)
    #         catch = self.CatchErrorEval(thrower, catcher)
    #     return throw, catch

    # def ThrowErrorEval(self, thrower):
    #     depth = self.Depth(thrower)
    #     diceroll = np.random.rand()
    #     tta = (thrower.throwacc - 50)/50
    #     ttp = (thrower.throwpower - 50)/50
    #     cscores = [tta, ttp]
    #     if depth == 'outfield':
    #         cweights = [2, 1]
    #     elif depth == 'infield':
    #         cweights = [1, 0]

    #     error_rate = (1+np.average(cscores, weights=cweights))*self.error_rate
    #     #print(f"BASELINE ERROR FORM CHECK THROW: {error_rate}/{diceroll}")
    #     if error_rate > diceroll:
    #         #print(True)
    #         thrower.fieldingstats.Adder("throwing_errors", 1)
    #         return True 
    #     else: 
    #         return False

    # def CatchErrorEval(self, thrower, catcher):
    #     if thrower == None:
    #         if catcher.lineup == 'leftfield' or catcher.lineup == 'centerfield' or catcher.lineup == 'rightfield':
    #             depth = 'outfield'
    #         else:
    #             depth = 'infield'
    #     elif thrower != None:
    #         depth = self.Depth(thrower)

    #     diceroll = np.random.rand()
    #     cfs = (catcher.fieldspot - 50)/50
    #     cfr = (catcher.fieldreact - 50)/50
    #     cfc = (catcher.fieldcatch - 50)/50
    #     cscores = [cfs, cfr, cfc]
    #     if depth == 'outfield':
    #         cweights = [4, 2, 3]
    #     elif depth == 'infield':
    #         cweights = [1, 2, 3]

    #     error_rate = (1+np.average(cscores, weights=cweights))*self.error_rate
    #     #print(f"BASELINE ERROR FORM CHECK CATCH: {error_rate}/{diceroll}")
    #     if error_rate > diceroll:
    #         #print(True)
    #         catcher.fieldingstats.Adder("catching_errors", 1)
    #         return True 
    #     else: 
    #         return False

    # def Depth(self, thrower):
    #     if thrower.lineup == 'leftfield' or thrower.lineup == 'centerfield' or thrower.lineup == 'rightfield':
    #         return 'outfield'
    #     else:
    #         return 'infield'


    def LoadBaselineJSON(directory):
        with open(str(directory)) as f:
            data=json.load(f)
        return data

    def LoadLeagueType(ruletype):
        directory = f'..\\Baselines\\'
        keyword = "_" + "baseline" + "_.json"
        for fname in os.listdir(directory):
            if keyword in fname:
                #print(fname, "has the keyword")
                #rules = Baselines.pullbaseline(directory+fname)
                rules = Baselines.LoadBaselineJSON(directory+fname)
                #print(rules)
                return rules[0][ruletype]
            
    # def pullbaseline(directory):
    #     _baselines = []
    #     #print(directory)
    #     with open(directory, 'r', newline='') as csvfile:
    #         reader = csv.DictReader(csvfile, delimiter=',', )
    #         for row in reader:
    #             _baselines.append(row)
    #     #print(_baselines)
    #     return _baselines




