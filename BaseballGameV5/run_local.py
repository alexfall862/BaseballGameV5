"""
Local testing entry point for running simulations from JSON files.

Both single game and batch payloads now use the same unified structure.
Single game: 1 game in subweeks.a
Batch: Multiple games across subweeks a/b/c/d

Usage:
    python run_local.py <json_file>
    python run_local.py ../exampleresponse.json
"""

import os
import sys
import json
import argparse

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import Game


# Default configurations
DEFAULT_RULES = {
    "innings": 9,
    "outs_per_inning": 3,
    "balls_for_walk": 4,
    "strikes_for_k": 3,
    "dh": True
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
    "game": {}
}


def load_json_file(filepath: str) -> dict:
    """Load and parse a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def run_single_game(game_data: dict, rules: dict, level_config: dict,
                    game_constants: dict, injury_types: list = None) -> dict:
    """
    Run a single game simulation.

    Args:
        game_data: Individual game data from subweeks
        rules: Rules for this game's level
        level_config: Level-specific configuration
        game_constants: Shared game constants
        injury_types: Injury type definitions

    Returns:
        Game result dictionary
    """
    game = Game.Game.from_endpoint(
        payload=game_data,
        rules=rules,
        level_config=level_config,
        game_constants=game_constants,
        injury_types=injury_types
    )

    return game.run_simulation()


def process_payload(payload: dict, verbose: bool = False) -> dict:
    """
    Process a unified payload (works for both single game and batch).

    Args:
        payload: The unified payload structure
        verbose: Print detailed output

    Returns:
        Results dict with subweeks, counts, errors
    """
    game_constants = payload.get("game_constants", {})
    level_configs = payload.get("level_configs", {})
    rules_by_level = payload.get("rules", {})
    injury_types = payload.get("injury_types", [])
    subweeks = payload.get("subweeks", {})

    results = {}
    total_games = 0
    successful_games = 0
    errors = []

    for subweek_name, games in subweeks.items():
        if not games:
            continue

        results[subweek_name] = []
        print(f"\nSubweek {subweek_name}: {len(games)} game(s)")

        for game_data in games:
            total_games += 1
            game_id = game_data.get("game_id", "?")

            # Get level_id from game data
            level_id = str(game_data.get("league_level_id", "9"))

            # Look up rules and level_config for this level
            rules = rules_by_level.get(level_id, DEFAULT_RULES)
            level_config = level_configs.get(level_id, DEFAULT_LEVEL_CONFIG)

            try:
                result = run_single_game(
                    game_data=game_data,
                    rules=rules,
                    level_config=level_config,
                    game_constants=game_constants,
                    injury_types=injury_types
                )

                results[subweek_name].append(result)
                successful_games += 1

                # Print result
                r = result['result']
                print(f"  Game {game_id}: {r['away_team']} {r['away_score']} @ "
                      f"{r['home_team']} {r['home_score']} -> {r['winning_team']}")

                if verbose and result.get('injuries'):
                    for injury in result['injuries']:
                        print(f"    Injury: {injury.get('player_name')} - "
                              f"{injury.get('name')} ({injury.get('timeframe')})")

            except Exception as e:
                print(f"  Game {game_id}: ERROR - {e}")
                errors.append({
                    "game_id": game_id,
                    "subweek": subweek_name,
                    "error": str(e)
                })
                if verbose:
                    import traceback
                    traceback.print_exc()

    return {
        "subweeks": results,
        "total_games": total_games,
        "successful_games": successful_games,
        "errors": errors
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run baseball simulations from JSON files"
    )
    parser.add_argument(
        "json_file",
        help="Path to JSON file (unified payload structure)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (defaults to stdout summary)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed output including injuries and tracebacks"
    )

    args = parser.parse_args()

    # Load JSON file
    print(f"Loading: {args.json_file}")
    payload = load_json_file(args.json_file)

    # Count total games
    total_games = sum(
        len(games) for games in payload.get("subweeks", {}).values()
    )
    print(f"Total games in payload: {total_games}")

    # Show subweeks
    subweeks = payload.get("subweeks", {})
    for sw, games in subweeks.items():
        if games:
            print(f"  Subweek {sw}: {len(games)} game(s)")

    # Process payload
    results = process_payload(payload, verbose=args.verbose)

    # Summary
    print()
    print("=" * 50)
    print(f"Completed: {results['successful_games']}/{results['total_games']} games")

    if results['errors']:
        print(f"Errors: {len(results['errors'])}")
        for err in results['errors']:
            print(f"  - Game {err['game_id']}: {err['error']}")

    # Save output - always save for debugging, use specified path or default
    output_path = args.output or "output_test.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
