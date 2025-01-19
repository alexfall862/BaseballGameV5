from Roster import Roster as r
from Strategy import Strategy as s
from Baselines import Baselines as b
import Fatigue as f
import Player
import os

class Team():
    def __init__(self, name, travelstatus, pitchervalue, baselines):
        self.name = name
        self.baselines = baselines
        self.travelstatus = travelstatus
        self.roster = r(self.name)
        self.strategy = s(self.name)
        self.score = 0
        self.catcher = Team.GrabPositionPlayer(self, 'catcher')
        self.firstbase = Team.GrabPositionPlayer(self, 'firstbase')
        self.secondbase = Team.GrabPositionPlayer(self, 'secondbase')
        self.thirdbase = Team.GrabPositionPlayer(self, 'thirdbase')
        self.shortstop = Team.GrabPositionPlayer(self, 'shortstop')
        self.leftfield = Team.GrabPositionPlayer(self, 'leftfield')
        self.centerfield = Team.GrabPositionPlayer(self, 'centerfield')
        self.rightfield = Team.GrabPositionPlayer(self, 'rightfield')
        self.designatedhitter = Team.GrabPositionPlayer(self, 'designatedhitter')
        self.battinglist = sorted([
            self.catcher, 
            self.firstbase, 
            self.secondbase, 
            self.thirdbase, 
            self.shortstop, 
            self.leftfield, 
            self.centerfield, 
            self.rightfield, 
            self.designatedhitter, 
            ], key=lambda x: x.battingorder)
        self.currentbatspot = 1
        self.currentbatter = Team.GrabBatter(self, self.currentbatspot)
        self.currentpitcher = Team.GrabStartingPitcher(self, pitchervalue)
        self.reliefpitchers = Team.GrabReliefPitchers(self)
        self.benchplayers = Team.GrabBenchBats(self)
    
    def TickBatter(self):
        self.TickBatSpot()
        self.currentbatter = self.GrabBatter(self.currentbatspot)

    def TickBatSpot(self):
        if self.currentbatspot < 9:
            self.currentbatspot +=1
        else:
            self.currentbatspot = 1

    def GrabBatter(self, currentbatspot):
        return self.battinglist[(currentbatspot-1)]

    def GrabPositionPlayer(self, position):
        return [player for player in self.roster.playerlist if player.lineup==position][0]
       
    def GrabStartingPitcher(self, pitchervalue):
        return [player for player in self.roster.playerlist if player.lineup=="starter" and player.pitchingorder==int(pitchervalue)][0]
    
    def GrabBenchBats(self):
        return [player for player in self.roster.playerlist if player.lineup=="bench"]
    
    def GrabReliefPitchers(self):
        return [player for player in self.roster.playerlist if player.lineup=="relief" and player.energy >= 75]
    
    def ChooseReliefPitcher(self):
        rpitchers = sorted(self.reliefpitchers, key=lambda x: x.rp_rating, reverse=True)
        newpitcher = self.reliefpitchers.pop(0)
        self.currentpitcher = newpitcher
        
    def ChooseBenchBat(self, subbedplayer):
        cpref = sorted(self.benchplayers, key=lambda x: x.c_rating, reverse=True)
        fbpref = sorted(self.benchplayers, key=lambda x: x.fb_rating, reverse=True)
        sbpref = sorted(self.benchplayers, key=lambda x: x.sb_rating, reverse=True)
        tbpref = sorted(self.benchplayers, key=lambda x: x.tb_rating, reverse=True)
        sspref = sorted(self.benchplayers, key=lambda x: x.ss_rating, reverse=True)
        lfpref = sorted(self.benchplayers, key=lambda x: x.lf_rating, reverse=True)
        cfpref = sorted(self.benchplayers, key=lambda x: x.cf_rating, reverse=True)
        rfpref = sorted(self.benchplayers, key=lambda x: x.rf_rating, reverse=True)
        dhpref = sorted(self.benchplayers, key=lambda x: x.dh_rating, reverse=True)
        
        def switch(position):
            if position == 'catcher':
                return cpref[0]
            elif position == 'firstbase':
                return fbpref[0]        
            elif position == 'secondbase':
                return sbpref[0]        
            elif position == 'thirdbase':
                return tbpref[0]        
            elif position == 'shortstop':
                return sspref[0]        
            elif position == 'leftfield':
                return lfpref[0]        
            elif position == 'centerfield':
                return cfpref[0]        
            elif position == 'rightfield':
                return rfpref[0]        
            elif position == 'designatedhitter':
                return dhpref[0]        
            else:
                return 'fail'
            
        sub = switch(subbedplayer.lineup)
        subid = find_index(self.benchplayers, 'id', sub.id)
        #print(f"{subid}: {sub}")
        sub = self.benchplayers.pop(subid)
        
        sub.lineup = subbedplayer.lineup
        sub.battingorder = subbedplayer.battingorder
        
        starterid = find_index(self.battinglist, 'lineup', subbedplayer.lineup)
        self.battinglist[starterid] = sub

    def TickInningsPlayed(self):
        
        defenders = [defender for defender in self.battinglist if defender.lineup!="designatedhitter"]

        for defender in defenders:
            defender.fieldingstats.Adder("innings_played", 1/3)
            
        self.TickInningsPitched()
            
    def TickInningsPitched(self):
        self.currentpitcher.pitchingstats.Adder("innings_pitched", 1/3)
        self.currentpitcher.fieldingstats.Adder("innings_played", 1/3)

    def TickPitcherStamina(self):
        f.TickEnergy(self.baselines, self.currentpitcher)
        # self.currentpitcher.energy = self.currentpitcher.energy - 1
        #print(f"{self.currentpitcher.name}: {self.currentpitcher.energy}")
        
    def TickBatterStamina(self):
        pass

    def TickDefenderStamina(self):
        pass

    def ActionAdjustments(self):
        Team.AttributeReCalc(self)
        Team.InjuryCheck(self)

    def AttributeReCalc(self):
        for player in self.battinglist:
            player.AbilityMod()
        self.currentpitcher.AbilityMod()

    def InjuryCheck(self):
        pass

    def DecidePitchingChange(self):
        playerstrat = [playerstrat for playerstrat in self.strategy.playerstrategy if playerstrat.id == self.currentpitcher.id][0]


        if self.currentpitcher.pitchingstats.pitches_thrown > playerstrat.pitchpull:
            print(f"pitches exceeded {self.currentpitcher.pitchingstats.pitches_thrown} / {playerstrat.pitchpull}")
            self.ChooseReliefPitcher()
        
        if playerstrat.pulltend == 'normal':
            pulltend = self.baselines.normalleash
        elif playerstrat.pulltend == 'quick':
            pulltend = self.baselines.shortleash
        elif playerstrat.pulltend == 'long':
            pulltend = self.baselines.longleash

        if self.currentpitcher.abilitymodifierscore < pulltend:
            print(f"manager pulls: {playerstrat.pulltend} / {self.currentpitcher.pitchingstats.pitches_thrown} / {self.currentpitcher.abilitymodifierscore}")
            self.ChooseReliefPitcher()

def find_index(objectlist, attribute, targetvalue):
    for index, obj in enumerate(objectlist):
        if getattr(obj, attribute) == targetvalue:
            return index
    return -1