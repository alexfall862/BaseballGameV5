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

    def LoadBaselineJSON(directory):
        with open(str(directory)) as f:
            data=json.load(f)
        return data

    def LoadLeagueType(ruletype):
        print(ruletype)
        directory = f'..\\Baselines\\'
        keyword = "_" + "baseline" + "_.json"
        for fname in os.listdir(directory):
            if keyword in fname:
                rules = Baselines.LoadBaselineJSON(directory+fname)
                return rules[0][ruletype]
            

