"""
Injury System - Handles in-game injury generation and effects.

This module provides:
- In-game injury checks during at-bats
- Injury generation based on player risk and injury pool
- Application of injury effects to player stats
"""

import random
from typing import Optional, List, Dict


class InjurySystem:
    """Handles in-game injury generation and tracking."""

    # Risk multipliers for injury chance
    RISK_MULTIPLIERS = {
        "Volatile": 2.0,
        "Risky": 1.5,
        "Normal": 1.0,
        "Dependable": 0.7,
        "Safe": 0.5,
    }

    def __init__(self, injury_adapter, base_rate: float = 0.001):
        """
        Initialize the injury system.

        Args:
            injury_adapter: InjuryAdapter instance with injury type definitions
            base_rate: Base probability of injury per at-bat (default 0.1%)
        """
        self.injury_adapter = injury_adapter
        self.base_rate = base_rate
        self.injuries_this_game = []

    def check_for_injury(self, player, action_type: str = "atbat") -> Optional[dict]:
        """
        Check if a player gets injured during an action.

        Args:
            player: Player object to check
            action_type: Type of action (atbat, pitch, field, run)

        Returns:
            Injury report dict if injured, None otherwise
        """
        if not self.injury_adapter:
            return None

        # Get player's risk multiplier
        injury_risk = getattr(player, 'injuryrisk', 'Normal')
        risk_mult = self.RISK_MULTIPLIERS.get(injury_risk, 1.0)

        # Calculate injury probability
        injury_prob = self.base_rate * risk_mult

        # Action-specific modifiers
        if action_type == "pitch":
            injury_prob *= 1.5  # Pitchers slightly more injury prone
        elif action_type == "run":
            injury_prob *= 1.2  # Running has some injury risk
        elif action_type == "field":
            injury_prob *= 0.8  # Fielding is lower risk

        # Roll for injury
        if random.random() > injury_prob:
            return None

        # Player is injured - determine injury type
        target = "pitcher" if player.ptype == "Pitcher" else "hitter"
        injury_pool = self.injury_adapter.get_ingame_injury_pool(target)

        if not injury_pool:
            return None

        # Weight selection by frequency_weight
        weights = [float(inj.get("frequency_weight", 1.0)) for inj in injury_pool]
        total_weight = sum(weights)
        if total_weight == 0:
            return None

        # Random selection
        roll = random.random() * total_weight
        cumulative = 0
        selected_injury = None
        for i, inj in enumerate(injury_pool):
            cumulative += weights[i]
            if roll <= cumulative:
                selected_injury = inj
                break

        if not selected_injury:
            selected_injury = injury_pool[0]

        # Calculate duration and effects
        duration = self.injury_adapter.calculate_injury_duration(selected_injury)
        effects = self.injury_adapter.calculate_injury_effects(selected_injury)

        # Apply effects to player
        applied_effects = self._apply_injury_effects(player, effects)

        # Build injury report
        injury_report = {
            "player_id": player.id,
            "player_name": f"{player.firstname} {player.lastname}",
            "code": selected_injury.get("code"),
            "name": selected_injury.get("name"),
            "timeframe": "ingame",
            "duration_weeks": duration,
            "effects": applied_effects,
            "injury_type_id": selected_injury.get("id"),
        }

        self.injuries_this_game.append(injury_report)
        return injury_report

    def _apply_injury_effects(self, player, effects: dict) -> dict:
        """
        Apply injury effects to a player.

        Args:
            player: Player object
            effects: Dict of attribute -> multiplier

        Returns:
            Dict of applied effects with original/modified values
        """
        applied = {}

        effect_map = {
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
            "stamina_pct": "energy",
        }

        for effect_key, multiplier in effects.items():
            attr_name = effect_map.get(effect_key)
            if not attr_name or not hasattr(player, attr_name):
                continue

            original = getattr(player, attr_name)
            modified = original * multiplier
            setattr(player, attr_name, modified)

            applied[attr_name] = {
                "original": original,
                "modified": modified,
                "multiplier": multiplier
            }

        # Mark player as injured
        player.injurystate = True

        return applied

    def get_injuries(self) -> List[dict]:
        """Get all injuries that occurred this game."""
        return self.injuries_this_game

    def reset(self):
        """Reset injuries for a new game."""
        self.injuries_this_game = []


def create_injury_system(injury_adapter, level_config: dict = None) -> InjurySystem:
    """
    Factory function to create an InjurySystem with appropriate settings.

    Args:
        injury_adapter: InjuryAdapter instance
        level_config: Level config with injury rate settings

    Returns:
        Configured InjurySystem instance
    """
    base_rate = 0.001  # Default 0.1% per at-bat

    if level_config:
        game_settings = level_config.get("game", {})
        base_rate = game_settings.get("ingame_injury_base_rate", 0.001)

    return InjurySystem(injury_adapter, base_rate)
