"""
Baseline Adapter - Transforms endpoint level_configs and game_constants to engine Baselines format.

The endpoint provides:
- level_configs: Per-level batting, contact_odds, distance_weights, fielding_weights, game settings
- game_constants: Shared defensive_alignment, fielding_difficulty, fielding_modifier, time_to_ground

This adapter converts these into the format expected by the Baselines class.
"""

from .direction_mapper import DirectionMapper


class BaselineAdapter:
    """Transforms endpoint baseline data to engine Baselines format."""

    # Order of distance outcomes for array conversion
    DIST_OUTCOMES = [
        "homerun", "deep_of", "middle_of", "shallow_of",
        "deep_if", "middle_if", "shallow_if", "mound", "catcher"
    ]

    # Order of fielding outcomes for array conversion (deprecated - kept for backwards compat)
    FIELDING_OUTCOMES = ["out", "single", "double", "triple"]

    # Field zone to spread key mapping
    FIELD_ZONE_TO_SPREAD = {
        "far_left": "leftline",
        "left": "left",
        "center_left": "centerleft",
        "dead_center": "center",
        "center_right": "centerright",
        "right": "right",
        "far_right": "rightline"
    }

    # Situation categories for catch rates
    # These are derived from depth + direction combinations
    CATCH_SITUATIONS = ["deep_gap", "gap", "deep_line", "line", "deep", "routine_of", "routine_if"]

    # Default catch rates per contact type per situation
    # These replace the hardcoded values in defense.py _is_out_play()
    DEFAULT_CATCH_RATES = {
        "barrel": {
            "deep_gap": 0.30,    # Deep gap - very hard to catch
            "gap": 0.50,         # Gap hit - hard to catch
            "deep_line": 0.45,   # Deep down the line
            "line": 0.50,        # Down the line
            "deep": 0.60,        # Deep fly (straight at fielder)
            "routine_of": 0.92,  # Routine outfield fly
            "routine_if": 0.97,  # Routine infield fly
        },
        "solid": {
            "deep_gap": 0.35,
            "gap": 0.55,
            "deep_line": 0.50,
            "line": 0.55,
            "deep": 0.65,
            "routine_of": 0.94,
            "routine_if": 0.98,
        },
        "flare": {
            "deep_gap": 0.45,
            "gap": 0.40,
            "deep_line": 0.55,
            "line": 0.50,
            "deep": 0.70,
            "routine_of": 0.85,
            "routine_if": 0.95,
        },
        "burner": {
            "deep_gap": 0.50,
            "gap": 0.55,
            "deep_line": 0.55,
            "line": 0.60,
            "deep": 0.75,
            "routine_of": 0.88,
            "routine_if": 0.92,
        },
        "under": {
            "deep_gap": 0.60,
            "gap": 0.70,
            "deep_line": 0.65,
            "line": 0.70,
            "deep": 0.80,
            "routine_of": 0.95,
            "routine_if": 0.98,
        },
        "topped": {
            "deep_gap": 0.80,
            "gap": 0.85,
            "deep_line": 0.80,
            "line": 0.85,
            "deep": 0.90,
            "routine_of": 0.95,
            "routine_if": 0.90,  # Ground balls, can beat throw
        },
        "weak": {
            "deep_gap": 0.85,
            "gap": 0.90,
            "deep_line": 0.85,
            "line": 0.90,
            "deep": 0.92,
            "routine_of": 0.97,
            "routine_if": 0.88,  # Weak dribblers, sometimes beat throw
        },
    }

    @classmethod
    def adapt(cls, level_config: dict, game_constants: dict) -> dict:
        """
        Convert endpoint level_config and game_constants to engine baseline format.

        Args:
            level_config: The level-specific config (batting, contact_odds, etc.)
            game_constants: Shared game constants (defensive_alignment, etc.)

        Returns:
            Dict ready for Baselines.from_dict()
        """
        batting = level_config.get("batting", {})
        contact_odds = level_config.get("contact_odds", {})
        game_settings = level_config.get("game", {})
        distance_weights = level_config.get("distance_weights", {})
        fielding_weights = level_config.get("fielding_weights", {})
        catch_rates = level_config.get("catch_rates", {})

        return {
            "baselines": cls._build_baselines(batting, contact_odds, game_settings),
            "spread": cls._build_spread(game_constants.get("field_zones", [])),
            "distweights": cls._convert_distweights(distance_weights),
            "distoutcomes": cls.DIST_OUTCOMES.copy(),
            # Deprecated - kept for backwards compatibility
            "fieldingweights": cls._convert_fieldingweights(fielding_weights),
            "fieldingoutcomes": cls.FIELDING_OUTCOMES.copy(),
            # New catch_rates system - replaces fieldingweights for outcome determination
            "catch_rates": cls._convert_catch_rates(catch_rates),
            "fieldingmod": cls._convert_fieldingmod(
                game_constants.get("fielding_modifier", {})
            ),
            "fieldingmultiplier": game_settings.get("fielding_multiplier", 0),
            "defensivealignment": DirectionMapper.convert_defensive_alignment(
                game_constants.get("defensive_alignment", {})
            ),
            "directlyat": cls._build_difficulty_array(
                game_constants.get("fielding_difficulty", {}), "directlyat"
            ),
            "onestepaway": cls._build_difficulty_array(
                game_constants.get("fielding_difficulty", {}), "onestepaway"
            ),
            "twostepaway": cls._build_difficulty_array(
                game_constants.get("fielding_difficulty", {}), "twostepaway"
            ),
            "threestepaway": cls._build_difficulty_array(
                game_constants.get("fielding_difficulty", {}), "threestepaway"
            ),
            "homerun": cls._build_difficulty_array(
                game_constants.get("fielding_difficulty", {}), "homerun"
            ),
            "timetoground": game_constants.get("time_to_ground", {}),
            "energytickcap": game_settings.get("energy_tick_cap", 1.5),
            "energystep": game_settings.get("energy_step", 2),
            "shortleash": game_settings.get("short_leash", 0.8),
            "normalleash": game_settings.get("normal_leash", 0.7),
            "longleash": game_settings.get("long_leash", 0.5),
        }

    @classmethod
    def _build_baselines(cls, batting: dict, contact_odds: dict,
                         game_settings: dict) -> dict:
        """Build the baselines dict from batting and contact_odds."""
        return {
            "OutsideSwing": batting.get("outside_swing", 0.3),
            "OutsideContact": batting.get("outside_contact", 0.66),
            "InsideSwing": batting.get("inside_swing", 0.65),
            "InsideContact": batting.get("inside_contact", 0.87),
            "c_barrelodds": contact_odds.get("barrel", 7),
            "c_solidodds": contact_odds.get("solid", 12),
            "c_flareodds": contact_odds.get("flare", 36),
            "c_burnerodds": contact_odds.get("burner", 39),
            "c_underodds": contact_odds.get("under", 2.4),
            "c_toppedodds": contact_odds.get("topped", 3.2),
            "c_weakodds": contact_odds.get("weak", 0.4),
            "modexp": batting.get("modexp", 2),
            "steal_success": game_settings.get("steal_success", 0.65),
            "pickoff_success": game_settings.get("pickoff_success", 0.1),
            "error_rate": game_settings.get("error_rate", 0.05),
        }

    @classmethod
    def _build_spread(cls, field_zones: list) -> dict:
        """Build spread dict from field_zones array."""
        spread = {
            "leftline": 14,
            "left": 14,
            "centerleft": 14,
            "center": 14,
            "centerright": 14,
            "right": 14,
            "rightline": 14
        }

        for zone in field_zones:
            zone_name = zone.get("name", "")
            spread_key = cls.FIELD_ZONE_TO_SPREAD.get(zone_name)
            if spread_key:
                spread[spread_key] = zone.get("spread_angle", 14)

        return spread

    @classmethod
    def _convert_distweights(cls, distance_weights: dict) -> dict:
        """
        Convert distance_weights from dict format to array format.

        Endpoint format: {barrel: {homerun: 0.2, deep_of: 0.45, ...}}
        Engine format: {barrel: [0.20, 0.45, 0.25, 0.10, 0.00, ...]}

        Array order: homerun, deep_of, middle_of, shallow_of, deep_if,
                     middle_if, shallow_if, mound, catcher
        """
        result = {}
        for contact_type, weights in distance_weights.items():
            # Build array in the correct order
            weight_array = []
            for outcome in cls.DIST_OUTCOMES:
                weight_array.append(weights.get(outcome, 0.0))
            result[contact_type] = weight_array
        return result

    @classmethod
    def _convert_fieldingweights(cls, fielding_weights: dict) -> dict:
        """
        Convert fielding_weights from dict format to array format.

        Endpoint format: {barrel: {out: 0.25, single: 0.28, ...}}
        Engine format: {barrel: [100.25, 0.28, 0.10, 0.05]}

        Array order: out, single, double, triple
        Note: The 'out' value gets 100 added to it as a marker in the engine
        """
        result = {}
        for contact_type, weights in fielding_weights.items():
            weight_array = []
            for i, outcome in enumerate(cls.FIELDING_OUTCOMES):
                value = weights.get(outcome, 0.0)
                # Add 100 to the 'out' value as a marker
                if outcome == "out":
                    value = 100 + value
                weight_array.append(value)
            result[contact_type] = weight_array
        return result

    @classmethod
    def _convert_fieldingmod(cls, fielding_modifier: dict) -> dict:
        """
        Convert fielding_modifier from dict format to array format.

        Endpoint format: {air: {infield: {out: 2, single: 2, ...}}}
        Engine format: {air: {infield: [2, 2, 3, 0]}}

        Array order: out, single, double, triple
        """
        result = {}
        for hit_type, zones in fielding_modifier.items():  # air, ground
            result[hit_type] = {}
            for zone, outcomes in zones.items():  # infield, outfield
                outcome_array = []
                for outcome in cls.FIELDING_OUTCOMES:
                    outcome_array.append(outcomes.get(outcome, 0))
                result[hit_type][zone] = outcome_array
        return result

    @classmethod
    def _build_difficulty_array(cls, fielding_difficulty: dict,
                                difficulty_level: str) -> list:
        """
        Build difficulty array from fielding_difficulty dict.

        Converts:
        {
            "center_left": {"catcher": "directlyat", "deep_if": "onestepaway", ...},
            ...
        }

        Into arrays of [direction, depth] pairs where depth matches difficulty_level:
        [["center left", "catcher"], ["far left", "middle_if"], ...]

        Direction keys are converted from underscores to spaces.
        """
        result = []
        for direction, depths in fielding_difficulty.items():
            engine_direction = DirectionMapper.to_engine(direction)
            for depth, level in depths.items():
                if level == difficulty_level:
                    result.append([engine_direction, depth])
        return result

    @classmethod
    def _convert_catch_rates(cls, catch_rates: dict) -> dict:
        """
        Convert catch_rates from endpoint format, merging with defaults.

        Endpoint format:
        {
            "barrel": {"deep_gap": 0.25, "gap": 0.45, ...},
            "solid": {...},
            ...
        }

        Returns full catch_rates dict with defaults for missing values.
        """
        import copy
        result = copy.deepcopy(cls.DEFAULT_CATCH_RATES)

        # Merge in any provided values from endpoint
        for contact_type, situations in catch_rates.items():
            if contact_type not in result:
                result[contact_type] = {}
            for situation, rate in situations.items():
                result[contact_type][situation] = float(rate)

        return result

    @classmethod
    def get_injury_rates(cls, level_config: dict) -> dict:
        """
        Extract injury rate settings from level config.

        Args:
            level_config: The level-specific config

        Returns:
            Dict with pregame and ingame injury base rates
        """
        game_settings = level_config.get("game", {})
        return {
            "pregame_base_rate": game_settings.get("pregame_injury_base_rate", 0.1),
            "ingame_base_rate": game_settings.get("ingame_injury_base_rate", 0.1),
        }
