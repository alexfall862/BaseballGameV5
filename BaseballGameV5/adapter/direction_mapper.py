"""
Direction Mapper - Handles the critical direction naming convention mismatch.

The endpoint returns direction names with underscores (far_left, center_left, etc.)
but the engine expects spaces (far left, center left, etc.).

This module provides conversion utilities to bridge this gap.
"""


class DirectionMapper:
    """Converts between endpoint format (underscores) and engine format (spaces)."""

    # Endpoint uses underscores, engine expects spaces
    ENDPOINT_TO_ENGINE = {
        "far_left": "far left",
        "center_left": "center left",
        "dead_center": "dead center",
        "center_right": "center right",
        "far_right": "far right",
        # These stay the same
        "left": "left",
        "right": "right",
    }

    ENGINE_TO_ENDPOINT = {v: k for k, v in ENDPOINT_TO_ENGINE.items()}

    @classmethod
    def to_engine(cls, direction: str) -> str:
        """
        Convert endpoint direction to engine format.

        Args:
            direction: Direction string from endpoint (e.g., "far_left")

        Returns:
            Direction string for engine (e.g., "far left")
        """
        return cls.ENDPOINT_TO_ENGINE.get(direction, direction)

    @classmethod
    def to_endpoint(cls, direction: str) -> str:
        """
        Convert engine direction to endpoint format.

        Args:
            direction: Direction string from engine (e.g., "far left")

        Returns:
            Direction string for endpoint (e.g., "far_left")
        """
        return cls.ENGINE_TO_ENDPOINT.get(direction, direction)

    @classmethod
    def convert_defensive_alignment(cls, alignment: dict) -> dict:
        """
        Convert entire defensive alignment dict keys from underscores to spaces.

        The defensive alignment structure is:
        {
            "far_left": {
                "deep_of": ["leftfield"],
                ...
            },
            ...
        }

        Args:
            alignment: Defensive alignment dict from endpoint

        Returns:
            Defensive alignment dict with space-separated direction keys
        """
        return {
            cls.to_engine(direction): depths
            for direction, depths in alignment.items()
        }

    @classmethod
    def convert_fielding_difficulty(cls, difficulty: dict) -> dict:
        """
        Convert fielding difficulty dict keys from underscores to spaces.

        Args:
            difficulty: Fielding difficulty dict from endpoint

        Returns:
            Fielding difficulty dict with space-separated direction keys
        """
        return {
            cls.to_engine(direction): depths
            for direction, depths in difficulty.items()
        }
