from Roster import Roster as r
from Strategy import Strategy as s
from Baselines import Baselines as b
import Fatigue as f
import Player
import os
import random

# Energy thresholds by usage_preference
USAGE_ENERGY_THRESHOLDS = {
    "only_fully_rested": 95,
    "normal": 75,
    "play_tired": 50,
    "desperation": 25,
}

# Role priority by game situation: which bullpen roles to try first
SITUATION_ROLE_ORDER = {
    "save":            ["closer", "setup", "middle", "long", "mop_up"],
    "setup":           ["setup", "middle", "closer", "long", "mop_up"],
    "middle":          ["middle", "setup", "long", "mop_up", "closer"],
    "early_relief":    ["long", "middle", "mop_up", "setup", "closer"],
    "blowout_winning": ["mop_up", "long", "middle", "setup", "closer"],
    "blowout_losing":  ["mop_up", "long", "middle", "setup", "closer"],
}

# Max outs per reliever role before pull probability kicks in
ROLE_MAX_OUTS = {
    "closer": 4,      # ~1.1 innings
    "setup": 6,       # 2 innings
    "middle": 6,      # 2 innings
    "long": 9,        # 3 innings
    "mop_up": 9,      # 3 innings
}

# Pull probability escalation rates (per out over target)
STARTER_PULL_RATE = 0.15     # 15% per out over target
RELIEVER_PULL_RATE = 0.40    # 40% per out over limit

# Soft pitch ceiling (pull probability starts here)
SOFT_PITCH_CEILING = 110
PITCH_CEILING_RATE = 0.03    # 3% per pitch over ceiling

