"""
Injury Adapter - Handles pregame injury effects and injury type utilities.

The endpoint provides:
- pregame_injuries: Array of injuries affecting players before the game
- injury_types: Array of all possible injury types with their effects and durations

This adapter:
1. Applies pregame injury effects to player stats
2. Provides utilities for injury type lookups
3. Calculates injury risk modifiers based on player injury_risk attribute
"""

from typing import Dict, List, Optional
from Player import Player


class InjuryAdapter:
    """Handles pregame injury effects and injury type utilities."""

    # Risk multipliers for injury chance
    RISK_MULTIPLIERS = {
        "Volatile": 2.0,
        "Risky": 1.5,
        "Normal": 1.0,
        "Dependable": 0.7,
        "Safe": 0.5,
    }

    # Map of effect keys to player attributes
    EFFECT_TO_ATTRIBUTE = {
        "contact": "contact",
        "power": "power",
        "discipline": "discipline",
        "eye": "eye",
        "speed": "speed",
        "baserunning": "baserunning",
        "basereaction": "basereaction",
        "throwpower": "throwpower",
        "throwacc": "throwacc",
        "fieldcatch": "fieldcatch",
        "fieldreact": "fieldreact",
        "fieldspot": "fieldspot",
        "pendurance": "pendurance",
        "pthrowpower": "pthrowpower",
        "pgencontrol": "pgencontrol",
        "stamina_pct": "energy",  # Applied as percentage
    }

    def __init__(self, injury_types: List[dict]):
        """
        Initialize with injury types from endpoint.

        Args:
            injury_types: Array of injury type definitions
        """
        self.injury_types = {
            injury["code"]: injury for injury in injury_types
        }
        self.injury_types_by_id = {
            injury["id"]: injury for injury in injury_types
        }

    def get_injury_type(self, code: str) -> Optional[dict]:
        """Get injury type by code."""
        return self.injury_types.get(code)

    def get_injury_type_by_id(self, injury_id: int) -> Optional[dict]:
        """Get injury type by ID."""
        return self.injury_types_by_id.get(injury_id)

    def get_risk_multiplier(self, injury_risk: str) -> float:
        """
        Get injury risk multiplier for a player's injury risk level.

        Args:
            injury_risk: Player's injury_risk attribute

        Returns:
            Multiplier for injury chance (higher = more likely to get injured)
        """
        return self.RISK_MULTIPLIERS.get(injury_risk, 1.0)

    @classmethod
    def apply_pregame_injuries(cls, players: List[Player],
                               pregame_injuries: List[dict]) -> List[dict]:
        """
        Apply pregame injury effects to players.

        Args:
            players: List of Player objects
            pregame_injuries: List of pregame injury dicts from endpoint

        Returns:
            List of applied injury reports for response
        """
        # Build player lookup by ID
        player_lookup = {p.id: p for p in players}

        injury_reports = []

        for injury in pregame_injuries:
            player_id = injury.get("player_id")
            player = player_lookup.get(player_id)

            if not player:
                continue

            effects = injury.get("effects", {})
            applied_effects = {}

            for effect_key, multiplier in effects.items():
                attr_name = cls.EFFECT_TO_ATTRIBUTE.get(effect_key)
                if not attr_name:
                    continue

                if hasattr(player, attr_name):
                    original_value = getattr(player, attr_name)
                    new_value = original_value * multiplier
                    setattr(player, attr_name, new_value)
                    applied_effects[attr_name] = {
                        "original": original_value,
                        "modified": new_value,
                        "multiplier": multiplier
                    }

            # Build injury report
            injury_reports.append({
                "player_id": player_id,
                "player_name": f"{player.firstname} {player.lastname}",
                "code": injury.get("code"),
                "name": injury.get("name"),
                "timeframe": "pregame",
                "duration_weeks": injury.get("duration_weeks", 1),
                "effects": applied_effects
            })

        return injury_reports

    @classmethod
    def build_injury_lookup(cls, injury_types: List[dict]) -> Dict[str, dict]:
        """
        Build a lookup dict from injury types array.

        Args:
            injury_types: Array of injury type definitions

        Returns:
            Dict keyed by injury code
        """
        return {injury["code"]: injury for injury in injury_types}

    def get_ingame_injury_pool(self, target: str = None) -> List[dict]:
        """
        Get pool of injuries that can occur in-game.

        Args:
            target: Filter by target ("hitter", "pitcher", "both", or None for all)

        Returns:
            List of injury types that can occur in-game
        """
        pool = []
        for injury in self.injury_types.values():
            if injury.get("timeframe") != "ingame":
                continue
            if target and injury.get("target") not in [target, "both"]:
                continue
            pool.append(injury)
        return pool

    def get_pregame_injury_pool(self, target: str = None) -> List[dict]:
        """
        Get pool of injuries that can occur pregame.

        Args:
            target: Filter by target ("hitter", "pitcher", "both", or None for all)

        Returns:
            List of injury types that can occur pregame
        """
        pool = []
        for injury in self.injury_types.values():
            if injury.get("timeframe") != "pregame":
                continue
            if target and injury.get("target") not in [target, "both"]:
                continue
            pool.append(injury)
        return pool

    def calculate_injury_duration(self, injury_type: dict) -> int:
        """
        Calculate random duration for an injury.

        Uses mean_weeks as center with min_weeks and max_weeks as bounds.

        Args:
            injury_type: Injury type definition

        Returns:
            Duration in weeks
        """
        import random
        min_weeks = injury_type.get("min_weeks", 1)
        max_weeks = injury_type.get("max_weeks", 4)
        mean_weeks = injury_type.get("mean_weeks", 2)

        # Use triangular distribution centered on mean
        return round(random.triangular(min_weeks, max_weeks, mean_weeks))

    def calculate_injury_effects(self, injury_type: dict) -> dict:
        """
        Calculate random effects for an injury.

        Uses min_pct and max_pct from impact_template_json.

        Args:
            injury_type: Injury type definition

        Returns:
            Dict of attribute -> multiplier
        """
        import random

        impact_template = injury_type.get("impact_template_json", {})
        effects = {}

        for attr, bounds in impact_template.items():
            if isinstance(bounds, dict):
                min_pct = bounds.get("min_pct", 1.0)
                max_pct = bounds.get("max_pct", 1.0)
                effects[attr] = random.uniform(min_pct, max_pct)
            else:
                effects[attr] = bounds

        return effects
