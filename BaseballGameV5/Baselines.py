import csv 
import os 

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




