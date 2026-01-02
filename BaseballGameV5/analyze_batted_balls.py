"""
Batted Ball Analysis Script

Analyzes output_test.json to understand:
1. Hit rates by contact type
2. Out rates when catch_probability = 0
3. Depth distribution by contact type
4. Where the "missing hits" are going
"""

import json
from collections import defaultdict
from pathlib import Path


def load_output(filepath):
    """Load the output JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def analyze_batted_balls(data):
    """Analyze all batted ball events across all games."""

    # Data structures for analysis
    contact_type_stats = defaultdict(lambda: {
        'total': 0,
        'hits': 0,  # single, double, triple, homerun
        'outs': 0,
        'by_depth': defaultdict(lambda: {'total': 0, 'hits': 0, 'outs': 0}),
        'by_situation': defaultdict(lambda: {'total': 0, 'hits': 0, 'outs': 0}),
        'zero_catch_rate': {'total': 0, 'hits': 0, 'outs': 0},
        'zero_catch_by_depth': defaultdict(lambda: {'total': 0, 'hits': 0, 'outs': 0}),
    })

    # Track all plays for detailed analysis
    all_plays = []
    zero_catch_outs = []  # Plays where catch_rate=0 but still out

    game_count = 0

    # Iterate through all subweeks and games
    for subweek_name, games in data.get('subweeks', {}).items():
        for game in games:
            game_count += 1
            play_by_play = game.get('play_by_play', [])

            for play in play_by_play:
                batted_ball = play.get('Batted Ball')

                # Skip non-batted ball events
                if batted_ball == 'None' or batted_ball is None:
                    continue

                depth = play.get('Hit Depth', 'unknown')
                direction = play.get('Hit Direction', 'unknown')
                situation = play.get('Hit Situation', 'unknown')
                catch_prob = play.get('Catch Probability')
                outcome = play.get('Defensive Outcome', 'unknown')

                # Determine if it's a hit
                is_hit = outcome in ['single', 'double', 'triple', 'homerun']
                is_out = outcome == 'out'

                # Skip if neither hit nor out (shouldn't happen much)
                if not is_hit and not is_out:
                    continue

                # Track the play
                play_record = {
                    'contact_type': batted_ball,
                    'depth': depth,
                    'direction': direction,
                    'situation': situation,
                    'catch_prob': catch_prob,
                    'outcome': outcome,
                    'is_hit': is_hit,
                }
                all_plays.append(play_record)

                # Update stats
                stats = contact_type_stats[batted_ball]
                stats['total'] += 1
                if is_hit:
                    stats['hits'] += 1
                else:
                    stats['outs'] += 1

                # By depth
                stats['by_depth'][depth]['total'] += 1
                if is_hit:
                    stats['by_depth'][depth]['hits'] += 1
                else:
                    stats['by_depth'][depth]['outs'] += 1

                # By situation
                stats['by_situation'][situation]['total'] += 1
                if is_hit:
                    stats['by_situation'][situation]['hits'] += 1
                else:
                    stats['by_situation'][situation]['outs'] += 1

                # Zero catch rate analysis
                if catch_prob is not None and catch_prob == 0:
                    stats['zero_catch_rate']['total'] += 1
                    if is_hit:
                        stats['zero_catch_rate']['hits'] += 1
                    else:
                        stats['zero_catch_rate']['outs'] += 1
                        zero_catch_outs.append(play_record)

                    # Zero catch by depth
                    stats['zero_catch_by_depth'][depth]['total'] += 1
                    if is_hit:
                        stats['zero_catch_by_depth'][depth]['hits'] += 1
                    else:
                        stats['zero_catch_by_depth'][depth]['outs'] += 1

    return contact_type_stats, all_plays, zero_catch_outs, game_count


def print_report(contact_type_stats, all_plays, zero_catch_outs, game_count):
    """Print a formatted analysis report."""

    print("=" * 80)
    print("BATTED BALL ANALYSIS REPORT")
    print(f"Games Analyzed: {game_count}")
    print(f"Total Batted Ball Events: {len(all_plays)}")
    print("=" * 80)

    # Overall hit rate by contact type
    print("\n" + "=" * 80)
    print("1. OVERALL HIT RATE BY CONTACT TYPE")
    print("=" * 80)
    print(f"{'Contact Type':<12} {'Total':>8} {'Hits':>8} {'Outs':>8} {'Hit Rate':>10}")
    print("-" * 50)

    for contact_type in ['barrel', 'solid', 'flare', 'burner', 'under', 'topped', 'weak']:
        stats = contact_type_stats.get(contact_type, {'total': 0, 'hits': 0, 'outs': 0})
        total = stats['total']
        hits = stats['hits']
        outs = stats['outs']
        hit_rate = (hits / total * 100) if total > 0 else 0
        print(f"{contact_type:<12} {total:>8} {hits:>8} {outs:>8} {hit_rate:>9.1f}%")

    # Zero catch rate analysis
    print("\n" + "=" * 80)
    print("2. ZERO CATCH RATE OUTCOMES (catch_probability = 0)")
    print("   These should theoretically all be hits, but throw-outs can occur")
    print("=" * 80)
    print(f"{'Contact Type':<12} {'Total':>8} {'Hits':>8} {'Outs':>8} {'Hit Rate':>10}")
    print("-" * 50)

    for contact_type in ['barrel', 'solid', 'flare', 'burner', 'under', 'topped', 'weak']:
        stats = contact_type_stats.get(contact_type, {})
        zero_stats = stats.get('zero_catch_rate', {'total': 0, 'hits': 0, 'outs': 0})
        total = zero_stats['total']
        hits = zero_stats['hits']
        outs = zero_stats['outs']
        hit_rate = (hits / total * 100) if total > 0 else 0
        if total > 0:
            print(f"{contact_type:<12} {total:>8} {hits:>8} {outs:>8} {hit_rate:>9.1f}%")

    # Zero catch rate outs by depth
    print("\n" + "=" * 80)
    print("3. ZERO CATCH RATE OUTS BY DEPTH")
    print("   Where are the 'should-be-hits' becoming outs?")
    print("=" * 80)

    for contact_type in ['flare', 'burner', 'topped', 'weak']:
        stats = contact_type_stats.get(contact_type, {})
        zero_by_depth = stats.get('zero_catch_by_depth', {})

        if not zero_by_depth:
            continue

        print(f"\n{contact_type.upper()}:")
        print(f"  {'Depth':<15} {'Total':>8} {'Hits':>8} {'Outs':>8} {'Hit Rate':>10}")
        print(f"  " + "-" * 50)

        for depth in ['deep_of', 'middle_of', 'shallow_of', 'deep_if', 'middle_if', 'shallow_if', 'mound', 'catcher']:
            depth_stats = zero_by_depth.get(depth, {'total': 0, 'hits': 0, 'outs': 0})
            total = depth_stats['total']
            if total > 0:
                hits = depth_stats['hits']
                outs = depth_stats['outs']
                hit_rate = (hits / total * 100)
                print(f"  {depth:<15} {total:>8} {hits:>8} {outs:>8} {hit_rate:>9.1f}%")

    # Depth distribution by contact type
    print("\n" + "=" * 80)
    print("4. DEPTH DISTRIBUTION BY CONTACT TYPE (where balls land)")
    print("=" * 80)

    for contact_type in ['flare', 'burner']:
        stats = contact_type_stats.get(contact_type, {})
        by_depth = stats.get('by_depth', {})
        total_for_type = stats.get('total', 0)

        if total_for_type == 0:
            continue

        print(f"\n{contact_type.upper()} (n={total_for_type}):")
        print(f"  {'Depth':<15} {'Count':>8} {'% of Total':>12} {'Hit Rate':>10}")
        print(f"  " + "-" * 50)

        for depth in ['homerun', 'deep_of', 'middle_of', 'shallow_of', 'deep_if', 'middle_if', 'shallow_if', 'mound', 'catcher']:
            depth_stats = by_depth.get(depth, {'total': 0, 'hits': 0, 'outs': 0})
            total = depth_stats['total']
            if total > 0:
                hits = depth_stats['hits']
                pct = (total / total_for_type * 100)
                hit_rate = (hits / total * 100)
                print(f"  {depth:<15} {total:>8} {pct:>11.1f}% {hit_rate:>9.1f}%")

    # Summary of zero-catch-rate outs
    print("\n" + "=" * 80)
    print("5. SAMPLE OF ZERO CATCH RATE OUTS (for debugging)")
    print("=" * 80)

    # Group by contact type and depth
    grouped = defaultdict(list)
    for play in zero_catch_outs:
        key = (play['contact_type'], play['depth'])
        grouped[key].append(play)

    for (contact_type, depth), plays in sorted(grouped.items()):
        print(f"\n{contact_type} to {depth}: {len(plays)} outs with 0% catch rate")
        # Show first few
        for play in plays[:3]:
            print(f"  - direction: {play['direction']}, situation: {play['situation']}")

    # Recommendations
    print("\n" + "=" * 80)
    print("6. TUNING RECOMMENDATIONS")
    print("=" * 80)

    print("\nKey observations:")

    # Calculate infield vs outfield zero-catch outs
    if_outs = sum(1 for p in zero_catch_outs if p['depth'] in ['deep_if', 'middle_if', 'shallow_if', 'mound', 'catcher'])
    of_outs = sum(1 for p in zero_catch_outs if p['depth'] in ['deep_of', 'middle_of', 'shallow_of'])

    print(f"  - Zero catch rate outs in INFIELD: {if_outs}")
    print(f"  - Zero catch rate outs in OUTFIELD: {of_outs}")
    print(f"  - Total zero catch rate outs: {len(zero_catch_outs)}")

    if if_outs > 0:
        print(f"\n  The {if_outs} infield outs with 0% catch rate are from throw-outs.")
        print("  These occur when the fielder has time to throw to first before the runner arrives.")

    print("\nTuning options:")
    print("  A. Shift depth distribution: More flares/burners to outfield depths")
    print("  B. Increase infield retrieval time in TimeCalculator.TIMING_CONSTANTS")
    print("  C. Add 'bobble penalty' time when catch_rate roll fails")
    print("  D. Reduce throw accuracy for rushed plays")


def main():
    # Find the output file
    script_dir = Path(__file__).parent
    output_file = script_dir / 'output_test.json'

    if not output_file.exists():
        print(f"Error: Could not find {output_file}")
        return

    print(f"Loading {output_file}...")
    data = load_output(output_file)

    print("Analyzing batted ball events...")
    contact_type_stats, all_plays, zero_catch_outs, game_count = analyze_batted_balls(data)

    print_report(contact_type_stats, all_plays, zero_catch_outs, game_count)


if __name__ == '__main__':
    main()
