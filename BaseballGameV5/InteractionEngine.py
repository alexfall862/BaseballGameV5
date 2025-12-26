import random 

class PitchEvent():
    def __init__(self, action):
        self.action = action
        self.batter = action.game.battingteam.currentbatter
        self.pitcher = action.game.pitchingteam.currentpitcher
        self.outsideswing = action.game.baselines.outsideswing
        self.outsidelook = action.game.baselines.outsidelook
        self.outsidecontact = action.game.baselines.outsidecontact
        self.insideswing = action.game.baselines.insideswing
        self.insidelook = action.game.baselines.insidelook
        self.insidecontact = action.game.baselines.insidecontact
        self.pitch, self.pitchlocation = self.choosepitch(action.game.pitchingteam.currentpitcher, action.game.pitchingteam.catcher)
        
        self.runpitcheval() 
        self.pitcher.pitchingstats.Adder("pitches_thrown", 1)


    def choosepitch(self, pitcher, catcher):
        pitchlist = [
            pitcher.pitch1,
            pitcher.pitch2,
            pitcher.pitch3,
            pitcher.pitch4,
            pitcher.pitch5
            ]
        pitchodds = [
            5,4,3,2,1
            ]
        pitchchoice = random.choices([*pitchlist],[*pitchodds], k=1)[0]
        pitchlocation = random.choices(["Inside", "Outside"], [1, 1.2], k=1)[0]
        return pitchchoice, pitchlocation
    
    def runpitcheval(self):
        # Ensure no division by zero - use minimum value of 1
        pitch_ovr = max(self.pitch.ovr, 1)
        batter_contact = max(self.batter.contact, 1)
        batter_eye = max(self.batter.eye, 1)
        batter_discipline = max(self.batter.discipline, 1)

        bat_cont_mod = float(batter_contact / pitch_ovr)
        pitch_cont_mod = float(pitch_ovr / batter_contact)
        bat_eye_mod = float(batter_eye / pitch_ovr)
        pitch_eye_mod = float(pitch_ovr / batter_eye)
        bat_disc_mod = float(batter_discipline / pitch_ovr)
        pitch_disc_mod = float(pitch_ovr / batter_discipline)

        if self.pitchlocation == "Inside":
            swing_w = self.insideswing * pitch_disc_mod
            look_w = self.insidelook * bat_disc_mod
        elif self.pitchlocation == "Outside":
            swing_w = self.outsideswing * bat_disc_mod
            look_w = self.outsidelook * pitch_disc_mod
        else:
            swing_w = 0.5
            look_w = 0.5

        # Normalize weights, with fallback for zero sum
        total_w = swing_w + look_w
        if total_w <= 0:
            swing_w = 0.5
            look_w = 0.5
        else:
            swing_w = swing_w / total_w
            look_w = look_w / total_w

        firstpassoutcome = random.choices(
            ["Swing", "Look"], [swing_w, look_w], k=1
        )[0]

        #first send outcome chance
        if firstpassoutcome == "Look":
            if self.pitchlocation == "Outside":
                self.outcome = ["Ball", "Looking", self.pitch.name]
                self.pitcher.pitchingstats.Adder("balls", 1)
                return self.outcome
            elif self.pitchlocation == "Inside":
                self.outcome = ["Strike", "Looking", self.pitch.name]
                self.pitcher.pitchingstats.Adder("strikes", 1)
                return self.outcome

        if firstpassoutcome == "Swing":
            if self.pitchlocation == "Outside":
                Whiff = (1 - self.outsidecontact) * pitch_eye_mod
                InPlay = (self.outsidecontact * .4) * bat_cont_mod
                Foul = (self.outsidecontact * .6) * pitch_cont_mod
            elif self.pitchlocation == "Inside":
                Whiff = (1 - self.insidecontact) * pitch_eye_mod
                InPlay = (self.insidecontact / 2) * bat_cont_mod
                Foul = (self.insidecontact / 2) * pitch_cont_mod
            else:
                Whiff = 0.33
                InPlay = 0.33
                Foul = 0.34

        # Ensure valid weights for second pass
        second_weights = [Whiff, InPlay, Foul]
        second_weights = [max(0, w) if w == w else 0 for w in second_weights]
        if sum(second_weights) <= 0:
            second_weights = [1, 1, 1]

        secondpassoutcome = random.choices(
            ["Whiff", "InPlay", "Foul"], second_weights, k=1
        )[0]

        if secondpassoutcome == "Whiff":
            self.outcome = ["Strike", "Swinging", self.pitch.name]
            self.pitcher.pitchingstats.Adder("strikes", 1)
            return self.outcome
        elif secondpassoutcome == "Foul":
            self.outcome = ["Strike", "Foul", self.pitch.name]
            self.pitcher.pitchingstats.Adder("strikes", 1)
            return self.outcome
        elif secondpassoutcome == "InPlay":
            self.outcome = BattedBallEvent(self).outcome
            return self.outcome
    
