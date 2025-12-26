"""
Player Adapter - Transforms endpoint player format to engine Player objects.

The endpoint provides player data with:
- Attribute names ending in _base (e.g., contact_base, power_base)
- Pitch data as flat fields (pitch1_name, pitch1_ovr, pitch1_pacc_base, etc.)
- Position abbreviations (fb, sb, tb instead of firstbase, secondbase, thirdbase)

This adapter converts all of that into the format expected by the Player constructor.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Player import Player


class PlayerAdapter:
    """Transforms endpoint player format to engine Player objects."""

    # Position mapping: endpoint abbreviation -> engine lineup name
    POSITION_MAP = {
        "c": "catcher",
        "fb": "firstbase",
        "sb": "secondbase",
        "tb": "thirdbase",
        "ss": "shortstop",
        "lf": "leftfield",
        "cf": "centerfield",
        "rf": "rightfield",
        "dh": "designatedhitter",
        "startingpitcher": "starter",
    }

    @classmethod
    def adapt_team(cls, team_side: dict, team_name: str, team_full_name: str) -> list:
        """
        Convert all players from a team side into Player objects.

        Args:
            team_side: The away_side or home_side dict from the endpoint
            team_name: Team abbreviation (e.g., "ARI", "PHI")
            team_full_name: Full team name (e.g., "Arizona Diamondbacks")

        Returns:
            List of Player objects ready for the engine
        """
        players = []

        defense = team_side.get("defense", {})
        lineup = team_side.get("lineup", [])
        available_pitcher_ids = team_side.get("available_pitcher_ids", [])
        bench = team_side.get("bench", [])
        starting_pitcher_id = team_side.get("starting_pitcher_id")

        for player_data in team_side.get("players", []):
            player = cls.adapt(
                player_data=player_data,
                defense=defense,
                lineup=lineup,
                available_pitchers=available_pitcher_ids,
                bench=bench,
                starting_pitcher_id=starting_pitcher_id,
                team_name=team_name,
                team_full_name=team_full_name
            )
            players.append(player)

        return players

    @classmethod
    def adapt(cls, player_data: dict, defense: dict, lineup: list,
              available_pitchers: list, bench: list,
              starting_pitcher_id: int, team_name: str,
              team_full_name: str = None) -> Player:
        """
        Convert endpoint player dict to engine Player object.

        Args:
            player_data: Player dict from endpoint with _base suffix attributes
            defense: Defense dict mapping position abbrev to player_id
            lineup: List of player_ids in batting order
            available_pitchers: List of available pitcher player_ids
            bench: List of bench player_ids
            starting_pitcher_id: Player ID of starting pitcher
            team_name: Team abbreviation
            team_full_name: Full team name (optional)

        Returns:
            Player object ready for the engine
        """
        pid = player_data["id"]

        # Determine lineup position
        lineup_position = cls._determine_lineup_position(
            pid, defense, lineup, available_pitchers,
            bench, starting_pitcher_id
        )

        # Determine batting order (1-9, or 0 for non-starters)
        batting_order = cls._determine_batting_order(pid, lineup)

        # Determine pitching order
        pitching_order = cls._determine_pitching_order(
            pid, starting_pitcher_id, available_pitchers
        )

        # Build pitch objects
        pitches = cls._build_pitches(player_data)

        # Build handedness array [bat, throw]
        handedness = [
            player_data.get("bat_hand", "R"),
            player_data.get("pitch_hand", "R")
        ]

        return Player(
            pid=pid,
            ptype=player_data.get("ptype", "Position"),
            firstname=player_data.get("firstname", "Unknown"),
            lastname=player_data.get("lastname", "Player"),
            handedness=handedness,
            armangle=player_data.get("arm_angle", "3/4's"),
            injuryrisk=player_data.get("injury_risk", "Normal"),
            durability=player_data.get("durability", "Normal"),

            # Hitting (remove _base suffix)
            contact=float(player_data.get("contact_base", 50)),
            power=float(player_data.get("power_base", 50)),
            discipline=float(player_data.get("discipline_base", 50)),
            eye=float(player_data.get("eye_base", 50)),

            # Running
            basereaction=float(player_data.get("basereaction_base", 50)),
            baserunning=float(player_data.get("baserunning_base", 50)),
            speed=float(player_data.get("speed_base", 50)),

            # Fielding
            throwpower=float(player_data.get("throwpower_base", 50)),
            throwacc=float(player_data.get("throwacc_base", 50)),
            fieldcatch=float(player_data.get("fieldcatch_base", 50)),
            fieldreact=float(player_data.get("fieldreact_base", 50)),
            fieldspot=float(player_data.get("fieldspot_base", 50)),

            # Catching
            catchframe=float(player_data.get("catchframe_base", 50)),
            catchsequence=float(player_data.get("catchsequence_base", 50)),

            # Pitching
            pendurance=float(player_data.get("pendurance_base", 50)),
            pthrowpower=float(player_data.get("pthrowpower_base", 50)),
            pgencontrol=float(player_data.get("pgencontrol_base", 50)),
            pickoff=float(player_data.get("pickoff_base", 50)),
            psequencing=float(player_data.get("psequencing_base", 50)),

            # 5 pitch objects
            pitch1=pitches[0],
            pitch2=pitches[1],
            pitch3=pitches[2],
            pitch4=pitches[3],
            pitch5=pitches[4],

            # Team info
            team=team_full_name or team_name,
            level="mlb",  # Could be derived from league_level_id

            # Position ratings
            sp_rating=float(player_data.get("sp_rating", 0)),
            rp_rating=float(player_data.get("rp_rating", 0)),
            c_rating=float(player_data.get("c_rating", 0)),
            fb_rating=float(player_data.get("fb_rating", 0)),
            sb_rating=float(player_data.get("sb_rating", 0)),
            tb_rating=float(player_data.get("tb_rating", 0)),
            ss_rating=float(player_data.get("ss_rating", 0)),
            lf_rating=float(player_data.get("lf_rating", 0)),
            cf_rating=float(player_data.get("cf_rating", 0)),
            rf_rating=float(player_data.get("rf_rating", 0)),
            dh_rating=float(player_data.get("dh_rating", 0)),

            # Roster position
            battingorder=batting_order,
            pitchingorder=pitching_order,
            lineup=lineup_position,

            # State
            injurystate=False,
            energy=float(player_data.get("stamina", 100)),
            teamname=team_name,

            # Strategy attributes
            stealfreq=float(player_data.get("stealfreq", 10.0)),
            pickofffreq=float(player_data.get("pickofffreq", 10.0)),
            plate_approach=player_data.get("plate_approach", "normal"),
            pitchchoices=player_data.get("pitchchoices", [])
        )

    @classmethod
    def _build_pitches(cls, player_data: dict) -> list:
        """Build 5 CreatePitch objects from player data."""
        pitches = []
        for i in range(1, 6):
            pitch = Player.CreatePitch(
                pitchname=player_data.get(f"pitch{i}_name", "Fastball"),
                ovr=float(player_data.get(f"pitch{i}_ovr", 50)),
                pacc=float(player_data.get(f"pitch{i}_pacc_base", 50)),
                pcntrl=float(player_data.get(f"pitch{i}_pcntrl_base", 50)),
                pbrk=float(player_data.get(f"pitch{i}_pbrk_base", 50)),
                consist=float(player_data.get(f"pitch{i}_consist_base", 50))
            )
            pitches.append(pitch)
        return pitches

    @classmethod
    def _determine_lineup_position(cls, pid: int, defense: dict, lineup: list,
                                   available_pitchers: list, bench: list,
                                   starting_pitcher_id: int) -> str:
        """Determine lineup position string for player."""
        # Check if starting pitcher
        if pid == starting_pitcher_id:
            return "starter"

        # Check if in defensive lineup
        for pos_abbrev, player_id in defense.items():
            if player_id == pid and pos_abbrev != "startingpitcher":
                return cls.POSITION_MAP.get(pos_abbrev, pos_abbrev)

        # Check if relief pitcher
        if pid in available_pitchers and pid != starting_pitcher_id:
            return "relief"

        # Check if on bench
        if pid in bench:
            return "bench"

        return "bench"

    @classmethod
    def _determine_batting_order(cls, pid: int, lineup: list) -> int:
        """Determine batting order (1-9) or 0 if not in lineup."""
        if pid in lineup:
            return lineup.index(pid) + 1
        return 0

    @classmethod
    def _determine_pitching_order(cls, pid: int, starting_pitcher_id: int,
                                  available_pitchers: list) -> int:
        """Determine pitching order."""
        if pid == starting_pitcher_id:
            return 1
        if pid in available_pitchers:
            try:
                return available_pitchers.index(pid) + 2
            except ValueError:
                return 0
        return 0

    @classmethod
    def apply_ballpark_modifiers(cls, players: list, power_mod: float = 1.0,
                                  pitch_break_mod: float = 1.0) -> list:
        """
        Apply ballpark modifiers to player stats.

        Args:
            players: List of Player objects
            power_mod: Multiplier for power stats
            pitch_break_mod: Multiplier for pitch break stats

        Returns:
            List of Player objects with modifiers applied
        """
        for player in players:
            # Apply power modifier
            player.power = player.power * power_mod
            player.og_power = player.og_power * power_mod

            # Apply pitch break modifier to all pitches
            for pitch_num in range(1, 6):
                pitch = getattr(player, f"pitch{pitch_num}")
                pitch.pbrk = pitch.pbrk * pitch_break_mod
                # Also update original values
                og_attr = f"og_pitch{pitch_num}pbrk"
                if hasattr(player, og_attr):
                    setattr(player, og_attr, getattr(player, og_attr) * pitch_break_mod)

        return players
