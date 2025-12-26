"""
Pydantic models for FastAPI request/response validation.

These models define the structure of API requests and responses
for the baseball simulation endpoints.

Both single game and batch endpoints now use the same unified payload structure.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# Request Models

class BallparkModel(BaseModel):
    """Ballpark configuration."""
    power_mod: float = Field(default=1.0, description="Power modifier for this ballpark")
    pitch_break_mod: float = Field(default=1.0, description="Pitch break modifier")
    ballpark_name: Optional[str] = None


class RulesModel(BaseModel):
    """Game rules configuration."""
    innings: int = Field(default=9, description="Number of innings")
    outs_per_inning: int = Field(default=3, description="Outs per half inning")
    balls_for_walk: int = Field(default=4, description="Balls for a walk")
    strikes_for_k: int = Field(default=3, description="Strikes for strikeout")
    dh: bool = Field(default=True, description="Whether DH rule is in effect")


class InjuryEffects(BaseModel):
    """Injury effects on player attributes."""
    contact: Optional[float] = None
    power: Optional[float] = None
    stamina_pct: Optional[float] = None


class PregameInjury(BaseModel):
    """Pregame injury affecting a player."""
    player_id: int
    code: str
    name: str
    injury_type_id: int
    duration_weeks: int
    timeframe: str = "pregame"
    effects: Dict[str, float] = Field(default_factory=dict)


class TeamSide(BaseModel):
    """Team data for one side of the game."""
    team_abbrev: Optional[str] = None
    team_name: Optional[str] = None
    team_nickname: Optional[str] = None
    org_id: Optional[int] = None
    players: List[Dict[str, Any]]
    lineup: List[int]
    defense: Dict[str, int]
    bench: List[int]
    available_pitcher_ids: List[int]
    starting_pitcher_id: int
    pregame_injuries: List[Dict[str, Any]] = Field(default_factory=list)


class LevelConfig(BaseModel):
    """Level-specific configuration."""
    batting: Dict[str, float] = Field(default_factory=dict)
    contact_odds: Dict[str, float] = Field(default_factory=dict)
    distance_weights: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    fielding_weights: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    game: Dict[str, float] = Field(default_factory=dict)


class GameCore(BaseModel):
    """
    Individual game data within subweeks.

    Does NOT contain rules or level_config - those are looked up from
    top-level rules/level_configs using league_level_id.
    """
    game_id: int
    league_level_id: int = Field(default=9, description="Level ID to look up rules/config")
    league_year_id: Optional[int] = None
    season_subweek: Optional[str] = None
    random_seed: Optional[str] = None
    ballpark: BallparkModel = Field(default_factory=BallparkModel)
    away_side: TeamSide
    home_side: TeamSide


class SimulationPayload(BaseModel):
    """
    Unified payload structure for both single game and batch simulations.

    Single game: Has 1 game in subweeks.a
    Batch: Has multiple games across subweeks a/b/c/d
    """
    league_year_id: Optional[int] = None
    league_level: Optional[int] = None
    season_week: Optional[int] = None
    total_games: Optional[int] = None

    # Top-level shared data
    game_constants: Dict[str, Any] = Field(default_factory=dict)
    level_configs: Dict[str, Any] = Field(default_factory=dict)  # Keyed by level_id string
    rules: Dict[str, RulesModel] = Field(default_factory=dict)  # Keyed by level_id string
    injury_types: List[Dict[str, Any]] = Field(default_factory=list)

    # Games organized by subweek
    subweeks: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)


# Response Models

class PlayerRef(BaseModel):
    """Player reference in response."""
    player_id: int
    player_name: str


class GameResult(BaseModel):
    """Game result summary."""
    home_team: str
    home_score: int
    away_team: str
    away_score: int
    winning_team: str


class InjuryReport(BaseModel):
    """Injury report for a player."""
    player_id: int
    player_name: str
    code: str
    name: str
    timeframe: str
    duration_weeks: int
    effects: Dict[str, Any] = Field(default_factory=dict)
    injury_type_id: Optional[int] = None


class GameResponse(BaseModel):
    """Single game simulation response."""
    game_id: int
    result: GameResult
    boxscore: Dict[str, Any]
    play_by_play: List[Dict[str, Any]]
    injuries: List[Dict[str, Any]] = Field(default_factory=list)


class SimulationResponse(BaseModel):
    """
    Unified response for both single game and batch simulations.

    Results organized by subweek, matching input structure.
    """
    subweeks: Dict[str, List[GameResponse]]
    total_games_simulated: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    details: Optional[str] = None
