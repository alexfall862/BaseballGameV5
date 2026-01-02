"""
Local testing entry point for running simulations from JSON files.

Both single game and batch payloads now use the same unified structure.
Single game: 1 game in subweeks.a
Batch: Multiple games across subweeks a/b/c/d

Usage:
    python run_local.py <json_file>
    python run_local.py ../exampleresponse.json
    python run_local.py input.json -o output.json --compact --no-debug
    python run_local.py input.json -o output.json.gz --compress
    python run_local.py input.json --split  # Creates output_a.json, output_b.json, etc.
"""

import os
import sys
import json
import gzip
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
                    game_constants: dict, injury_types: list = None,
                    include_debug: bool = True) -> dict:
    """
    Run a single game simulation.

    Args:
        game_data: Individual game data from subweeks
        rules: Rules for this game's level
        level_config: Level-specific configuration
        game_constants: Shared game constants
        injury_types: Injury type definitions
        include_debug: Whether to include debug data in output

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

    result = game.run_simulation()

    # Remove debug section if not requested (saves significant memory/disk)
    if not include_debug and 'debug' in result:
        del result['debug']

    return result


def process_payload(payload: dict, verbose: bool = False,
                    include_debug: bool = True) -> dict:
    """
    Process a unified payload (works for both single game and batch).

    Args:
        payload: The unified payload structure
        verbose: Print detailed output
        include_debug: Whether to include debug data in output

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
                    injury_types=injury_types,
                    include_debug=include_debug
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


def write_json_output(data: dict, output_path: str, compact: bool = False,
                      compress: bool = False):
    """
    Write JSON output with optional compression and formatting.

    Args:
        data: Data to write
        output_path: Output file path
        compact: If True, no indentation (smaller file)
        compress: If True, use gzip compression
    """
    indent = None if compact else 2

    if compress:
        # Ensure .gz extension
        if not output_path.endswith('.gz'):
            output_path += '.gz'
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, default=str)
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, default=str)

    return output_path


def write_split_output(results: dict, base_path: str, compact: bool = False,
                       compress: bool = False):
    """
    Write results split by subweek into separate files.

    Args:
        results: Full results dict with subweeks
        base_path: Base output path (e.g., "output" -> "output_a.json")
        compact: If True, no indentation
        compress: If True, use gzip compression

    Returns:
        List of written file paths
    """
    # Remove extension from base path
    base, ext = os.path.splitext(base_path)
    if ext == '.gz':
        base, _ = os.path.splitext(base)  # Handle .json.gz
        ext = '.json.gz' if compress else '.json'
    elif not ext:
        ext = '.json.gz' if compress else '.json'
    elif compress and not ext.endswith('.gz'):
        ext += '.gz'

    written_files = []
    subweeks = results.get('subweeks', {})

    for subweek_name, games in subweeks.items():
        if not games:
            continue

        # Create per-subweek result
        subweek_result = {
            "subweek": subweek_name,
            "games": games,
            "game_count": len(games),
            "total_games": results.get('total_games', 0),
            "successful_games": results.get('successful_games', 0),
        }

        output_path = f"{base}_{subweek_name}{ext}"
        actual_path = write_json_output(subweek_result, output_path, compact, compress)
        written_files.append(actual_path)
        print(f"  Written: {actual_path} ({len(games)} games)")

    # Write summary/errors file
    summary = {
        "total_games": results.get('total_games', 0),
        "successful_games": results.get('successful_games', 0),
        "errors": results.get('errors', []),
        "subweek_files": written_files
    }
    summary_path = f"{base}_summary{ext}"
    write_json_output(summary, summary_path, compact, compress)
    written_files.append(summary_path)
    print(f"  Written: {summary_path} (summary)")

    return written_files


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
        help="Output file path (defaults to output_test.json)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed output including injuries and tracebacks"
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Write compact JSON without indentation (smaller files)"
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Write gzip-compressed output (.gz)"
    )
    parser.add_argument(
        "--no-debug",
        action="store_true",
        help="Exclude debug section from output (significantly reduces size)"
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Split output into separate files per subweek"
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

    # Recommend options for large batches
    if total_games > 50:
        suggestions = []
        if not args.no_debug:
            suggestions.append("--no-debug")
        if not args.compact:
            suggestions.append("--compact")
        if not args.compress:
            suggestions.append("--compress")
        if suggestions:
            print(f"TIP: For large batches, consider: {' '.join(suggestions)}")

    # Show subweeks
    subweeks = payload.get("subweeks", {})
    for sw, games in subweeks.items():
        if games:
            print(f"  Subweek {sw}: {len(games)} game(s)")

    # Process payload
    include_debug = not args.no_debug
    results = process_payload(payload, verbose=args.verbose, include_debug=include_debug)

    # Summary
    print()
    print("=" * 50)
    print(f"Completed: {results['successful_games']}/{results['total_games']} games")

    if results['errors']:
        print(f"Errors: {len(results['errors'])}")
        for err in results['errors']:
            print(f"  - Game {err['game_id']}: {err['error']}")

    # Save output
    output_path = args.output or "output_test.json"

    print(f"\nWriting output...")
    if args.split:
        written_files = write_split_output(
            results, output_path,
            compact=args.compact,
            compress=args.compress
        )
        print(f"Split output into {len(written_files)} files")
    else:
        actual_path = write_json_output(
            results, output_path,
            compact=args.compact,
            compress=args.compress
        )
        # Get file size for feedback
        try:
            size_bytes = os.path.getsize(actual_path)
            if size_bytes > 1024 * 1024:
                size_str = f"{size_bytes / (1024*1024):.1f} MB"
            elif size_bytes > 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes} bytes"
            print(f"Results saved to: {actual_path} ({size_str})")
        except OSError:
            print(f"Results saved to: {actual_path}")


if __name__ == "__main__":
    main()