class BattedBallEvent():
    def __init__(self, pitchevent):
        self.pitchevent = pitchevent
        self.batter = pitchevent.batter
        self.pitcher = pitchevent.pitcher
        self.barrelodds = pitchevent.action.game.baselines.barrelodds
        self.solidodds = self.pitchevent.action.game.baselines.solidodds
        self.flareodds = self.pitchevent.action.game.baselines.flareodds
        self.burnerodds = self.pitchevent.action.game.baselines.burnerodds
        self.underodds = self.pitchevent.action.game.baselines.underodds
        self.toppedodds = self.pitchevent.action.game.baselines.toppedodds
        self.weakodds = self.pitchevent.action.game.baselines.weakodds
        self.modexp = self.pitchevent.action.game.baselines.modexp
        self.handcheck()
        self.runcalc()
        self.outcome = self.diceroll()
        
    def handcheck(self):
        modamount = 5
        mina = 1
        maxa = 99
        if(self.batter.handedness[0]=="S"):
            return
        else:
            if (self.batter.handedness[0]==self.pitcher.handedness[1]):
                self.batter.contact = max(self.batter.contact - modamount, mina)
                self.batter.power = max(self.batter.power - modamount, mina)
                self.batter.eye = max(self.batter.eye - modamount, mina)
                self.batter.discipline = max(self.batter.discipline - modamount, mina)
            elif (self.batter.handedness[0]!=self.pitcher.handedness[1]):
                self.batter.contact = min(self.batter.contact + modamount, maxa)
                self.batter.power = min(self.batter.power + modamount, maxa)
                self.batter.eye = min(self.batter.eye + modamount, maxa)
                self.batter.discipline = min(self.batter.discipline + modamount, maxa)                  
    def setweights(self):
        # Ensure pitch ovr and batter stats are never zero to prevent division issues
        pitch_ovr = max(self.pitchevent.pitch.ovr, 1)
        batter_contact = max(self.batter.contact, 1)
        batter_power = max(self.batter.power, 1)

        self.barrelw: float = ((((batter_contact) + (batter_power*4))/5)/pitch_ovr)**self.modexp
        self.solidw: float = ((((batter_contact) + (batter_power*2))/3)/pitch_ovr)**self.modexp
        self.leftoverspace = 1 - (min((self.barrelodds * self.barrelw)/100, .4) + min((self.solidodds * self.solidw)/100, .4))
        # Ensure leftoverspace is positive
        self.leftoverspace = max(self.leftoverspace, 0.1)

        self.flarew: float = ((batter_contact/pitch_ovr)**self.modexp)
        self.burnerw: float = ((batter_contact/pitch_ovr)**self.modexp)
        self.underw: float = ((pitch_ovr/batter_contact)**self.modexp)
        self.toppedw: float = ((pitch_ovr/batter_contact)**self.modexp)
        self.weakw: float = ((pitch_ovr/batter_contact)**self.modexp)
        self.leftoverweight = ((self.flarew*self.flareodds) +
                               (self.burnerw*self.burnerodds) +
                               (self.underw*self.underodds) +
                               (self.toppedw*self.toppedodds) +
                               (self.weakw*self.weakodds)
                               )
        # Ensure leftoverweight is never zero to prevent division by zero
        self.leftoverweight = max(self.leftoverweight, 0.001)        
    def runcalc(self):
        self.setweights()
        self.barrelodds = min((self.barrelodds * self.barrelw)/100, .4)
        self.solidodds = min((self.solidodds * self.solidw)/100, .4)
        self.flareodds = ((self.flareodds * self.flarew)/self.leftoverweight)*self.leftoverspace
        self.burnerodds = ((self.burnerodds * self.burnerw)/self.leftoverweight)*self.leftoverspace
        self.underodds = ((self.underodds * self.underw)/self.leftoverweight)*self.leftoverspace
        self.toppedodds = ((self.toppedodds * self.toppedw)/self.leftoverweight)*self.leftoverspace
        self.weakodds = ((self.weakodds * self.weakw)/self.leftoverweight)*self.leftoverspace        

    def diceroll(self):
        direction = self.direction()
        outcomes = ["barrel", "solid", "flare", "burner", "under", "topped", "weak"]
        weights = [
            self.barrelodds,
            self.solidodds,
            self.flareodds,
            self.burnerodds,
            self.underodds,
            self.toppedodds,
            self.weakodds
        ]
        # Ensure all weights are valid numbers and non-negative
        weights = [max(0, w) if w == w else 0 for w in weights]  # NaN check: w != w means NaN
        # If all weights are zero, use equal weights as fallback
        if sum(weights) <= 0:
            weights = [1, 1, 1, 1, 1, 1, 1]
        bbeoutcome = random.choices(outcomes, weights=weights, k=1)[0]
        return [bbeoutcome, direction, self.pitchevent.pitch.name]
    
    def direction(self):
        leftline = self.pitchevent.action.game.baselines.spread_leftline
        left = self.pitchevent.action.game.baselines.spread_left
        centerleft = self.pitchevent.action.game.baselines.spread_centerleft
        center = self.pitchevent.action.game.baselines.spread_center
        centerright = self.pitchevent.action.game.baselines.spread_centerright
        right = self.pitchevent.action.game.baselines.spread_right
        rightline = self.pitchevent.action.game.baselines.spread_rightline

        directions = ["far left", "left", "center left", "dead center", "center right", "right", "far right"]
        weights = [leftline, left, centerleft, center, centerright, right, rightline]
        # Ensure all weights are valid and non-negative
        weights = [max(0, w) if w == w else 0 for w in weights]
        # Fallback if all weights are zero
        if sum(weights) <= 0:
            weights = [14, 14, 14, 14, 14, 14, 14]  # Default spread
        directionpicker = random.choices(directions, weights=weights, k=1)[0]
        return directionpicker

    def __repr__(self):
        return f"CT: {self.barrelodds}\nCT: {self.solidodds}\nCT: {self.flareodds}\nCT: {self.burnerodds}\nCT: {self.underodds}\nCT: {self.toppedodds}\nCT: {self.weakodds}\n"
