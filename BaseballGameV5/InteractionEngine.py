import random 

class PitchEvent():
    def __init__(self, action):
        self.batter = action.game.battingteam.currentbatter
        self.pitcher = action.game.pitchingteam.currentpitcher
        self.outsideswing = action.game.baselines.outsideswing
        self.outsidelook = action.game.baselines.outsidelook
        self.outsidecontact = action.game.baselines.outsidecontact
        self.insideswing = action.game.baselines.insideswing
        self.insidelook = action.game.baselines.insidelook
        self.insidecontact = action.game.baselines.insidecontact
        self.pitch = self.choosepitch(action.game.pitchingteam.currentpitcher, action.gane.pitchingteam.catcher)
        
    def choosepitch(pitcher, catcher):
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
        pitchchoice = random.chocies([*pitchlist],[*pitchodds], k=1)[0]
        return pitchchoice
    
    def runpitcheval(self):
        self.outcome = BattedBallEvent(self).outcome

class BattedBallEvent():
    def __init__(self):
        pass
    

