"""
Rules Adapter - Transforms endpoint rules format to engine Rules format.

The endpoint provides:
- innings: Number of innings
- outs_per_inning: Outs per half inning
- balls_for_walk: Balls for a walk
- strikes_for_k: Strikes for a strikeout
- dh: Whether DH rule is in effect

This adapter converts these to the format expected by the Rules class.
"""


class RulesAdapter:
    """Transforms endpoint rules data to engine Rules format."""

    @classmethod
    def adapt(cls, rules_data: dict) -> dict:
        """
        Convert endpoint rules format to engine rules format.

        Args:
            rules_data: The rules dict from the endpoint

        Returns:
            Dict ready for Rules.from_dict()
        """
        return {
            "Innings": rules_data.get("innings", 9),
            "Outs": rules_data.get("outs_per_inning", 3),
            "Balls": rules_data.get("balls_for_walk", 4),
            "Strikes": rules_data.get("strikes_for_k", 3),
            "DH": rules_data.get("dh", True),
        }

    @classmethod
    def uses_dh(cls, rules_data: dict) -> bool:
        """
        Check if DH rule is in effect.

        Args:
            rules_data: The rules dict from the endpoint

        Returns:
            True if DH is in effect, False if pitcher bats
        """
        return rules_data.get("dh", True)
