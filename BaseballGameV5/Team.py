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

    @classmethod
    def from_players(cls, name: str, players: list, baselines, use_dh: bool = True,
                     travelstatus: str = "home"):
        """
        Create a Team instance from a pre-built list of Player objects.

        Args:
            name: Team name/abbreviation
            players: List of Player objects (already adapted from endpoint)
            baselines: Baselines instance
            use_dh: Whether DH rule is in effect
            travelstatus: Travel status (home/away)

        Returns:
            Team instance
        """
        instance = object.__new__(cls)
        instance.name = name
        instance.baselines = baselines
        instance.travelstatus = travelstatus
        instance.score = 0

        # Store all players for reference
        instance._all_players = players

        # Create a mock roster object with playerlist
        class MockRoster:
            def __init__(self, playerlist):
                self.playerlist = playerlist
        instance.roster = MockRoster(players)

        # Create a mock strategy object
        class MockStrategy:
            def __init__(self, players):
                self.playerstrategy = []
                for p in players:
                    class PlayerStrat:
                        def __init__(self, player):
                            self.id = player.id
                            # Use player's usage_preference if available
                            pref = getattr(player, 'usage_preference', 'normal')
                            self.pitchpull = 100 if pref == 'normal' else (80 if pref == 'short' else 120)
                            self.pulltend = pref if pref in ['normal', 'quick', 'long'] else 'normal'
                            # Strategy values from player (endpoint data)
                            self.stealfreq = getattr(player, 'stealfreq', 10.0)
                            self.pickofffreq = getattr(player, 'pickofffreq', 10.0)
                            self.plate_approach = getattr(player, 'plate_approach', 'normal')
                            self.pitchchoices = getattr(player, 'pitchchoices', [])
                    self.playerstrategy.append(PlayerStrat(p))
        instance.strategy = MockStrategy(players)

        # Grab position players
        instance.catcher = instance._grab_position_from_list(players, 'catcher')
        instance.firstbase = instance._grab_position_from_list(players, 'firstbase')
        instance.secondbase = instance._grab_position_from_list(players, 'secondbase')
        instance.thirdbase = instance._grab_position_from_list(players, 'thirdbase')
        instance.shortstop = instance._grab_position_from_list(players, 'shortstop')
        instance.leftfield = instance._grab_position_from_list(players, 'leftfield')
        instance.centerfield = instance._grab_position_from_list(players, 'centerfield')
        instance.rightfield = instance._grab_position_from_list(players, 'rightfield')

        # Handle DH or pitcher batting
        if use_dh:
            instance.designatedhitter = instance._grab_position_from_list(players, 'designatedhitter')
        else:
            # Pitcher bats 9th when no DH
            starter = instance._grab_starting_pitcher_from_list(players)
            starter.battingorder = 9
            starter.lineup = "designatedhitter"  # For batting list purposes
            instance.designatedhitter = starter

        # Build batting list
        batting_players = [
            instance.catcher,
            instance.firstbase,
            instance.secondbase,
            instance.thirdbase,
            instance.shortstop,
            instance.leftfield,
            instance.centerfield,
            instance.rightfield,
            instance.designatedhitter,
        ]
        instance.battinglist = sorted(batting_players, key=lambda x: x.battingorder)

        instance.currentbatspot = 1
        instance.currentbatter = instance.battinglist[0]

        # Grab pitchers
        instance.currentpitcher = instance._grab_starting_pitcher_from_list(players)
        instance.currentpitcher.pitchingstats.Adder("games_started", 1)

        instance.reliefpitchers = [p for p in players if p.lineup == "relief" and p.energy >= 75]
        instance.benchplayers = [p for p in players if p.lineup == "bench"]

        return instance

    def _grab_position_from_list(self, players: list, position: str):
        """Grab a position player from the player list."""
        matches = [p for p in players if p.lineup == position]
        if matches:
            starter = matches[0]
            starter.battingstats.Adder("games_started", 1)
            starter.battingstats.Adder("game_appearances", 1)
            return starter
        return None

    def _grab_starting_pitcher_from_list(self, players: list):
        """Grab the starting pitcher from the player list."""
        matches = [p for p in players if p.lineup == "starter"]
        if matches:
            return matches[0]
        return None
    
    def TickBatter(self):
        self.TickBatSpot()
        self.currentbatter = self.GrabBatter(self.currentbatspot)
        self.currentbatter.battingstats.Adder("plate_appearances", 1)

    def TickBatSpot(self):
        if self.currentbatspot < 9:
            self.currentbatspot +=1
        else:
            self.currentbatspot = 1

    def GrabBatter(self, currentbatspot):
        return self.battinglist[(currentbatspot-1)]

    def GrabPositionPlayer(self, position):
        starter = [player for player in self.roster.playerlist if player.lineup==position][0]
        starter.battingstats.Adder("games_started", 1)
        starter.battingstats.Adder("game_appearances", 1)
        return starter
       
    def GrabStartingPitcher(self, pitchervalue):
        starter = [player for player in self.roster.playerlist if player.lineup=="starter" and player.pitchingorder==int(pitchervalue)][0]
        starter.pitchingstats.Adder("games_started", 1)
        return starter
    
    def GrabBenchBats(self):
        return [player for player in self.roster.playerlist if player.lineup=="bench"]
    
    def GrabReliefPitchers(self):
        return [player for player in self.roster.playerlist if player.lineup=="relief" and player.energy >= 75]
    
    def ChooseReliefPitcher(self):
        rpitchers = sorted(self.reliefpitchers, key=lambda x: x.rp_rating, reverse=True)
        self.reliefpitchers = rpitchers
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
        sub = self.benchplayers.pop(subid)
        
        sub.lineup = subbedplayer.lineup
        sub.battingorder = subbedplayer.battingorder
        
        starterid = find_index(self.battinglist, 'lineup', subbedplayer.lineup)
        self.battinglist[starterid] = sub

    def TickInningsPlayed(self):
        defenders = [defender for defender in self.battinglist if defender.lineup!="designatedhitter"]

        for defender in defenders:
            defender.fieldingstats.Adder("outs_played", 1)

        self.TickInningsPitched()

    def TickInningsPitched(self):
        self.currentpitcher.pitchingstats.Adder("outs_pitched", 1)
        self.currentpitcher.fieldingstats.Adder("outs_played", 1)

    def TickPitcherStamina(self):
        f.TickEnergy(self.baselines, self.currentpitcher)
        
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
            #print(f"pitches exceeded {self.currentpitcher.pitchingstats.pitches_thrown} / {playerstrat.pitchpull}")
            #self.ChooseReliefPitcher()
            pass 

        if playerstrat.pulltend == 'normal':
            pulltend = self.baselines.normalleash
        elif playerstrat.pulltend == 'quick':
            pulltend = self.baselines.shortleash
        elif playerstrat.pulltend == 'long':
            pulltend = self.baselines.longleash

        if self.currentpitcher.abilitymodifierscore < pulltend:
            #print(f"manager pulls: {playerstrat.pulltend} / {self.currentpitcher.pitchingstats.pitches_thrown} / {self.currentpitcher.abilitymodifierscore}")
            #self.ChooseReliefPitcher()
            pass
            

def find_index(objectlist, attribute, targetvalue):
    for index, obj in enumerate(objectlist):
        if getattr(obj, attribute) == targetvalue:
            return index
    return -1