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
        self.fieldingweights = load["fieldingweights"]  # Deprecated
        self.fieldingoutcomes = load["fieldingoutcomes"]  # Deprecated
        self.catch_rates = load.get("catch_rates", {})  # New system
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

    @classmethod
    def from_dict(cls, data: dict, leaguetype: str = "endpoint"):
        """
        Create a Baselines instance from a pre-adapted dictionary.

        Args:
            data: Dict containing all baseline data (from BaselineAdapter.adapt())
            leaguetype: Label for this baseline set

        Returns:
            Baselines instance
        """
        instance = object.__new__(cls)
        instance.leaguetype = leaguetype

        baselines = data.get("baselines", {})
        instance.outsideswing = float(baselines.get("OutsideSwing", 0.3))
        instance.outsidelook = float(1 - instance.outsideswing)
        instance.outsidecontact = float(baselines.get("OutsideContact", 0.66))
        instance.insideswing = float(baselines.get("InsideSwing", 0.65))
        instance.insidelook = float(1 - instance.insideswing)
        instance.insidecontact = float(baselines.get("InsideContact", 0.87))
        instance.barrelodds = float(baselines.get("c_barrelodds", 7))
        instance.solidodds = float(baselines.get("c_solidodds", 12))
        instance.flareodds = float(baselines.get("c_flareodds", 36))
        instance.burnerodds = float(baselines.get("c_burnerodds", 39))
        instance.underodds = float(baselines.get("c_underodds", 2.4))
        instance.toppedodds = float(baselines.get("c_toppedodds", 3.2))
        instance.weakodds = float(baselines.get("c_weakodds", 0.4))
        instance.modexp = float(baselines.get("modexp", 2))
        instance.steal_success = float(baselines.get("steal_success", 0.65))
        instance.pickoff_success = float(baselines.get("pickoff_success", 0.1))
        instance.error_rate = float(baselines.get("error_rate", 0.05))

        spread = data.get("spread", {})
        instance.spread_leftline = spread.get("leftline", 14)
        instance.spread_left = spread.get("left", 14)
        instance.spread_centerleft = spread.get("centerleft", 14)
        instance.spread_center = spread.get("center", 14)
        instance.spread_centerright = spread.get("centerright", 14)
        instance.spread_right = spread.get("right", 14)
        instance.spread_rightline = spread.get("rightline", 14)

        instance.distweights = data.get("distweights", {})
        instance.distoutcomes = data.get("distoutcomes", [])
        instance.fieldingweights = data.get("fieldingweights", {})  # Deprecated
        instance.fieldingoutcomes = data.get("fieldingoutcomes", [])  # Deprecated
        instance.catch_rates = data.get("catch_rates", {})  # New system
        instance.defensivealignment = data.get("defensivealignment", {})
        instance.fieldingmod = data.get("fieldingmod", {})
        instance.fieldingmultiplier = data.get("fieldingmultiplier", 0)
        instance.directlyat = data.get("directlyat", [])
        instance.onestepaway = data.get("onestepaway", [])
        instance.twostepaway = data.get("twostepaway", [])
        instance.threestepaway = data.get("threestepaway", [])
        instance.homerun = data.get("homerun", [])
        instance.timetoground = data.get("timetoground", {})

        instance.energytickcap = data.get("energytickcap", 1.5)
        instance.energystep = data.get("energystep", 2)

        instance.shortleash = data.get("shortleash", 0.8)
        instance.normalleash = data.get("normalleash", 0.7)
        instance.longleash = data.get("longleash", 0.5)

        return instance

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
            