class Team():
    def __init__(self, name, travelstatus, pitchervalue, baselines):
        self.name = name
        self.baselines = baselines
        self.travelstatus = travelstatus
        self.roster = r(self.name)
        self.strategy = s(self.name)
        self.score = 0
        self.use_dh = True
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
        self._pitching_appearance_seq = 1
        self.currentpitcher.pitch_appearance_order = 1
        self.reliefpitchers = Team.GrabReliefPitchers(self)
        self.benchplayers = Team.GrabBenchBats(self)

    @classmethod
    def from_players(cls, name: str, players: list, baselines, use_dh: bool = True,
                     travelstatus: str = "home", team_strategy: dict = None,
                     bullpen_order: list = None):
        """
        Create a Team instance from a pre-built list of Player objects.

        Args:
            name: Team name/abbreviation
            players: List of Player objects (already adapted from endpoint)
            baselines: Baselines instance
            use_dh: Whether DH rule is in effect
            travelstatus: Travel status (home/away)
            team_strategy: Team strategy dict (bullpen_cutoff, bullpen_priority, emergency_pitcher_id)
            bullpen_order: List of dicts with slot, player_id, role for bullpen ordering

        Returns:
            Team instance
        """
        instance = object.__new__(cls)
        instance.name = name
        instance.baselines = baselines
        instance.travelstatus = travelstatus
        instance.score = 0
        instance.use_dh = use_dh

        # Store all players for reference
        instance._all_players = players

        # Create a mock roster object with playerlist
        class MockRoster:
            def __init__(self, playerlist):
                self.playerlist = playerlist
        instance.roster = MockRoster(players)

        # Create a mock team strategy from payload
        ts = team_strategy or {}
        team_cutoff = ts.get("bullpen_cutoff", 85)

        class MockTeamStrategy:
            def __init__(self, data):
                self.bullpencutoff = data.get("bullpen_cutoff", 85)
                self.bullpenpriority = data.get("bullpen_priority", "best_available")
                self.emergencypitcher = data.get("emergency_pitcher_id", None)
                self.outfieldspacing = data.get("outfield_spacing", "normal")
                self.infieldspacing = data.get("infield_spacing", "normal")
                self.walklist = data.get("intentional_walk_list", [])

        # Create a mock strategy object
        class MockStrategy:
            def __init__(self, players, cutoff):
                self.playerstrategy = []
                self.teamstrategy = MockTeamStrategy(ts)
                for p in players:
                    class PlayerStrat:
                        def __init__(self, player, team_cutoff):
                            self.id = player.id
                            # Per-player pitchpull overrides team bullpen_cutoff
                            self.pitchpull = getattr(player, 'pitchpull', None) or team_cutoff
                            self.pulltend = getattr(player, 'pulltend', 'normal')
                            # Strategy values from player (endpoint data)
                            self.stealfreq = getattr(player, 'stealfreq', 10.0)
                            self.pickofffreq = getattr(player, 'pickofffreq', 10.0)
                            self.plate_approach = getattr(player, 'plate_approach', 'normal')
                            self.pitchchoices = getattr(player, 'pitchchoices', [])
                    self.playerstrategy.append(PlayerStrat(p, cutoff))
        instance.strategy = MockStrategy(players, team_cutoff)

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
        batting_candidates = {
            "catcher": instance.catcher,
            "firstbase": instance.firstbase,
            "secondbase": instance.secondbase,
            "thirdbase": instance.thirdbase,
            "shortstop": instance.shortstop,
            "leftfield": instance.leftfield,
            "centerfield": instance.centerfield,
            "rightfield": instance.rightfield,
            "designatedhitter": instance.designatedhitter,
        }
        missing = [pos for pos, player in batting_candidates.items() if player is None]
        if missing:
            raise ValueError(f"Team '{name}': no player found for position(s): {missing}")
        instance.battinglist = sorted(batting_candidates.values(), key=lambda x: x.battingorder)

        instance.currentbatspot = 1
        instance.currentbatter = instance.battinglist[0]

        # Grab pitchers
        instance.currentpitcher = starter if not use_dh else instance._grab_starting_pitcher_from_list(players)
        instance.currentpitcher.pitchingstats.Adder("games_started", 1)
        instance._pitching_appearance_seq = 1
        instance.currentpitcher.pitch_appearance_order = 1

        instance.reliefpitchers = [
            p for p in players
            if p.lineup == "relief"
            and p.energy >= USAGE_ENERGY_THRESHOLDS.get(
                getattr(p, 'usage_preference', 'normal'), 75
            )
        ]
        instance.benchplayers = [p for p in players if p.lineup == "bench"]
        instance._bullpen_empty_at_start = len(instance.reliefpitchers) == 0

        # Assign bullpen roles from bullpen_order
        bp_order = bullpen_order or []
        for entry in bp_order:
            pid = entry.get("player_id")
            role = entry.get("role", "middle")
            slot = entry.get("slot", 99)
            for rp in instance.reliefpitchers:
                if rp.id == pid:
                    rp.bullpen_role = role
                    rp.bullpen_slot = slot
                    break
        for rp in instance.reliefpitchers:
            if not hasattr(rp, 'bullpen_role'):
                rp.bullpen_role = "middle"
                rp.bullpen_slot = 99

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
        # Fallback: check for pitchingorder == 1 (starting pitcher attribute)
        fallback = [p for p in players if getattr(p, 'pitchingorder', 0) == 1]
        if fallback:
            return fallback[0]
        raise ValueError(
            f"No starting pitcher found for team '{self.name}'. "
            f"Player lineups: {[(p.name, p.lineup) for p in players]}"
        )
    
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
    
    def ChooseReliefPitcher(self, game):
        if not self.reliefpitchers:
            self._UseEmergencyPitcher(game)
            return

        newpitcher = self._SelectByRole(game)

        if newpitcher:
            self._SwapPitcher(newpitcher, game)
        else:
            # Fallback: best rp_rating regardless of role
            rpitchers = sorted(self.reliefpitchers, key=lambda x: x.rp_rating, reverse=True)
            if rpitchers:
                self._SwapPitcher(rpitchers[0], game)
            else:
                self._UseEmergencyPitcher(game)
        
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
        f.TickBatterEnergy(self.currentbatter)

    def TickDefenderStamina(self):
        for player in self.battinglist:
            f.TickDefenderEnergy(player)

    def ActionAdjustments(self):
        Team.AttributeReCalc(self)
        Team.InjuryCheck(self)

    def AttributeReCalc(self):
        for player in self.battinglist:
            player.AbilityMod()
        self.currentpitcher.AbilityMod()

    def InjuryCheck(self):
        pass

    def DecidePitchingChange(self, game):
        matches = [ps for ps in self.strategy.playerstrategy if ps.id == self.currentpitcher.id]
        if matches:
            playerstrat = matches[0]
        else:
            class DefaultStrat:
                def __init__(self, pid, cutoff):
                    self.id = pid
                    self.pitchpull = cutoff
                    self.pulltend = 'normal'
            playerstrat = DefaultStrat(self.currentpitcher.id, self.strategy.teamstrategy.bullpencutoff)

        should_pull = False

        # Trigger 1: Pitch count exceeded
        if self.currentpitcher.pitchingstats.pitches_thrown > playerstrat.pitchpull:
            should_pull = True

        # Trigger 2: Fatigue below leash threshold
        if playerstrat.pulltend == 'quick':
            pulltend = self.baselines.shortleash
        elif playerstrat.pulltend == 'long':
            pulltend = self.baselines.longleash
        else:
            pulltend = self.baselines.normalleash

        if self.currentpitcher.abilitymodifierscore < pulltend:
            should_pull = True

        # Trigger 3: Starter outs limit (probability-based, performance-gated)
        if not should_pull and self.currentpitcher.pitchingstats.games_started > 0:
            base_outs = 15
            bonus = max(0, int((self.currentpitcher.pendurance - 40) / 10))
            target_outs = min(base_outs + bonus, 24)

            outs_over = self.currentpitcher.pitchingstats.outs_pitched - target_outs
            if outs_over > 0:
                base_chance = STARTER_PULL_RATE * outs_over

                er = self.currentpitcher.pitchingstats.earned_runs
                energy_pct = self.currentpitcher.energy / max(self.currentpitcher.starting_energy, 1)

                if er <= 1 and energy_pct > 0.4:
                    perf_mod = -0.25
                elif er <= 2 and energy_pct > 0.3:
                    perf_mod = -0.10
                elif er >= 4:
                    perf_mod = 0.20
                else:
                    perf_mod = 0.0

                pull_chance = max(0.05, min(0.95, base_chance + perf_mod))
                if random.random() < pull_chance:
                    should_pull = True

        # Trigger 4: Reliever outs limit (probability-based, steep)
        if not should_pull and self.currentpitcher.pitchingstats.games_started == 0:
            role = getattr(self.currentpitcher, 'bullpen_role', 'middle')
            role_max = ROLE_MAX_OUTS.get(role, 6)
            outs_over = self.currentpitcher.pitchingstats.outs_pitched - role_max
            if outs_over > 0:
                pull_chance = max(0.10, min(0.95, RELIEVER_PULL_RATE * outs_over))
                if random.random() < pull_chance:
                    should_pull = True

        # Trigger 5: Soft pitch ceiling (any pitcher)
        if not should_pull:
            pitches = self.currentpitcher.pitchingstats.pitches_thrown
            if pitches > SOFT_PITCH_CEILING:
                overage = pitches - SOFT_PITCH_CEILING
                pull_chance = max(0.05, min(0.95, PITCH_CEILING_RATE * overage))
                if random.random() < pull_chance:
                    should_pull = True

        if should_pull:
            self.ChooseReliefPitcher(game)

    def DecideBetweenInningChange(self, game):
        """Evaluate whether to change pitchers at an inning boundary.

        Called after InningFlip updates inning/half state but before teams are
        swapped. Only applies to relievers — starters are handled by the
        existing mid-inning triggers.
        """
        if self.currentpitcher.pitchingstats.games_started > 0:
            return  # starters handled by mid-inning triggers

        # Determine what inning this team will next pitch.
        # After InningFlip, topofinning has been flipped but teams not yet swapped.
        #   topofinning is now False  → top just ended → next pitch is top of currentinning+1
        #   topofinning is now True   → bottom just ended, inning already incremented
        #                              → next pitch is bottom of currentinning
        if not game.topofinning:
            next_inning = game.currentinning + 1
        else:
            next_inning = game.currentinning

        situation = self._ClassifyGameSituation(game, inning_override=next_inning)
        role_order = SITUATION_ROLE_ORDER.get(situation, SITUATION_ROLE_ORDER["middle"])
        current_role = getattr(self.currentpitcher, 'bullpen_role', 'middle')

        # Walk the priority list. If a better-suited available pitcher is found
        # before we reach the current pitcher's role, make the change.
        for role in role_order:
            if role == current_role:
                return  # current pitcher is already the best fit for this situation
            candidates = [rp for rp in self.reliefpitchers
                          if getattr(rp, 'bullpen_role', 'middle') == role]
            if candidates:
                self.ChooseReliefPitcher(game)
                return

    def _IsSaveSituation(self, game):
        """MLB save situation: leading by 1-3, or tying run on base/at-bat/on-deck."""
        score_diff = self._GetScoreDiff(game)
        runners_on = sum(1 for r in [game.on_firstbase, game.on_secondbase, game.on_thirdbase] if r is not None)
        return self._is_entry_save_situation(score_diff, runners_on)

    def _is_entry_save_situation(self, score_diff, runners_on):
        """Check if conditions constitute a save situation per MLB rules."""
        if score_diff <= 0:
            return False
        if score_diff <= 3:
            return True
        # Tying run on base, at bat, or on deck
        if score_diff <= runners_on + 2:
            return True
        return False

    def _GetScoreDiff(self, game):
        return self.score - game.battingteam.score

    def _ClassifyGameSituation(self, game, inning_override=None):
        """Classify current game context for bullpen role selection."""
        inning = inning_override if inning_override is not None else game.currentinning
        score_diff = self._GetScoreDiff(game)
        is_save = self._IsSaveSituation(game)

        if is_save and inning >= 8:
            return "save"
        if 1 <= score_diff <= 5 and inning >= 7:
            return "setup"
        if score_diff <= -6:
            return "blowout_losing"
        if score_diff >= 6:
            return "blowout_winning"
        if inning <= 5:
            return "early_relief"
        return "middle"

    def _SelectByRole(self, game):
        """Select relief pitcher based on game situation and role priority."""
        situation = self._ClassifyGameSituation(game)
        role_order = SITUATION_ROLE_ORDER.get(situation, SITUATION_ROLE_ORDER["middle"])
        priority = self.strategy.teamstrategy.bullpenpriority

        for role in role_order:
            candidates = [rp for rp in self.reliefpitchers
                          if getattr(rp, 'bullpen_role', 'middle') == role]
            if not candidates:
                continue

            if priority == "matchup":
                ranked = self._RankByMatchup(candidates, game)
            elif priority == "rest":
                ranked = sorted(candidates, key=lambda x: getattr(x, 'bullpen_slot', 99))
            else:  # "best_available"
                ranked = sorted(candidates, key=lambda x: x.rp_rating, reverse=True)

            return ranked[0]

        return None

    def _RankByMatchup(self, candidates, game):
        """Rank relief pitcher candidates by handedness matchup advantage."""
        batter_hand = game.battingteam.currentbatter.handedness[0]

        def matchup_score(rp):
            score = rp.rp_rating
            pitcher_hand = rp.handedness[1]
            if batter_hand == 'S':
                score += 5
            elif batter_hand == pitcher_hand:
                score += 10  # Same-side = pitcher advantage
            return score

        return sorted(candidates, key=matchup_score, reverse=True)

    def _SwapPitcher(self, newpitcher, game):
        replaced = self.currentpitcher
        self.reliefpitchers.remove(newpitcher)
        self.currentpitcher = newpitcher
        self._pitching_appearance_seq += 1
        newpitcher.pitch_appearance_order = self._pitching_appearance_seq
        newpitcher.pitchingstats.Adder("appearances", 1)

        # In no-DH games, new pitcher inherits the replaced pitcher's batting spot
        if not self.use_dh:
            newpitcher.battingorder = replaced.battingorder
            newpitcher.lineup = replaced.lineup
            for idx, player in enumerate(self.battinglist):
                if player.id == replaced.id:
                    self.battinglist[idx] = newpitcher
                    break

        # Entry-state tracking for save/hold/blown-save determination
        score_diff = self.score - game.battingteam.score
        runners_on = sum(1 for r in [game.on_firstbase, game.on_secondbase, game.on_thirdbase] if r is not None)
        newpitcher.pitchingstats.Adder("inherited_runners", runners_on)

        game.substitutions.append({
            "team": self.name,
            "inning": game.currentinning,
            "half": "top" if game.topofinning else "bottom",
            "player_in_id": newpitcher.id,
            "player_in_name": newpitcher.name,
            "new_position": "P",
            "player_out_id": replaced.id,
            "player_out_name": replaced.name,
            "batting_order": newpitcher.battingorder if not self.use_dh else None,
            "type": "pitching_change",
            "entry_score_diff": score_diff,
            "entry_runners_on": runners_on,
            "entry_inning": game.currentinning,
            "entry_outs": game.currentouts,
            "entry_is_save_situation": self._is_entry_save_situation(score_diff, runners_on)
        })

    def _UseEmergencyPitcher(self, game):
        ep_id = self.strategy.teamstrategy.emergencypitcher

        # Try designated emergency pitcher first
        if ep_id is not None:
            for i, bp in enumerate(self.benchplayers):
                if bp.id == ep_id:
                    self._ActivateEmergencyPitcher(bp, i, game)
                    return

        # Fallback: bench player with highest pendurance
        if self.benchplayers:
            best_idx = max(range(len(self.benchplayers)),
                           key=lambda i: getattr(self.benchplayers[i], 'pendurance', 0))
            self._ActivateEmergencyPitcher(self.benchplayers[best_idx], best_idx, game)
            return

    def _ActivateEmergencyPitcher(self, player, index, game):
        replaced = self.currentpitcher
        emergency = self.benchplayers.pop(index)
        self.currentpitcher = emergency
        self._pitching_appearance_seq += 1
        emergency.pitch_appearance_order = self._pitching_appearance_seq
        emergency.pitchingstats.Adder("appearances", 1)

        # In no-DH games, new pitcher inherits the replaced pitcher's batting spot
        if not self.use_dh:
            emergency.battingorder = replaced.battingorder
            emergency.lineup = replaced.lineup
            for idx, p in enumerate(self.battinglist):
                if p.id == replaced.id:
                    self.battinglist[idx] = emergency
                    break

        # Entry-state tracking for save/hold/blown-save determination
        score_diff = self.score - game.battingteam.score
        runners_on = sum(1 for r in [game.on_firstbase, game.on_secondbase, game.on_thirdbase] if r is not None)
        emergency.pitchingstats.Adder("inherited_runners", runners_on)

        game.substitutions.append({
            "team": self.name,
            "inning": game.currentinning,
            "half": "top" if game.topofinning else "bottom",
            "player_in_id": emergency.id,
            "player_in_name": emergency.name,
            "new_position": "P",
            "player_out_id": replaced.id,
            "player_out_name": replaced.name,
            "batting_order": emergency.battingorder if not self.use_dh else None,
            "type": "emergency_pitcher",
            "entry_score_diff": score_diff,
            "entry_runners_on": runners_on,
            "entry_inning": game.currentinning,
            "entry_outs": game.currentouts,
            "entry_is_save_situation": self._is_entry_save_situation(score_diff, runners_on)
        })


def find_index(objectlist, attribute, targetvalue):
    for index, obj in enumerate(objectlist):
        if getattr(obj, attribute) == targetvalue:
            return index
    return -1