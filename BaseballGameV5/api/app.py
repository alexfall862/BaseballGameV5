"""
FastAPI application for baseball game simulation.

Provides a unified endpoint for both single game and batch simulations.
Both use the same payload structure - single game just has 1 game in subweeks.a.
"""

import sys
import os
import asyncio
from typing import Dict, List, Any
from contextlib import asynccontextmanager
from concurrent.futures import ProcessPoolExecutor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import (
    SimulationPayload,
    SimulationResponse,
    BatchPayload,
    BatchResponse,
    HealthResponse,
)
import Game

# Shared process pool for parallel game simulation across all requests
_process_pool: ProcessPoolExecutor | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage shared process pool lifecycle."""
    global _process_pool
    cpus = os.cpu_count() or 4
    _process_pool = ProcessPoolExecutor(max_workers=cpus)
    yield
    _process_pool.shutdown(wait=True)
    _process_pool = None


# Create FastAPI app
app = FastAPI(
    title="Baseball Game Simulation API",
    description="Simulate baseball games with deterministic results",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware for service-to-service communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Default configurations (used if not provided in payload)
DEFAULT_GAME_CONSTANTS = {
    "defensive_alignment": {},
    "fielding_difficulty": {},
    "fielding_modifier": {},
    "time_to_ground": {},
    "field_zones": [],
}

DEFAULT_LEVEL_CONFIG = {
    "batting": {
        "inside_contact": 0.87,
        "inside_swing": 0.65,
        "modexp": 2,
        "outside_contact": 0.66,
        "outside_swing": 0.3
    },
    "contact_odds": {
        "barrel": 7, "solid": 12, "flare": 36, "burner": 39,
        "under": 2.4, "topped": 3.2, "weak": 0.4
    },
    "distance_weights": {},
    "fielding_weights": {},
    "game": {
        "energy_step": 2, "energy_tick_cap": 1.5, "error_rate": 0.05,
        "fielding_multiplier": 0, "ingame_injury_base_rate": 0.001,
        "long_leash": 0.5, "normal_leash": 0.7, "pickoff_success": 0.1,
        "pregame_injury_base_rate": 0.1, "short_leash": 0.8, "steal_success": 0.65
    }
}

DEFAULT_RULES = {
    "innings": 9,
    "outs_per_inning": 3,
    "balls_for_walk": 4,
    "strikes_for_k": 3,
    "dh": True
}


def simulate_single_game(
    game_data: dict,
    rules: dict,
    level_config: dict,
    game_constants: dict,
    injury_types: list = None,
    detail_level: str = "full"
) -> dict:
    """
    Simulate a single game.

    Args:
        game_data: Individual game data from subweeks
        rules: Rules for this game's level
        level_config: Level-specific configuration
        game_constants: Shared game constants
        injury_types: List of injury type definitions
        detail_level: Response verbosity - "full", "standard", or "minimal"

    Returns:
        Game result dictionary
    """
    try:
        # Create game from endpoint payload
        game = Game.Game.from_endpoint(
            payload=game_data,
            rules=rules,
            level_config=level_config,
            game_constants=game_constants,
            injury_types=injury_types
        )

        # Run simulation
        result = game.run_simulation(detail_level=detail_level)
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "game_id": game_data.get("game_id", 0),
            "error": str(e),
            "result": None,
            "boxscore": None,
            "play_by_play": [],
            "injuries": []
        }


def _worker_simulate(job: dict) -> dict:
    """
    Worker function for parallel simulation. Runs in a subprocess.

    Args:
        job: Dict with game_data, rules, level_config, game_constants,
             injury_types, and payload_index for error reporting.

    Returns:
        Dict with result or error info.
    """
    try:
        result = simulate_single_game(
            game_data=job["game_data"],
            rules=job["rules"],
            level_config=job["level_config"],
            game_constants=job["game_constants"],
            injury_types=job.get("injury_types"),
            detail_level=job.get("detail_level", "full"),
        )
        if "error" in result and result.get("result") is None:
            return {
                "ok": False,
                "game_id": job["game_data"].get("game_id"),
                "payload_index": job["payload_index"],
                "error": result["error"],
            }
        return {"ok": True, "result": result}
    except Exception as e:
        return {
            "ok": False,
            "game_id": job["game_data"].get("game_id"),
            "payload_index": job["payload_index"],
            "error": str(e),
        }


def process_simulation(payload_dict: dict) -> dict:
    """
    Process a simulation payload (works for both single game and batch).

    Args:
        payload_dict: The unified payload structure

    Returns:
        Results dict with subweeks, total_games_simulated, errors
    """
    game_constants = payload_dict.get("game_constants", DEFAULT_GAME_CONSTANTS)
    level_configs = payload_dict.get("level_configs", {})
    rules_by_level = payload_dict.get("rules", {})
    injury_types = payload_dict.get("injury_types", [])
    subweeks = payload_dict.get("subweeks", {})

    results: Dict[str, List[dict]] = {}
    errors: List[dict] = []
    total_games = 0
    successful_games = 0

    for subweek_name, games in subweeks.items():
        results[subweek_name] = []

        for game_data in games:
            total_games += 1

            # Get level_id from game data
            level_id = str(game_data.get("league_level_id", "9"))

            # Look up rules and level_config for this level
            rules = rules_by_level.get(level_id, DEFAULT_RULES)
            if hasattr(rules, 'model_dump'):
                rules = rules.model_dump()

            level_config = level_configs.get(level_id, DEFAULT_LEVEL_CONFIG)
            if hasattr(level_config, 'model_dump'):
                level_config = level_config.model_dump()

            try:
                result = simulate_single_game(
                    game_data=game_data,
                    rules=rules,
                    level_config=level_config,
                    game_constants=game_constants,
                    injury_types=injury_types
                )

                if "error" in result and result.get("result") is None:
                    errors.append({
                        "game_id": game_data.get("game_id"),
                        "subweek": subweek_name,
                        "error": result["error"]
                    })
                else:
                    results[subweek_name].append(result)
                    successful_games += 1

            except Exception as e:
                errors.append({
                    "game_id": game_data.get("game_id"),
                    "subweek": subweek_name,
                    "error": str(e)
                })

    return {
        "subweeks": results,
        "total_games_simulated": successful_games,
        "errors": errors
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Railway."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/simulate", response_model=SimulationResponse)
async def simulate(payload: SimulationPayload):
    """
    Unified simulation endpoint for both single game and batch.

    Single game: Has 1 game in subweeks.a
    Batch: Has multiple games across subweeks a/b/c/d

    Args:
        payload: Unified simulation payload

    Returns:
        Results organized by subweek
    """
    try:
        payload_dict = payload.model_dump()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, process_simulation, payload_dict)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Keep legacy endpoints for backwards compatibility
@app.post("/simulate/game", response_model=SimulationResponse)
async def simulate_game(payload: SimulationPayload):
    """
    Legacy single game endpoint - redirects to unified /simulate.
    """
    return await simulate(payload)


@app.post("/simulate/batch", response_model=BatchResponse)
async def simulate_batch(payload: BatchPayload):
    """
    Batch endpoint that accepts an array of game payloads.

    Shared config (game_constants, level_configs, rules, injury_types) can
    be at the top level or per-game element. Per-game values take priority.

    Games are simulated in parallel across CPU cores.
    """
    subweek_key = payload.subweek or "a"

    # Top-level shared config (fallback when per-game element omits them)
    shared_game_constants = payload.game_constants or DEFAULT_GAME_CONSTANTS
    shared_level_configs = payload.level_configs or {}
    shared_rules = payload.rules or {}
    shared_injury_types = payload.injury_types or []

    # Build flat list of jobs to dispatch
    jobs = []
    for i, game_payload in enumerate(payload.games):
        game_constants = game_payload.get("game_constants") or shared_game_constants
        level_configs = game_payload.get("level_configs") or shared_level_configs
        rules_by_level = game_payload.get("rules") or shared_rules
        injury_types = game_payload.get("injury_types") or shared_injury_types
        subweeks = game_payload.get("subweeks", {})
        games_in_subweek = subweeks.get(subweek_key, [])

        for game_data in games_in_subweek:
            level_id = str(game_data.get("league_level_id",
                           game_payload.get("league_level", "9")))

            rules = rules_by_level.get(level_id, DEFAULT_RULES)
            if hasattr(rules, 'model_dump'):
                rules = rules.model_dump()

            level_config = level_configs.get(level_id, DEFAULT_LEVEL_CONFIG)
            if hasattr(level_config, 'model_dump'):
                level_config = level_config.model_dump()

            jobs.append({
                "game_data": game_data,
                "rules": rules,
                "level_config": level_config,
                "game_constants": game_constants,
                "injury_types": injury_types,
                "payload_index": i,
                "detail_level": payload.detail_level,
            })

    # Submit all games to the shared process pool (non-blocking)
    loop = asyncio.get_event_loop()
    futures = [
        loop.run_in_executor(_process_pool, _worker_simulate, job)
        for job in jobs
    ]
    outcomes = await asyncio.gather(*futures, return_exceptions=True)

    results = []
    errors = []
    for outcome in outcomes:
        if isinstance(outcome, Exception):
            errors.append({"game_id": None, "payload_index": None, "error": str(outcome)})
        elif outcome["ok"]:
            results.append(outcome["result"])
        else:
            errors.append({
                "game_id": outcome.get("game_id"),
                "payload_index": outcome.get("payload_index"),
                "error": outcome.get("error"),
            })

    return {
        "results": results,
        "total_games_simulated": len(results),
        "errors": errors
    }


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Baseball Game Simulation API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/simulate": "Unified simulation endpoint (single or batch)",
            "/simulate/game": "Legacy single game endpoint",
            "/simulate/batch": "Batch endpoint (accepts games array)"
        }
    }
