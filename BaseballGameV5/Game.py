from ast import Pass, literal_eval
import Team
import Rules
import Action
import Baselines
import json
import csv
import random
import numpy as np
import Stats as stats
import pandas as pd

# Import adapters
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapter import PlayerAdapter, BaselineAdapter, RulesAdapter, InjuryAdapter


class Game():
    def __init__(self, gamedict):
        self.gname = gamedict.get("gameid")
        self.baselines = Baselines.Baselines(gamedict.get("Rules"))
        self.hometeam = Team.Team(gamedict.get("Home"), "Home", gamedict.get("Rotation"), self.baselines)
        self.awayteam = Team.Team(gamedict.get("Away"), "Away", gamedict.get("Rotation"), self.baselines)
        self.rules = Rules.Rules(gamedict.get("Rules"))
        self.currentinning = 1
        self.currentouts = 0
        self.currentballs = 0
        self.currentstrikes = 0
        self.outcount = 0
        self.on_firstbase = None
        self.on_secondbase = None
        self.on_thirdbase = None
        self.current_runners_home = []
        self.is_walk = False
        self.is_strikeout = False
        self.is_pickoff = False
        self.is_stealattempt = False
        self.is_stealsuccess = False
        self.is_inplay = False
        self.is_hit = False #temp
        self.is_hbp = False
        self.error_count = 0
        self.is_single = False
        self.is_double = False
        self.is_triple = False
        self.is_homerun = False
        self.is_liveball = False
        self.ab_over = False
        self.topofinning = True
        self.gamedone = False
        self.battingteam = self.awayteam
        self.pitchingteam = self.hometeam
        self.batted_ball = None
        self.air_or_ground = None
        self.targeted_defender = None
        self.skip_bool = None
        self.actions = []
        self.overallresults = []
        self.meta = Game.GameResult(self.gname, self.hometeam, self.awayteam, self.actions)

    @classmethod
    def from_endpoint(cls, payload: dict, rules: dict, level_config: dict,
                      game_constants: dict, injury_types: list = None):
        """
        Create a Game instance from endpoint payload.

        Args:
            payload: Single game payload from endpoint (game_id, teams, ballpark, etc.)
            rules: Rules dict for this game's level (from top-level rules by league_level_id)
            level_config: Level-specific config (batting, contact_odds, etc.)
            game_constants: Shared game constants (defensive_alignment, etc.)
            injury_types: List of injury type definitions (optional)

        Returns:
            Game instance ready to run
        """
        # Seed random for deterministic simulation
        # Both Python's random and numpy's random must be seeded for full determinism
        random_seed = payload.get("random_seed")
        if random_seed:
            seed_int = int(random_seed)
            random.seed(seed_int)
            # numpy requires seed between 0 and 2^32-1, so use modulo for large seeds
            np.random.seed(seed_int % (2**32))

        # Create instance without calling __init__
        instance = object.__new__(cls)

        # Game identification
        instance.gname = payload.get("game_id", 0)

        # Adapt baselines from level_config and game_constants
        baseline_data = BaselineAdapter.adapt(level_config, game_constants)
        instance.baselines = Baselines.Baselines.from_dict(baseline_data)

        # Adapt rules (now passed in from top-level, not from payload)
        rules_data = RulesAdapter.adapt(rules)
        instance.rules = Rules.Rules.from_dict(rules_data)
        use_dh = instance.rules.dh

        # Get ballpark modifiers
        ballpark = payload.get("ballpark", {})
        instance.power_mod = ballpark.get("power_mod", 1.0)
        instance.pitch_break_mod = ballpark.get("pitch_break_mod", 1.0)

        # Adapt away team
        away_side = payload.get("away_side", {})
        away_name = away_side.get("team_abbrev", "AWAY")
        away_full_name = away_side.get("team_full_name", away_name)
        away_players = PlayerAdapter.adapt_team(away_side, away_name, away_full_name)

        # Apply ballpark modifiers to away players
        PlayerAdapter.apply_ballpark_modifiers(
            away_players, instance.power_mod, instance.pitch_break_mod
        )

        # Adapt home team
        home_side = payload.get("home_side", {})
        home_name = home_side.get("team_abbrev", "HOME")
        home_full_name = home_side.get("team_full_name", home_name)
        home_players = PlayerAdapter.adapt_team(home_side, home_name, home_full_name)

        # Apply ballpark modifiers to home players
        PlayerAdapter.apply_ballpark_modifiers(
            home_players, instance.power_mod, instance.pitch_break_mod
        )

        # Apply pregame injuries
        instance.pregame_injury_reports = []
        if injury_types:
            away_injuries = away_side.get("pregame_injuries", [])
            home_injuries = home_side.get("pregame_injuries", [])

            away_reports = InjuryAdapter.apply_pregame_injuries(away_players, away_injuries)
            home_reports = InjuryAdapter.apply_pregame_injuries(home_players, home_injuries)

            instance.pregame_injury_reports = away_reports + home_reports

        # Create teams from adapted players
        instance.awayteam = Team.Team.from_players(
            away_name, away_players, instance.baselines, use_dh, "away"
        )
        instance.hometeam = Team.Team.from_players(
            home_name, home_players, instance.baselines, use_dh, "home"
        )

        # Initialize game state
        instance.currentinning = 1
        instance.currentouts = 0
        instance.currentballs = 0
        instance.currentstrikes = 0
        instance.outcount = 0
        instance.on_firstbase = None
        instance.on_secondbase = None
        instance.on_thirdbase = None
        instance.current_runners_home = []
        instance.is_walk = False
        instance.is_strikeout = False
        instance.is_pickoff = False
        instance.is_stealattempt = False
        instance.is_stealsuccess = False
        instance.is_inplay = False
        instance.is_hit = False
        instance.is_hbp = False
        instance.error_count = 0
        instance.is_single = False
        instance.is_double = False
        instance.is_triple = False
        instance.is_homerun = False
        instance.is_liveball = False
        instance.ab_over = False
        instance.topofinning = True
        instance.gamedone = False
        instance.battingteam = instance.awayteam
        instance.pitchingteam = instance.hometeam
        instance.batted_ball = None
        instance.air_or_ground = None
        instance.targeted_defender = None
        instance.skip_bool = None
        instance.actions = []
        instance.overallresults = []
        instance.ingame_injury_reports = []

        # Store injury adapter for in-game injury checks
        if injury_types:
            instance.injury_adapter = InjuryAdapter(injury_types)
        else:
            instance.injury_adapter = None

        instance.meta = Game.GameResult(
            instance.gname, instance.hometeam, instance.awayteam, instance.actions
        )

        return instance

    def run_simulation(self):
        """
        Run the game simulation and return results.

        Returns:
            Dict with game results, boxscore, play-by-play, injuries, tuning data
        """
        # Run the game
        while self.gamedone == False:
            x = Action.Action(self)
        Action.Action.counter = 0

        # Build results
        return {
            "game_id": self.gname,
            "result": {
                "home_team": self.hometeam.name,
                "home_score": self.hometeam.score,
                "away_team": self.awayteam.name,
                "away_score": self.awayteam.score,
                "winning_team": self.hometeam.name if self.hometeam.score > self.awayteam.score else self.awayteam.name
            },
            "game_summary": self._build_game_summary(),
            "boxscore": self.ReturnBox(),
            "play_by_play": self.actions,
            "injuries": self.pregame_injury_reports + getattr(self, 'ingame_injury_reports', []),
            "tuning_data": self._build_tuning_data(),
            "debug": self._build_debug_data()
        }

    def _build_tuning_data(self):
        """Build tuning data for analysis and debugging."""
        return {
            "lineup_stats": {
                "away": self._get_lineup_stats(self.awayteam),
                "home": self._get_lineup_stats(self.hometeam)
            },
            "starting_pitcher_stats": {
                "away": self._get_pitcher_stats(self.awayteam),
                "home": self._get_pitcher_stats(self.hometeam)
            },
            "contact_distribution": self._get_contact_distribution(),
            "baserunning_analysis": self._get_baserunning_analysis()
        }

    def _build_game_summary(self):
        """Build game summary with pitching decisions, team totals, and game info."""
        return {
            "pitching_decisions": self._get_pitching_decisions(),
            "team_totals": self._get_team_totals(),
            "game_info": self._get_game_info()
        }

    def _get_pitching_decisions(self):
        """
        Determine W/L/S/BS for pitchers.

        Rules:
        - Winning pitcher: pitcher of record when team takes the final lead
        - Losing pitcher: pitcher who gave up the run that put opponent ahead for good
        - Save: reliever finishes game with lead, wasn't winning pitcher, and:
          - Entered with lead of 3 or less, OR
          - Entered with tying run on base/at bat/on deck, OR
          - Pitched at least 3 innings
        - Blown save: pitcher in save situation who allowed tying/go-ahead run
        """
        # Track score changes and pitcher of record through the game
        home_score = 0
        away_score = 0
        home_pitcher_of_record = None  # Pitcher credited if home wins
        away_pitcher_of_record = None  # Pitcher credited if away wins
        home_losing_pitcher = None     # Pitcher blamed if home loses
        away_losing_pitcher = None     # Pitcher blamed if away loses

        # Track current pitchers (from play-by-play)
        current_home_pitcher = None
        current_away_pitcher = None

        # Save situation tracking
        save_candidate = None
        save_situation_entered = False
        blown_saves = []

        for action in self.actions:
            # Track current pitcher
            pitcher_info = action.get("Pitcher")
            inning_half = action.get("Inning Half")

            if pitcher_info:
                pitcher_id = pitcher_info.get("player_id")
                if inning_half == "Top":
                    # Top of inning = away batting, home pitching
                    current_home_pitcher = pitcher_info
                else:
                    # Bottom of inning = home batting, away pitching
                    current_away_pitcher = pitcher_info

            # Get runs scored this action
            runners_scored = action.get("Runners_Scored", 0)
            if runners_scored > 0:
                prev_home = home_score
                prev_away = away_score

                if inning_half == "Top":
                    away_score += runners_scored
                else:
                    home_score += runners_scored

                # Check if lead changed
                prev_lead = prev_home - prev_away  # Positive = home leads
                new_lead = home_score - away_score

                # Determine if a team took the lead
                if prev_lead <= 0 and new_lead > 0:
                    # Home took the lead
                    home_pitcher_of_record = current_home_pitcher
                    # The away pitcher who gave up the lead is the losing pitcher candidate
                    away_losing_pitcher = current_away_pitcher
                elif prev_lead >= 0 and new_lead < 0:
                    # Away took the lead
                    away_pitcher_of_record = current_away_pitcher
                    # The home pitcher who gave up the lead is the losing pitcher candidate
                    home_losing_pitcher = current_home_pitcher
                elif prev_lead == 0 and new_lead == 0:
                    # Still tied - no change
                    pass

        # Final score
        final_home = self.hometeam.score
        final_away = self.awayteam.score

        # Determine winning and losing pitchers
        winning_pitcher = None
        losing_pitcher = None

        if final_home > final_away:
            winning_pitcher = home_pitcher_of_record
            losing_pitcher = away_losing_pitcher
        elif final_away > final_home:
            winning_pitcher = away_pitcher_of_record
            losing_pitcher = home_losing_pitcher

        # Determine save (simplified: last pitcher on winning team who isn't winning pitcher)
        save_pitcher = None
        if final_home != final_away:
            winning_team = self.hometeam if final_home > final_away else self.awayteam
            # Get the last pitcher used by winning team
            last_winning_pitcher = None
            for action in reversed(self.actions):
                pitcher_info = action.get("Pitcher")
                if pitcher_info:
                    inning_half = action.get("Inning Half")
                    is_winning_team_pitching = (
                        (inning_half == "Top" and final_home > final_away) or
                        (inning_half == "Bottom" and final_away > final_home)
                    )
                    if is_winning_team_pitching:
                        last_winning_pitcher = pitcher_info
                        break

            # Check if save situation (different pitcher than winning pitcher, closed out game)
            if (last_winning_pitcher and winning_pitcher and
                last_winning_pitcher.get("player_id") != winning_pitcher.get("player_id")):
                lead_margin = abs(final_home - final_away)
                # Simple save: finished game with lead of 3 or less
                if lead_margin <= 3:
                    save_pitcher = last_winning_pitcher

        return {
            "winning_pitcher": winning_pitcher,
            "losing_pitcher": losing_pitcher,
            "save": save_pitcher,
            "blown_saves": blown_saves  # Future enhancement
        }

    def _get_team_totals(self):
        """Aggregate team batting/pitching totals."""
        def get_team_batting_totals(team):
            totals = {
                "at_bats": 0,
                "runs": 0,
                "hits": 0,
                "doubles": 0,
                "triples": 0,
                "homeruns": 0,
                "rbi": 0,  # Would need RBI tracking
                "walks": 0,
                "strikeouts": 0,
                "stolen_bases": 0,
                "caught_stealing": 0,
                "left_on_base": 0,
                "errors": 0
            }

            for player in team.roster.playerlist:
                bs = player.battingstats
                totals["at_bats"] += bs.at_bats
                totals["runs"] += bs.runs
                totals["hits"] += bs.singles + bs.doubles + bs.triples + bs.homeruns
                totals["doubles"] += bs.doubles
                totals["triples"] += bs.triples
                totals["homeruns"] += bs.homeruns
                totals["walks"] += bs.walks
                totals["strikeouts"] += bs.strikeouts
                totals["stolen_bases"] += bs.stolen_bases
                totals["caught_stealing"] += bs.caught_stealing

                # Count fielding errors
                fs = player.fieldingstats
                totals["errors"] += fs.throwing_errors + fs.catching_errors

            return totals

        def get_team_pitching_totals(team):
            totals = {
                "innings_pitched": 0.0,
                "hits_allowed": 0,
                "runs_allowed": 0,
                "earned_runs": 0,
                "walks": 0,
                "strikeouts": 0,
                "homeruns_allowed": 0,
                "pitches_thrown": 0
            }

            total_outs = 0
            for player in team.roster.playerlist:
                ps = player.pitchingstats
                if ps.pitches_thrown > 0:
                    total_outs += ps.outs_pitched
                    totals["hits_allowed"] += ps.singles + ps.doubles + ps.triples + ps.homeruns
                    totals["earned_runs"] += ps.earned_runs
                    totals["runs_allowed"] += ps.earned_runs + ps.unearned_runs
                    totals["walks"] += ps.walks
                    totals["strikeouts"] += ps.strikeouts
                    totals["homeruns_allowed"] += ps.homeruns
                    totals["pitches_thrown"] += ps.pitches_thrown

            totals["innings_pitched"] = stats.outs_to_innings(total_outs)
            return totals

        # Calculate LOB from play-by-play (runners stranded at end of innings)
        home_lob = 0
        away_lob = 0
        for action in self.actions:
            # End of half-inning: 3 outs
            if action.get("Out Count") == 3:
                runners_on = 0
                if action.get("On First"):
                    runners_on += 1
                if action.get("On Second"):
                    runners_on += 1
                if action.get("On Third"):
                    runners_on += 1

                if action.get("Inning Half") == "Top":
                    away_lob += runners_on
                else:
                    home_lob += runners_on

        home_batting = get_team_batting_totals(self.hometeam)
        away_batting = get_team_batting_totals(self.awayteam)
        home_batting["left_on_base"] = home_lob
        away_batting["left_on_base"] = away_lob

        return {
            "away": {
                "team_abbrev": self.awayteam.name,
                "batting": away_batting,
                "pitching": get_team_pitching_totals(self.awayteam)
            },
            "home": {
                "team_abbrev": self.hometeam.name,
                "batting": home_batting,
                "pitching": get_team_pitching_totals(self.hometeam)
            }
        }

    def _get_game_info(self):
        """Get game-level information."""
        # Determine if walkoff
        is_walkoff = False
        if self.hometeam.score > self.awayteam.score:
            # Home won - check if they scored the winning run in their last at-bat
            last_home_action = None
            for action in reversed(self.actions):
                if action.get("Inning Half") == "Bottom":
                    last_home_action = action
                    break
            if last_home_action and last_home_action.get("Runners_Scored", 0) > 0:
                is_walkoff = True

        # Count total pitches
        home_pitches = sum(p.pitchingstats.pitches_thrown for p in self.hometeam.roster.playerlist)
        away_pitches = sum(p.pitchingstats.pitches_thrown for p in self.awayteam.roster.playerlist)

        # Count total actions (plate appearances roughly)
        total_actions = len(self.actions)

        # Get final inning
        final_inning = self.currentinning

        return {
            "innings_played": final_inning,
            "is_walkoff": is_walkoff,
            "total_pitches": {
                "away": away_pitches,
                "home": home_pitches,
                "total": away_pitches + home_pitches
            },
            "total_actions": total_actions,
            "duration_estimate_minutes": None  # Could estimate from pitch count
        }

    def _get_lineup_stats(self, team):
        """Get batting stats for lineup players."""
        lineup_stats = []
        for player in team.battinglist:
            lineup_stats.append({
                "player_id": getattr(player, 'id', None),
                "player_name": f"{player.firstname} {player.lastname}",
                "batting_order": player.battingorder,
                "position": player.lineup,
                "contact": round(player.contact, 1),
                "power": round(player.power, 1),
                "eye": round(player.eye, 1),
                "discipline": round(player.discipline, 1)
            })
        # Calculate lineup averages
        if lineup_stats:
            avg_contact = sum(p["contact"] for p in lineup_stats) / len(lineup_stats)
            avg_power = sum(p["power"] for p in lineup_stats) / len(lineup_stats)
            avg_eye = sum(p["eye"] for p in lineup_stats) / len(lineup_stats)
            avg_discipline = sum(p["discipline"] for p in lineup_stats) / len(lineup_stats)
        else:
            avg_contact = avg_power = avg_eye = avg_discipline = 0

        return {
            "players": lineup_stats,
            "averages": {
                "contact": round(avg_contact, 1),
                "power": round(avg_power, 1),
                "eye": round(avg_eye, 1),
                "discipline": round(avg_discipline, 1)
            }
        }

    def _get_pitcher_stats(self, team):
        """Get stats for the starting pitcher and pitches used."""
        pitcher = team.currentpitcher
        pitches = []
        for i in range(1, 6):
            pitch = getattr(pitcher, f'pitch{i}', None)
            if pitch and pitch.ovr > 0:
                pitches.append({
                    "pitch_name": pitch.name,
                    "pitch_ovr": round(pitch.ovr, 1)
                })

        # Calculate weighted average OVR (weighted by usage order)
        if pitches:
            weights = [5, 4, 3, 2, 1][:len(pitches)]
            weighted_sum = sum(p["pitch_ovr"] * w for p, w in zip(pitches, weights))
            total_weight = sum(weights)
            weighted_avg = weighted_sum / total_weight
        else:
            weighted_avg = 0

        return {
            "player_id": getattr(pitcher, 'id', None),
            "player_name": f"{pitcher.firstname} {pitcher.lastname}",
            "pitches": pitches,
            "weighted_pitch_ovr": round(weighted_avg, 1)
        }

    def _get_contact_distribution(self):
        """Calculate contact type distribution from play-by-play."""
        contact_types = ["barrel", "solid", "flare", "burner", "under", "topped", "weak"]
        counts = {ct: 0 for ct in contact_types}
        total = 0

        for action in self.actions:
            batted_ball = action.get("Batted Ball")
            if batted_ball and batted_ball != "None":
                if batted_ball in counts:
                    counts[batted_ball] += 1
                    total += 1

        # Calculate percentages
        distribution = {}
        for ct in contact_types:
            count = counts[ct]
            pct = round((count / total * 100), 1) if total > 0 else 0
            distribution[ct] = {"count": count, "pct": pct}

        distribution["total_batted_balls"] = total
        return distribution

    def _get_baserunning_analysis(self):
        """Analyze baserunning outcomes for tuning validation using Pre_R1/R2/R3 fields."""
        analysis = {
            # Sac fly tracking
            "sac_fly_opportunities": 0,  # R3 with <2 outs, fly ball out
            "sac_fly_scores": 0,

            # R2 on single tracking
            "r2_on_single_opportunities": 0,
            "r2_scores_on_single": 0,

            # R1 advancement tracking
            "r1_on_single_opportunities": 0,
            "r1_to_third_on_single": 0,

            # R1 on double tracking
            "r1_on_double_opportunities": 0,
            "r1_scores_on_double": 0,

            # Tag-up tracking
            "tag_up_attempts": 0,
            "tag_up_successes": 0,

            # Overall
            "total_runs_scored": 0,
            "runs_on_hits": 0,
            "runs_on_sac_flies": 0,

            # Double play / Triple play tracking
            "dp_opportunities": 0,  # R1 with <2 outs, ground ball
            "dp_completed": 0,      # 2+ outs on DP opportunity
            "tp_opportunities": 0,  # R1+R2 with 0 outs, ground ball
            "tp_completed": 0,      # 3 outs on TP opportunity
        }

        for action in self.actions:
            # Track runs scored
            runners_scored = action.get("Runners_Scored", 0)
            if runners_scored:
                analysis["total_runs_scored"] += runners_scored

            # Get pre-play state (captured at start of action)
            pre_r1 = action.get("Pre_R1")
            pre_r2 = action.get("Pre_R2")
            pre_r3 = action.get("Pre_R3")
            pre_outs = action.get("Pre_Outs", 0)

            # Get post-play state
            on_third = action.get("On Third")
            outcome = action.get("Defensive Outcome")
            air_or_ground = action.get("Air or Ground")
            runners_scored_ids = action.get("Runners_Scored_IDs", [])

            # Helper to check if a player scored
            def player_scored(pre_player):
                if not pre_player:
                    return False
                player_id = pre_player.get("player_id")
                return player_id in runners_scored_ids

            # Helper to check if a player is on a specific base
            def player_on_base(pre_player, base_obj):
                if not pre_player or not base_obj:
                    return False
                return pre_player.get("player_id") == base_obj.get("player_id")

            # Sac fly opportunity: R3 with <2 outs, OUTFIELD fly ball out
            # Only count outfield depths as true sac fly opportunities
            hit_depth = action.get("Hit Depth", "")
            outfield_depths = ["deep_of", "middle_of", "shallow_of"]
            if pre_r3 and pre_outs < 2 and air_or_ground == "air" and outcome == "out" and hit_depth in outfield_depths:
                analysis["sac_fly_opportunities"] += 1
                if player_scored(pre_r3):
                    analysis["sac_fly_scores"] += 1
                    analysis["runs_on_sac_flies"] += 1

            # R2 on single
            if pre_r2 and outcome == "single":
                analysis["r2_on_single_opportunities"] += 1
                if player_scored(pre_r2):
                    analysis["r2_scores_on_single"] += 1

            # R1 on single
            if pre_r1 and outcome == "single":
                analysis["r1_on_single_opportunities"] += 1
                if player_on_base(pre_r1, on_third):
                    analysis["r1_to_third_on_single"] += 1

            # R1 on double
            if pre_r1 and outcome == "double":
                analysis["r1_on_double_opportunities"] += 1
                if player_scored(pre_r1):
                    analysis["r1_scores_on_double"] += 1

            # Track tag-up events from defensive actions
            defensive_actions = str(action.get("Defensive Actions", ""))
            if "tags to" in defensive_actions:
                analysis["tag_up_attempts"] += 1
                analysis["tag_up_successes"] += 1

            # Track DP/TP opportunities and completions
            # Use the pre-computed fields from ActionPrint
            if action.get("Is_DP_Opportunity"):
                analysis["dp_opportunities"] += 1
                if action.get("Is_DP"):
                    analysis["dp_completed"] += 1

            if action.get("Is_TP_Opportunity"):
                analysis["tp_opportunities"] += 1
                if action.get("Is_TP"):
                    analysis["tp_completed"] += 1

        # Calculate rates
        def safe_rate(num, denom):
            return round(num / denom * 100, 1) if denom > 0 else 0.0

        analysis["rates"] = {
            "sac_fly_rate": safe_rate(analysis["sac_fly_scores"], analysis["sac_fly_opportunities"]),
            "r2_scores_on_single_rate": safe_rate(analysis["r2_scores_on_single"], analysis["r2_on_single_opportunities"]),
            "r1_to_third_on_single_rate": safe_rate(analysis["r1_to_third_on_single"], analysis["r1_on_single_opportunities"]),
            "r1_scores_on_double_rate": safe_rate(analysis["r1_scores_on_double"], analysis["r1_on_double_opportunities"]),
            "dp_rate": safe_rate(analysis["dp_completed"], analysis["dp_opportunities"]),
            "tp_rate": safe_rate(analysis["tp_completed"], analysis["tp_opportunities"]),
        }

        return analysis

    def _build_debug_data(self):
        """
        Build comprehensive debug data for analysis and troubleshooting.

        Includes:
        - Full player attributes for all players who participated
        - Config baselines used for this game
        - Advantage distribution statistics
        - Per-player outcome summaries
        - Defensive performance data
        - Detailed breakdowns by situation
        """
        return {
            # Player data
            "players_participated": self._get_players_participated(),
            "defense_data": self._get_defense_data(),

            # Config
            "config_baselines": self._get_config_baselines(),

            # Advantage analysis
            "advantage_summary": self._get_advantage_summary(),
            "pitcher_matchup_data": self._get_pitcher_matchup_data(),

            # Detailed breakdowns
            "tier_distribution_by_player": self._get_tier_distribution_by_player(),
            "swing_decision_rates": self._get_swing_decision_rates(),
            "whiff_rates_by_advantage": self._get_whiff_rates_by_advantage(),
            "barrel_rates_by_power_advantage": self._get_barrel_rates_by_power_advantage(),
            "count_situation_data": self._get_count_situation_data(),
            "handedness_matchup_breakdown": self._get_handedness_matchup_breakdown(),

            # Samples
            "interaction_samples": self._get_interaction_samples()
        }

    def _get_players_participated(self):
        """Get full attributes for all players who participated in the game."""
        players = {
            "away_batters": [],
            "away_pitchers": [],
            "home_batters": [],
            "home_pitchers": []
        }

        for team, prefix in [(self.awayteam, "away"), (self.hometeam, "home")]:
            for player in team.roster.playerlist:
                # Check if batter participated (had plate appearances)
                if player.battingstats.plate_appearances > 0:
                    players[f"{prefix}_batters"].append(self._get_batter_debug_info(player))

                # Check if pitcher participated (threw pitches)
                if player.pitchingstats.pitches_thrown > 0:
                    players[f"{prefix}_pitchers"].append(self._get_pitcher_debug_info(player))

        return players

    def _get_batter_debug_info(self, player):
        """Get full batting-relevant attributes for a player."""
        bs = player.battingstats
        return {
            "player_id": player.id,
            "name": f"{player.firstname} {player.lastname}",
            "position": player.lineup,
            "batting_order": player.battingorder,
            "handedness": player.handedness,
            # Core batting attributes
            "attributes": {
                "contact": round(player.contact, 1),
                "power": round(player.power, 1),
                "eye": round(player.eye, 1),
                "discipline": round(player.discipline, 1),
                # Original values (before any modifiers)
                "og_contact": round(player.og_contact, 1),
                "og_power": round(player.og_power, 1),
                "og_eye": round(player.og_eye, 1),
                "og_discipline": round(player.og_discipline, 1),
            },
            # Baserunning attributes
            "baserunning": {
                "speed": round(player.speed, 1),
                "baserunning": round(player.baserunning, 1),
                "basereaction": round(player.basereaction, 1),
            },
            # Spray chart
            "spray_chart": {
                "left": round(player.left_split, 3),
                "center": round(player.center_split, 3),
                "right": round(player.right_split, 3),
            },
            # Game stats
            "game_stats": {
                "pa": bs.plate_appearances,
                "ab": bs.at_bats,
                "hits": bs.singles + bs.doubles + bs.triples + bs.homeruns,
                "singles": bs.singles,
                "doubles": bs.doubles,
                "triples": bs.triples,
                "homeruns": bs.homeruns,
                "walks": bs.walks,
                "strikeouts": bs.strikeouts,
                "hbp": bs.hbp,
            }
        }

    def _get_pitcher_debug_info(self, player):
        """Get full pitching-relevant attributes for a player."""
        ps = player.pitchingstats

        # Build pitch arsenal
        pitches = []
        for i in range(1, 6):
            pitch = getattr(player, f'pitch{i}', None)
            if pitch and pitch.ovr > 0:
                pitches.append({
                    "name": pitch.name,
                    "ovr": round(pitch.ovr, 1),
                    "pacc": round(pitch.pacc, 1),
                    "pcntrl": round(pitch.pcntrl, 1),
                    "pbrk": round(pitch.pbrk, 1),
                    "consist": round(pitch.consist, 1),
                })

        return {
            "player_id": player.id,
            "name": f"{player.firstname} {player.lastname}",
            "handedness": player.handedness,
            # Core pitching attributes
            "attributes": {
                "pgencontrol": round(player.pgencontrol, 1),
                "pthrowpower": round(player.pthrowpower, 1),
                "pendurance": round(player.pendurance, 1),
                "psequencing": round(player.psequencing, 1),
                "pickoff": round(player.pickoff, 1),
            },
            # Pitch arsenal
            "pitches": pitches,
            # Game stats
            "game_stats": {
                "pitches_thrown": ps.pitches_thrown,
                "outs_pitched": ps.outs_pitched,
                "innings": round(ps.outs_pitched / 3, 1),
                "hits_allowed": ps.singles + ps.doubles + ps.triples + ps.homeruns,
                "walks": ps.walks,
                "strikeouts": ps.strikeouts,
                "homeruns": ps.homeruns,
                "earned_runs": ps.earned_runs,
            }
        }

    def _get_config_baselines(self):
        """Get the config baselines used for this game."""
        bl = self.baselines
        return {
            "batted_ball_odds": {
                "barrel": bl.barrelodds,
                "solid": bl.solidodds,
                "flare": bl.flareodds,
                "burner": bl.burnerodds,
                "topped": bl.toppedodds,
                "under": bl.underodds,
                "weak": bl.weakodds,
            },
            "swing_rates": {
                "inside_swing": bl.insideswing,
                "outside_swing": bl.outsideswing,
            },
            "contact_rates": {
                "inside_contact": bl.insidecontact,
                "outside_contact": bl.outsidecontact,
            },
            "ballpark_modifiers": {
                "power_mod": getattr(self, 'power_mod', 1.0),
                "pitch_break_mod": getattr(self, 'pitch_break_mod', 1.0),
            }
        }

    def _get_advantage_summary(self):
        """
        Summarize matchup advantages from play-by-play.
        Extracts advantage data logged in actions.
        """
        advantages = {
            "contact": [],
            "power": [],
            "eye": [],
            "discipline": []
        }

        for action in self.actions:
            # Check if interaction data exists
            interaction = action.get("Interaction_Data", {})
            if interaction:
                for key in advantages.keys():
                    adv_key = f"adv_{key}"
                    if adv_key in interaction and interaction[adv_key] is not None:
                        advantages[key].append(interaction[adv_key])

        # Calculate statistics
        def calc_stats(values):
            if not values:
                return {"count": 0, "min": None, "max": None, "avg": None}
            return {
                "count": len(values),
                "min": round(min(values), 3),
                "max": round(max(values), 3),
                "avg": round(sum(values) / len(values), 3)
            }

        return {
            "contact_advantage": calc_stats(advantages["contact"]),
            "power_advantage": calc_stats(advantages["power"]),
            "eye_advantage": calc_stats(advantages["eye"]),
            "discipline_advantage": calc_stats(advantages["discipline"]),
        }

    def _get_pitcher_matchup_data(self):
        """Get pitcher attribute averages for matchup analysis."""
        def get_pitcher_avgs(team):
            pitchers = [p for p in team.roster.playerlist if p.pitchingstats.pitches_thrown > 0]
            if not pitchers:
                return None

            # Weighted by pitches thrown
            total_pitches = sum(p.pitchingstats.pitches_thrown for p in pitchers)
            if total_pitches == 0:
                return None

            weighted_pgencontrol = sum(p.pgencontrol * p.pitchingstats.pitches_thrown for p in pitchers) / total_pitches

            # Average pitch attributes (weighted by pitches thrown)
            weighted_pacc = 0
            weighted_pcntrl = 0
            weighted_pbrk = 0
            for p in pitchers:
                weight = p.pitchingstats.pitches_thrown / total_pitches
                # Use pitch1 as representative (most used)
                weighted_pacc += p.pitch1.pacc * weight
                weighted_pcntrl += p.pitch1.pcntrl * weight
                weighted_pbrk += p.pitch1.pbrk * weight

            return {
                "pgencontrol_weighted_avg": round(weighted_pgencontrol, 1),
                "pitch1_pacc_weighted_avg": round(weighted_pacc, 1),
                "pitch1_pcntrl_weighted_avg": round(weighted_pcntrl, 1),
                "pitch1_pbrk_weighted_avg": round(weighted_pbrk, 1),
            }

        return {
            "away_pitchers": get_pitcher_avgs(self.awayteam),
            "home_pitchers": get_pitcher_avgs(self.hometeam),
        }

    def _get_interaction_samples(self, max_samples=10):
        """
        Get sample interaction snapshots for debugging.
        Returns up to max_samples of batted ball events with full interaction data.
        """
        samples = []
        for action in self.actions:
            if action.get("Batted Ball") and action.get("Batted Ball") != "None":
                sample = {
                    "inning": action.get("Inning"),
                    "inning_half": action.get("Inning Half"),
                    "batter": action.get("Batter", {}).get("player_name"),
                    "pitcher": action.get("Pitcher", {}).get("player_name"),
                    "batted_ball": action.get("Batted Ball"),
                    "direction": action.get("Hit Direction"),
                    "depth": action.get("Hit Depth"),
                    "outcome": action.get("Defensive Outcome"),
                    "interaction_data": action.get("Interaction_Data"),
                    "modifier_data": action.get("Modifier_Data"),
                }
                samples.append(sample)
                if len(samples) >= max_samples:
                    break

        return samples

    def _get_defense_data(self):
        """Get defensive performance data for all fielders."""
        defense = {
            "away_fielders": [],
            "home_fielders": []
        }

        for team, prefix in [(self.awayteam, "away"), (self.hometeam, "home")]:
            for player in team.roster.playerlist:
                fs = player.fieldingstats
                # Only include players who had fielding opportunities
                total_chances = fs.putouts + fs.assists + fs.throwing_errors + fs.catching_errors
                if total_chances > 0:
                    defense[f"{prefix}_fielders"].append({
                        "player_id": player.id,
                        "name": f"{player.firstname} {player.lastname}",
                        "position": player.lineup,
                        "attributes": {
                            "throwpower": round(player.throwpower, 1),
                            "throwacc": round(player.throwacc, 1),
                            "fieldcatch": round(player.fieldcatch, 1),
                            "fieldreact": round(player.fieldreact, 1),
                            "fieldspot": round(player.fieldspot, 1),
                            "speed": round(player.speed, 1),
                        },
                        "game_stats": {
                            "putouts": fs.putouts,
                            "assists": fs.assists,
                            "throwing_errors": fs.throwing_errors,
                            "catching_errors": fs.catching_errors,
                            "total_chances": total_chances,
                            "fielding_pct": round((fs.putouts + fs.assists) / total_chances, 3) if total_chances > 0 else 1.0,
                        }
                    })

        # Add team-level defensive summary
        for prefix in ["away", "home"]:
            fielders = defense[f"{prefix}_fielders"]
            if fielders:
                total_putouts = sum(f["game_stats"]["putouts"] for f in fielders)
                total_assists = sum(f["game_stats"]["assists"] for f in fielders)
                total_errors = sum(f["game_stats"]["throwing_errors"] + f["game_stats"]["catching_errors"] for f in fielders)
                total_chances = total_putouts + total_assists + total_errors

                defense[f"{prefix}_team_summary"] = {
                    "total_putouts": total_putouts,
                    "total_assists": total_assists,
                    "total_errors": total_errors,
                    "team_fielding_pct": round((total_putouts + total_assists) / total_chances, 3) if total_chances > 0 else 1.0
                }

        return defense

    def _get_tier_distribution_by_player(self):
        """Track which tier each batter lands in most often."""
        player_tiers = {}

        for action in self.actions:
            batter = action.get("Batter", {})
            batter_id = batter.get("player_id")
            if not batter_id:
                continue

            modifier_data = action.get("Modifier_Data", {})
            if not modifier_data:
                continue

            tier = modifier_data.get("selected_tier")
            if not tier:
                continue

            if batter_id not in player_tiers:
                player_tiers[batter_id] = {
                    "player_name": batter.get("player_name"),
                    "quality": 0,
                    "neutral": 0,
                    "poor": 0,
                    "total": 0
                }

            player_tiers[batter_id][tier] += 1
            player_tiers[batter_id]["total"] += 1

        # Calculate percentages
        for player_id, data in player_tiers.items():
            total = data["total"]
            if total > 0:
                data["quality_pct"] = round(data["quality"] / total * 100, 1)
                data["neutral_pct"] = round(data["neutral"] / total * 100, 1)
                data["poor_pct"] = round(data["poor"] / total * 100, 1)

        return player_tiers

    def _get_swing_decision_rates(self):
        """Track swing rates on Inside (strikes) vs Outside (balls) by player."""
        player_swings = {}

        for action in self.actions:
            batter = action.get("Batter", {})
            batter_id = batter.get("player_id")
            if not batter_id:
                continue

            interaction = action.get("Interaction_Data", {})
            if not interaction:
                continue

            swing_decision = interaction.get("swing_decision")
            final_location = interaction.get("final_location")

            if swing_decision is None or final_location is None:
                continue

            if batter_id not in player_swings:
                player_swings[batter_id] = {
                    "player_name": batter.get("player_name"),
                    "inside_swings": 0,
                    "inside_takes": 0,
                    "outside_swings": 0,
                    "outside_takes": 0,
                }

            if final_location == "Inside":
                if swing_decision == "Swing":
                    player_swings[batter_id]["inside_swings"] += 1
                else:
                    player_swings[batter_id]["inside_takes"] += 1
            else:  # Outside
                if swing_decision == "Swing":
                    player_swings[batter_id]["outside_swings"] += 1
                else:
                    player_swings[batter_id]["outside_takes"] += 1

        # Calculate rates
        for player_id, data in player_swings.items():
            inside_total = data["inside_swings"] + data["inside_takes"]
            outside_total = data["outside_swings"] + data["outside_takes"]

            data["inside_swing_rate"] = round(data["inside_swings"] / inside_total * 100, 1) if inside_total > 0 else 0
            data["outside_swing_rate"] = round(data["outside_swings"] / outside_total * 100, 1) if outside_total > 0 else 0
            data["chase_rate"] = data["outside_swing_rate"]  # Alias for clarity

        return player_swings

    def _get_whiff_rates_by_advantage(self):
        """Track K% bucketed by eye advantage."""
        buckets = {
            "very_negative": {"range": "< -0.6", "swings": 0, "whiffs": 0, "contacts": 0},
            "negative": {"range": "-0.6 to -0.3", "swings": 0, "whiffs": 0, "contacts": 0},
            "slight_negative": {"range": "-0.3 to 0", "swings": 0, "whiffs": 0, "contacts": 0},
            "slight_positive": {"range": "0 to 0.3", "swings": 0, "whiffs": 0, "contacts": 0},
            "positive": {"range": "0.3 to 0.6", "swings": 0, "whiffs": 0, "contacts": 0},
            "very_positive": {"range": ">= 0.6", "swings": 0, "whiffs": 0, "contacts": 0},
        }

        for action in self.actions:
            interaction = action.get("Interaction_Data", {})
            if not interaction:
                continue

            eye_adv = interaction.get("adv_eye")
            swing_decision = interaction.get("swing_decision")
            contact_result = interaction.get("contact_result")

            if eye_adv is None or swing_decision != "Swing":
                continue

            # Determine bucket
            if eye_adv < -0.6:
                bucket = "very_negative"
            elif eye_adv < -0.3:
                bucket = "negative"
            elif eye_adv < 0:
                bucket = "slight_negative"
            elif eye_adv < 0.3:
                bucket = "slight_positive"
            elif eye_adv < 0.6:
                bucket = "positive"
            else:
                bucket = "very_positive"

            buckets[bucket]["swings"] += 1
            if contact_result == "Whiff":
                buckets[bucket]["whiffs"] += 1
            elif contact_result in ["Foul", "InPlay"]:
                buckets[bucket]["contacts"] += 1

        # Calculate rates
        for bucket, data in buckets.items():
            if data["swings"] > 0:
                data["whiff_rate"] = round(data["whiffs"] / data["swings"] * 100, 1)
                data["contact_rate"] = round(data["contacts"] / data["swings"] * 100, 1)
            else:
                data["whiff_rate"] = 0
                data["contact_rate"] = 0

        return buckets

    def _get_barrel_rates_by_power_advantage(self):
        """Track barrel% bucketed by power advantage."""
        buckets = {
            "very_negative": {"range": "< -0.6", "quality_hits": 0, "barrels": 0, "solids": 0},
            "negative": {"range": "-0.6 to -0.3", "quality_hits": 0, "barrels": 0, "solids": 0},
            "slight_negative": {"range": "-0.3 to 0", "quality_hits": 0, "barrels": 0, "solids": 0},
            "slight_positive": {"range": "0 to 0.3", "quality_hits": 0, "barrels": 0, "solids": 0},
            "positive": {"range": "0.3 to 0.6", "quality_hits": 0, "barrels": 0, "solids": 0},
            "very_positive": {"range": ">= 0.6", "quality_hits": 0, "barrels": 0, "solids": 0},
        }

        for action in self.actions:
            modifier_data = action.get("Modifier_Data", {})
            if not modifier_data:
                continue

            power_adv = modifier_data.get("power_advantage")
            selected_tier = modifier_data.get("selected_tier")
            batted_ball = action.get("Batted Ball")

            if power_adv is None or selected_tier != "quality":
                continue

            # Determine bucket
            if power_adv < -0.6:
                bucket = "very_negative"
            elif power_adv < -0.3:
                bucket = "negative"
            elif power_adv < 0:
                bucket = "slight_negative"
            elif power_adv < 0.3:
                bucket = "slight_positive"
            elif power_adv < 0.6:
                bucket = "positive"
            else:
                bucket = "very_positive"

            buckets[bucket]["quality_hits"] += 1
            if batted_ball == "barrel":
                buckets[bucket]["barrels"] += 1
            elif batted_ball == "solid":
                buckets[bucket]["solids"] += 1

        # Calculate rates
        for bucket, data in buckets.items():
            if data["quality_hits"] > 0:
                data["barrel_rate"] = round(data["barrels"] / data["quality_hits"] * 100, 1)
                data["solid_rate"] = round(data["solids"] / data["quality_hits"] * 100, 1)
            else:
                data["barrel_rate"] = 0
                data["solid_rate"] = 0

        return buckets

    def _get_count_situation_data(self):
        """Track outcomes by ball/strike count."""
        counts = {}

        for action in self.actions:
            # Use correct field names from ActionPrint
            balls = action.get("Ball Count", 0)
            strikes = action.get("Strike Count", 0)
            count_key = f"{balls}-{strikes}"

            defensive_outcome = action.get("Defensive Outcome")
            batted_ball = action.get("Batted Ball")

            if count_key not in counts:
                counts[count_key] = {
                    "total_pitches": 0,
                    "balls": 0,
                    "strikes_looking": 0,
                    "strikes_swinging": 0,
                    "fouls": 0,
                    "in_play": 0,
                    "hits": 0,
                    "outs": 0,
                    "walks": 0,
                    "strikeouts": 0,
                    "hbp": 0,
                }

            counts[count_key]["total_pitches"] += 1

            # Parse the Outcomes string to get result type and detail
            # Format: "['Strike', 'Looking', 'Fastball']" or "['Ball', 'Looking', 'Slider']"
            # or for batted balls: "['barrel', 'center left', 'Fastball']"
            outcomes_str = action.get("Outcomes", "")
            result_type = None
            result_detail = None

            if outcomes_str and outcomes_str != "None":
                try:
                    # Parse the string representation of the list
                    outcomes_list = literal_eval(outcomes_str)
                    if len(outcomes_list) >= 1:
                        result_type = outcomes_list[0]
                    if len(outcomes_list) >= 2:
                        result_detail = outcomes_list[1]
                except (ValueError, SyntaxError):
                    # Fallback: simple string parsing
                    pass

            # Use boolean flags as backup/verification
            is_foul = action.get("Is_Foul", False)
            is_hbp = action.get("Is_HBP", False)
            is_inplay = action.get("Is_InPlay", False)
            is_walk = action.get("Is_Walk", False)
            is_strikeout = action.get("Is_Strikeout", False)

            # Categorize pitch outcome
            if is_hbp or result_type == "HBP":
                counts[count_key]["hbp"] += 1
            elif result_type == "Ball":
                counts[count_key]["balls"] += 1
            elif result_type == "Strike":
                if result_detail == "Looking":
                    counts[count_key]["strikes_looking"] += 1
                elif result_detail == "Swinging":
                    counts[count_key]["strikes_swinging"] += 1
                elif result_detail == "Foul" or is_foul:
                    counts[count_key]["fouls"] += 1
            elif is_foul:
                # Foul ball (result_type might be contact type for batted foul)
                counts[count_key]["fouls"] += 1

            # Track balls in play
            if is_inplay or (batted_ball and batted_ball != "None" and not is_foul):
                counts[count_key]["in_play"] += 1
                if defensive_outcome in ["single", "double", "triple", "homerun"]:
                    counts[count_key]["hits"] += 1
                elif defensive_outcome == "out":
                    counts[count_key]["outs"] += 1

            # Track final PA outcomes at this count
            if action.get("AB_Over"):
                if is_walk:
                    counts[count_key]["walks"] += 1
                elif is_strikeout:
                    counts[count_key]["strikeouts"] += 1

        return counts

    def _get_handedness_matchup_breakdown(self):
        """Get per-matchup (LvL, LvR, RvL, RvR, SvL, SvR) advantage and outcome stats."""
        matchups = {}

        for action in self.actions:
            batter = action.get("Batter", {})
            pitcher = action.get("Pitcher", {})

            batter_hand = batter.get("handedness", "R")[0] if batter.get("handedness") else "R"
            pitcher_hand = pitcher.get("handedness", "R")[1] if pitcher.get("handedness") and len(pitcher.get("handedness", "")) > 1 else "R"

            matchup_key = f"{batter_hand}v{pitcher_hand}"

            if matchup_key not in matchups:
                matchups[matchup_key] = {
                    "plate_appearances": 0,
                    "at_bats": 0,
                    "hits": 0,
                    "walks": 0,
                    "strikeouts": 0,
                    "homeruns": 0,
                    "batted_balls": 0,
                    "quality_contact": 0,
                    "barrels": 0,
                    "advantages": {
                        "contact": [],
                        "power": [],
                        "eye": [],
                        "discipline": []
                    }
                }

            matchups[matchup_key]["plate_appearances"] += 1

            # Track advantages
            interaction = action.get("Interaction_Data", {})
            if interaction:
                for key in ["contact", "power", "eye", "discipline"]:
                    adv_key = f"adv_{key}"
                    if adv_key in interaction and interaction[adv_key] is not None:
                        matchups[matchup_key]["advantages"][key].append(interaction[adv_key])

            # Track outcomes
            outcome = action.get("Defensive Outcome")
            result_type = action.get("Result Type")
            batted_ball = action.get("Batted Ball")

            if outcome in ["single", "double", "triple", "homerun"]:
                matchups[matchup_key]["hits"] += 1
                matchups[matchup_key]["at_bats"] += 1
                if outcome == "homerun":
                    matchups[matchup_key]["homeruns"] += 1
            elif outcome == "out":
                matchups[matchup_key]["at_bats"] += 1
            elif result_type == "Ball" and action.get("Balls") == 4:
                matchups[matchup_key]["walks"] += 1
            elif result_type == "Strike" and action.get("Strikes") == 3:
                matchups[matchup_key]["strikeouts"] += 1

            if batted_ball and batted_ball != "None":
                matchups[matchup_key]["batted_balls"] += 1
                if batted_ball in ["barrel", "solid"]:
                    matchups[matchup_key]["quality_contact"] += 1
                if batted_ball == "barrel":
                    matchups[matchup_key]["barrels"] += 1

        # Calculate rates and averages
        for matchup_key, data in matchups.items():
            ab = data["at_bats"]
            bb = data["batted_balls"]

            data["avg"] = round(data["hits"] / ab, 3) if ab > 0 else 0
            data["k_rate"] = round(data["strikeouts"] / data["plate_appearances"] * 100, 1) if data["plate_appearances"] > 0 else 0
            data["bb_rate"] = round(data["walks"] / data["plate_appearances"] * 100, 1) if data["plate_appearances"] > 0 else 0
            data["quality_rate"] = round(data["quality_contact"] / bb * 100, 1) if bb > 0 else 0
            data["barrel_rate"] = round(data["barrels"] / bb * 100, 1) if bb > 0 else 0

            # Calculate advantage averages
            for key in ["contact", "power", "eye", "discipline"]:
                values = data["advantages"][key]
                if values:
                    data[f"avg_{key}_advantage"] = round(sum(values) / len(values), 3)
                else:
                    data[f"avg_{key}_advantage"] = None

            # Remove raw advantage lists to reduce output size
            del data["advantages"]

        return matchups

    def ReturnBox(self):
        test = stats.StatJSONConverter(self)
        return test 

    class GameResult():
        def __init__(self, gname, hometeam, awayteam, actions):
            self.id = gname
            self.hometeam = hometeam
            self.awayteam = awayteam
            self.actions = actions
        def to_dict(self):
            return {
                "id":self.id,
                "hometeam":self.hometeam.name,
                "hometeam score": self.hometeam.score,
                "awayteam":self.awayteam.name,
                "awayteam score": self.awayteam.score,
            }

    def __repr__(self):
        return f"{str(self.gname)} {str(self.hometeam)} {str(self.awayteam)} {str(self.rules)}"
    
    def RunGame(self):    
        while self.gamedone == False:
            x = Action.Action(self)
        Action.Action.counter = 0
        listofactions = []
        thing = stats.create_score_table(self.overallresults)        
        stats.FieldStatPullSave(self.hometeam, self.gname)
        stats.FieldStatPullSave(self.awayteam, self.gname)
        stats.BattingStatPullSave(self.hometeam, self.gname)
        stats.BattingStatPullSave(self.awayteam, self.gname)
        stats.PitchStatPullSave(self.hometeam, self.gname)
        stats.PitchStatPullSave(self.awayteam, self.gname)

        for player in self.hometeam.roster.playerlist:
            if player.pitchingstats.pitches_thrown > 0:
                pass

        for player in self.hometeam.roster.playerlist:
            if player.battingstats.plate_appearances> 0:
                pass

        for action in self.actions:
            listofactions.append(action)    
        export_dataframe = pd.DataFrame(listofactions)
        export_dataframe.replace({"None": ""}, inplace=True)
        export_dataframe.to_csv(f"{self.gname}.csv", na_rep="", index=False)

        actions_string = listofactions

        test = stats.StatJSONConverter(self)

        stats.SaveJSON(test, "full_json_test")
        
        with open(f"testoutput_{self.gname}.json", "w") as outfile:
            json.dump(actions_string, outfile)