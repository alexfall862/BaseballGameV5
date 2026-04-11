import csv
import os
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
        self.stealawareness_max = float(baselines["stealawareness_max"])
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

        # Feature tunables
        self.consecutive_pitch_debuff_scale = float(load.get("consecutive_pitch_debuff_scale", 1.5))
        self.battery_iq_weight = float(load.get("battery_iq_weight", 0.5))
        self.arm_angle_familiarity_increment = float(load.get("arm_angle_familiarity_increment", 1.0))
        self.velocity_swing_suppression_max = float(load.get("velocity_swing_suppression_max", 0.05))
        self.control_strike_floor = float(load.get("control_strike_floor", 0.35))
        self.control_strike_ceiling = float(load.get("control_strike_ceiling", 0.70))
        self.consist_degrade_max = float(load.get("consist_degrade_max", 0.45))
        self.consist_degrade_min = float(load.get("consist_degrade_min", 0.05))
        self.consist_exponent_low = float(load.get("consist_exponent_low", 1.2))
        self.consist_exponent_high = float(load.get("consist_exponent_high", 3.0))
        self.steal_awareness_exponent = float(load.get("steal_awareness_exponent", 2.0))

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
        instance.barrelodds = float(baselines.get("c_barrelodds", 6))
        instance.solidodds = float(baselines.get("c_solidodds", 10))
        instance.flareodds = float(baselines.get("c_flareodds", 13))
        instance.burnerodds = float(baselines.get("c_burnerodds", 15))
        instance.underodds = float(baselines.get("c_underodds", 20))
        instance.toppedodds = float(baselines.get("c_toppedodds", 33))
        instance.weakodds = float(baselines.get("c_weakodds", 4))
        instance.modexp = float(baselines.get("modexp", 2))
        instance.steal_success = float(baselines.get("steal_success", 0.65))
        instance.pickoff_success = float(baselines.get("pickoff_success", 0.1))
        instance.stealawareness_max = float(baselines.get("stealawareness_max", 0.80))
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

        instance.shortleash = data.get("shortleash", 0.85)
        instance.normalleash = data.get("normalleash", 0.8)
        instance.longleash = data.get("longleash", 0.7)

        # Feature tunables
        instance.consecutive_pitch_debuff_scale = float(data.get("consecutive_pitch_debuff_scale", 1.5))
        instance.battery_iq_weight = float(data.get("battery_iq_weight", 0.5))
        instance.arm_angle_familiarity_increment = float(data.get("arm_angle_familiarity_increment", 1.0))
        instance.velocity_swing_suppression_max = float(data.get("velocity_swing_suppression_max", 0.05))
        instance.control_strike_floor = float(data.get("control_strike_floor", 0.35))
        instance.control_strike_ceiling = float(data.get("control_strike_ceiling", 0.70))
        instance.consist_degrade_max = float(data.get("consist_degrade_max", 0.45))
        instance.consist_degrade_min = float(data.get("consist_degrade_min", 0.05))
        instance.consist_exponent_low = float(data.get("consist_exponent_low", 1.2))
        instance.consist_exponent_high = float(data.get("consist_exponent_high", 3.0))
        instance.steal_awareness_exponent = float(data.get("steal_awareness_exponent", 1.4))

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
            

