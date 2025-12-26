from ast import Pass
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
            Dict with game results, boxscore, play-by-play, injuries
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
            "boxscore": self.ReturnBox(),
            "play_by_play": self.actions,
            "injuries": self.pregame_injury_reports + getattr(self, 'ingame_injury_reports', [])
        }

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