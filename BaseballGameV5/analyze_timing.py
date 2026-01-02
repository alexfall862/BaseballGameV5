"""
Timing Analysis Script (Updated for Enhanced Timing System)

Analyzes the new Timing_Diagnostics data to understand:
1. Speed distribution of batters
2. How speed affects hit/out outcomes
3. Timing margins by speed bucket
4. NEW: fieldreact and fieldspot impact
5. NEW: Variance effects on outcomes
6. Detailed flare/burner timing breakdown
"""

import json
from collections import defaultdict
from pathlib import Path


def load_output(filepath):
    """Load the output JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def analyze_timing(data):
    """Analyze timing diagnostics from all batted ball events."""

    # Data collection
    plays_with_timing = []
    speed_buckets = {
        'slow (20-40)': {'hits': 0, 'outs': 0, 'margins': []},
        'below_avg (40-50)': {'hits': 0, 'outs': 0, 'margins': []},
        'average (50-60)': {'hits': 0, 'outs': 0, 'margins': []},
        'above_avg (60-70)': {'hits': 0, 'outs': 0, 'margins': []},
        'fast (70-80)': {'hits': 0, 'outs': 0, 'margins': []},
        'elite (80+)': {'hits': 0, 'outs': 0, 'margins': []},
    }

    contact_type_timing = defaultdict(lambda: {
        'plays': [],
        'speeds': [],
        'margins': [],
        'hits': 0,
        'outs': 0,
        # NEW: Track enhanced timing components
        'defense_variances': [],
        'runner_variances': [],
        'reaction_times': [],
        'fieldspot_modifiers': [],
        'fielder_fieldreacts': [],
        'fielder_fieldspots': [],
    })

    game_count = 0

    # Iterate through all subweeks and games
    for subweek_name, games in data.get('subweeks', {}).items():
        for game in games:
            game_count += 1
            play_by_play = game.get('play_by_play', [])

            for play in play_by_play:
                timing = play.get('Timing_Diagnostics')
                if timing is None:
                    continue

                batted_ball = play.get('Batted Ball')
                outcome = play.get('Defensive Outcome')

                if batted_ball == 'None' or batted_ball is None:
                    continue

                is_hit = outcome in ['single', 'double', 'triple', 'homerun']
                is_out = outcome == 'out'

                if not is_hit and not is_out:
                    continue

                speed = timing.get('batter_speed', 50)
                margin = timing.get('timing_margin', 0)
                field_time = timing.get('field_time', 0)
                progress = timing.get('runner_progress', 0)

                # NEW: Extract enhanced timing components
                defense_variance = timing.get('defense_variance', 0)
                runner_variance = timing.get('runner_variance', 0)
                reaction_time = timing.get('reaction_time', 0)
                fieldspot_mod = timing.get('fieldspot_modifier', 1.0)
                fielder_fieldreact = timing.get('fielder_fieldreact', 50)
                fielder_fieldspot = timing.get('fielder_fieldspot', 50)
                ball_travel = timing.get('ball_travel', 0)
                reach_time_base = timing.get('reach_time_base', 0)
                reach_time_modified = timing.get('reach_time_modified', 0)
                retrieval_time = timing.get('retrieval_time', 0)

                play_record = {
                    'batted_ball': batted_ball,
                    'outcome': outcome,
                    'is_hit': is_hit,
                    'speed': speed,
                    'margin': margin,
                    'field_time': field_time,
                    'progress': progress,
                    'depth': play.get('Hit Depth'),
                    'direction': play.get('Hit Direction'),
                    'timing': timing,
                    # NEW: Store enhanced components
                    'defense_variance': defense_variance,
                    'runner_variance': runner_variance,
                    'reaction_time': reaction_time,
                    'fieldspot_modifier': fieldspot_mod,
                    'fielder_fieldreact': fielder_fieldreact,
                    'fielder_fieldspot': fielder_fieldspot,
                    'ball_travel': ball_travel,
                    'reach_time_base': reach_time_base,
                    'reach_time_modified': reach_time_modified,
                    'retrieval_time': retrieval_time,
                }
                plays_with_timing.append(play_record)

                # Bucket by speed
                if speed < 40:
                    bucket = 'slow (20-40)'
                elif speed < 50:
                    bucket = 'below_avg (40-50)'
                elif speed < 60:
                    bucket = 'average (50-60)'
                elif speed < 70:
                    bucket = 'above_avg (60-70)'
                elif speed < 80:
                    bucket = 'fast (70-80)'
                else:
                    bucket = 'elite (80+)'

                speed_buckets[bucket]['margins'].append(margin)
                if is_hit:
                    speed_buckets[bucket]['hits'] += 1
                else:
                    speed_buckets[bucket]['outs'] += 1

                # Track by contact type
                ct_stats = contact_type_timing[batted_ball]
                ct_stats['plays'].append(play_record)
                ct_stats['speeds'].append(speed)
                ct_stats['margins'].append(margin)
                if is_hit:
                    ct_stats['hits'] += 1
                else:
                    ct_stats['outs'] += 1

                # NEW: Track enhanced components
                ct_stats['defense_variances'].append(defense_variance)
                ct_stats['runner_variances'].append(runner_variance)
                ct_stats['reaction_times'].append(reaction_time)
                ct_stats['fieldspot_modifiers'].append(fieldspot_mod)
                ct_stats['fielder_fieldreacts'].append(fielder_fieldreact)
                ct_stats['fielder_fieldspots'].append(fielder_fieldspot)

    return plays_with_timing, speed_buckets, contact_type_timing, game_count


def print_report(plays_with_timing, speed_buckets, contact_type_timing, game_count):
    """Print timing analysis report."""

    print("=" * 90)
    print("ENHANCED TIMING DIAGNOSTICS ANALYSIS")
    print("Includes: fieldreact, fieldspot, defense/runner variance")
    print(f"Games Analyzed: {game_count}")
    print(f"Plays with Timing Data: {len(plays_with_timing)}")
    print("=" * 90)

    # Speed bucket analysis
    print("\n" + "=" * 90)
    print("1. HIT RATE BY SPEED BUCKET")
    print("   Does speed actually affect outcomes?")
    print("=" * 90)
    print(f"{'Speed Bucket':<20} {'Hits':>8} {'Outs':>8} {'Hit Rate':>10} {'Avg Margin':>12}")
    print("-" * 60)

    for bucket in ['slow (20-40)', 'below_avg (40-50)', 'average (50-60)',
                   'above_avg (60-70)', 'fast (70-80)', 'elite (80+)']:
        stats = speed_buckets[bucket]
        total = stats['hits'] + stats['outs']
        if total > 0:
            hit_rate = stats['hits'] / total * 100
            avg_margin = sum(stats['margins']) / len(stats['margins']) if stats['margins'] else 0
            print(f"{bucket:<20} {stats['hits']:>8} {stats['outs']:>8} {hit_rate:>9.1f}% {avg_margin:>11.3f}s")

    # NEW: Enhanced timing component analysis for flares/burners
    print("\n" + "=" * 90)
    print("2. FLARE & BURNER TIMING BREAKDOWN (Enhanced)")
    print("=" * 90)

    for contact_type in ['flare', 'burner']:
        stats = contact_type_timing.get(contact_type)
        if not stats or not stats['plays']:
            print(f"\n{contact_type.upper()}: No data available")
            continue

        print(f"\n{'='*40}")
        print(f"{contact_type.upper()}")
        print(f"{'='*40}")

        total = stats['hits'] + stats['outs']
        hit_rate = stats['hits'] / total * 100 if total > 0 else 0

        print(f"\n  OUTCOMES:")
        print(f"    Total: {total}, Hits: {stats['hits']}, Outs: {stats['outs']}")
        print(f"    Hit Rate: {hit_rate:.1f}%")

        # Batter speed analysis
        avg_speed = sum(stats['speeds']) / len(stats['speeds']) if stats['speeds'] else 0
        print(f"\n  BATTER SPEED:")
        print(f"    Average: {avg_speed:.1f}")

        # Timing margin analysis
        avg_margin = sum(stats['margins']) / len(stats['margins']) if stats['margins'] else 0
        print(f"\n  TIMING MARGIN:")
        print(f"    Average: {avg_margin:.3f}s")
        if stats['margins']:
            print(f"    Range: {min(stats['margins']):.3f}s to {max(stats['margins']):.3f}s")

        # NEW: Variance analysis
        if stats['defense_variances']:
            avg_def_var = sum(stats['defense_variances']) / len(stats['defense_variances'])
            avg_run_var = sum(stats['runner_variances']) / len(stats['runner_variances'])
            print(f"\n  VARIANCE (per-play randomness):")
            print(f"    Defense variance avg: {avg_def_var:.3f}s")
            print(f"    Runner variance avg:  {avg_run_var:.3f}s")
            if stats['defense_variances']:
                print(f"    Defense range: {min(stats['defense_variances']):.3f}s to {max(stats['defense_variances']):.3f}s")
            if stats['runner_variances']:
                print(f"    Runner range:  {min(stats['runner_variances']):.3f}s to {max(stats['runner_variances']):.3f}s")

        # NEW: Reaction time analysis (fieldreact)
        if stats['reaction_times'] and any(r > 0 for r in stats['reaction_times']):
            avg_react = sum(stats['reaction_times']) / len(stats['reaction_times'])
            print(f"\n  REACTION TIME (fieldreact impact):")
            print(f"    Average: {avg_react:.3f}s")
            print(f"    Range: {min(stats['reaction_times']):.3f}s to {max(stats['reaction_times']):.3f}s")

        # NEW: Fieldspot modifier analysis
        if stats['fieldspot_modifiers'] and any(f != 1.0 for f in stats['fieldspot_modifiers']):
            avg_fspot = sum(stats['fieldspot_modifiers']) / len(stats['fieldspot_modifiers'])
            print(f"\n  FIELDSPOT MODIFIER:")
            print(f"    Average: {avg_fspot:.4f}")
            print(f"    Range: {min(stats['fieldspot_modifiers']):.4f} to {max(stats['fieldspot_modifiers']):.4f}")

        # NEW: Fielder attribute distribution
        if stats['fielder_fieldreacts']:
            avg_fr = sum(stats['fielder_fieldreacts']) / len(stats['fielder_fieldreacts'])
            avg_fs = sum(stats['fielder_fieldspots']) / len(stats['fielder_fieldspots'])
            print(f"\n  FIELDER ATTRIBUTES:")
            print(f"    Avg fieldreact: {avg_fr:.1f}")
            print(f"    Avg fieldspot:  {avg_fs:.1f}")

        # Group by hit vs out with enhanced analysis
        hit_plays = [p for p in stats['plays'] if p['is_hit']]
        out_plays = [p for p in stats['plays'] if not p['is_hit']]

        if hit_plays:
            hit_speeds = [p['speed'] for p in hit_plays]
            hit_def_vars = [p['defense_variance'] for p in hit_plays]
            hit_run_vars = [p['runner_variance'] for p in hit_plays]
            print(f"\n  HITS ({len(hit_plays)}):")
            print(f"    Batter speed avg: {sum(hit_speeds)/len(hit_speeds):.1f}")
            if hit_def_vars:
                print(f"    Defense variance avg: {sum(hit_def_vars)/len(hit_def_vars):.3f}s")
                print(f"    Runner variance avg:  {sum(hit_run_vars)/len(hit_run_vars):.3f}s")

        if out_plays:
            out_speeds = [p['speed'] for p in out_plays]
            out_margins = [p['margin'] for p in out_plays]
            out_def_vars = [p['defense_variance'] for p in out_plays]
            out_run_vars = [p['runner_variance'] for p in out_plays]
            print(f"\n  OUTS ({len(out_plays)}):")
            print(f"    Batter speed avg: {sum(out_speeds)/len(out_speeds):.1f}")
            print(f"    Margin avg: {sum(out_margins)/len(out_margins):.3f}s")
            if out_def_vars:
                print(f"    Defense variance avg: {sum(out_def_vars)/len(out_def_vars):.3f}s")
                print(f"    Runner variance avg:  {sum(out_run_vars)/len(out_run_vars):.3f}s")

            # Close plays analysis
            close_outs = [p for p in out_plays if abs(p['margin']) < 0.3]
            print(f"\n    Close plays (|margin| < 0.3s): {len(close_outs)}")
            if close_outs:
                print(f"      These could flip with variance!")

    # NEW: Variance impact analysis
    print("\n" + "=" * 90)
    print("3. VARIANCE IMPACT ANALYSIS")
    print("   How often does variance change the outcome?")
    print("=" * 90)

    for contact_type in ['flare', 'burner']:
        stats = contact_type_timing.get(contact_type)
        if not stats or not stats['plays']:
            continue

        print(f"\n{contact_type.upper()}:")

        # Find plays where variance could have flipped outcome
        flippable_plays = []
        for play in stats['plays']:
            margin = play['margin']
            def_var = play.get('defense_variance', 0)
            run_var = play.get('runner_variance', 0)
            total_var = abs(def_var) + abs(run_var)

            # If margin is smaller than potential variance swing, it could flip
            if abs(margin) < 0.4:  # Within typical variance range
                flippable_plays.append(play)

        total = len(stats['plays'])
        if total > 0:
            print(f"  Plays within flip range (|margin| < 0.4s): {len(flippable_plays)} ({len(flippable_plays)/total*100:.1f}%)")

            # Analyze flippable plays
            if flippable_plays:
                flipped_hits = [p for p in flippable_plays if p['is_hit']]
                flipped_outs = [p for p in flippable_plays if not p['is_hit']]
                print(f"    Of these: {len(flipped_hits)} were hits, {len(flipped_outs)} were outs")

    # NEW: Field time component breakdown
    print("\n" + "=" * 90)
    print("4. FIELD TIME COMPONENT BREAKDOWN")
    print("   What contributes to total field time?")
    print("=" * 90)

    for contact_type in ['flare', 'burner']:
        stats = contact_type_timing.get(contact_type)
        if not stats or not stats['plays']:
            continue

        plays = stats['plays']
        if not plays:
            continue

        # Calculate averages for each component
        ball_travels = [p.get('ball_travel', 0) for p in plays if p.get('ball_travel')]
        reaction_times = [p.get('reaction_time', 0) for p in plays if p.get('reaction_time')]
        reach_times = [p.get('reach_time_modified', 0) for p in plays if p.get('reach_time_modified')]
        retrieval_times = [p.get('retrieval_time', 0) for p in plays if p.get('retrieval_time')]
        defense_vars = [p.get('defense_variance', 0) for p in plays]
        field_times = [p.get('field_time', 0) for p in plays if p.get('field_time')]

        print(f"\n{contact_type.upper()} (n={len(plays)}):")

        if field_times:
            print(f"  Total field time avg: {sum(field_times)/len(field_times):.3f}s")
        if ball_travels:
            print(f"    Ball travel:     {sum(ball_travels)/len(ball_travels):.3f}s")
        if reaction_times:
            print(f"    Reaction time:   {sum(reaction_times)/len(reaction_times):.3f}s (fieldreact)")
        if reach_times:
            print(f"    Reach time:      {sum(reach_times)/len(reach_times):.3f}s (includes fieldspot)")
        if retrieval_times:
            print(f"    Retrieval time:  {sum(retrieval_times)/len(retrieval_times):.3f}s")
        if defense_vars:
            print(f"    Defense variance:{sum(defense_vars)/len(defense_vars):+.3f}s (avg)")

    # Sample detailed plays
    print("\n" + "=" * 90)
    print("5. SAMPLE DETAILED PLAYS")
    print("   Showing full timing breakdown")
    print("=" * 90)

    for contact_type in ['flare', 'burner']:
        stats = contact_type_timing.get(contact_type)
        if not stats or not stats['plays']:
            continue

        print(f"\n{contact_type.upper()} - Sample plays:")

        # Show a few hits and outs
        hits = [p for p in stats['plays'] if p['is_hit']][:3]
        outs = [p for p in stats['plays'] if not p['is_hit']][:3]

        for i, play in enumerate(hits):
            t = play.get('timing', {})
            print(f"\n  HIT {i+1}: {play['depth']} ({play['outcome']})")
            print(f"    Batter speed: {play['speed']:.1f}")
            print(f"    Field time: {play['field_time']:.3f}s")
            print(f"      Ball travel: {t.get('ball_travel', 'N/A')}")
            print(f"      Reaction: {t.get('reaction_time', 'N/A')} (fieldreact={t.get('fielder_fieldreact', 'N/A')})")
            print(f"      Reach: {t.get('reach_time_modified', 'N/A')} (fieldspot_mod={t.get('fieldspot_modifier', 'N/A')})")
            print(f"      Retrieval: {t.get('retrieval_time', 'N/A')}")
            print(f"      Defense var: {t.get('defense_variance', 'N/A')}")
            print(f"    Runner var: {t.get('runner_variance', 'N/A')}")
            print(f"    Timing margin: {play['margin']:.3f}s")

        for i, play in enumerate(outs):
            t = play.get('timing', {})
            print(f"\n  OUT {i+1}: {play['depth']}")
            print(f"    Batter speed: {play['speed']:.1f}")
            print(f"    Field time: {play['field_time']:.3f}s")
            print(f"      Ball travel: {t.get('ball_travel', 'N/A')}")
            print(f"      Reaction: {t.get('reaction_time', 'N/A')} (fieldreact={t.get('fielder_fieldreact', 'N/A')})")
            print(f"      Reach: {t.get('reach_time_modified', 'N/A')} (fieldspot_mod={t.get('fieldspot_modifier', 'N/A')})")
            print(f"      Retrieval: {t.get('retrieval_time', 'N/A')}")
            print(f"      Defense var: {t.get('defense_variance', 'N/A')}")
            print(f"    Runner var: {t.get('runner_variance', 'N/A')}")
            print(f"    Timing margin: {play['margin']:.3f}s (defense wins by this)")


def main():
    script_dir = Path(__file__).parent
    output_file = script_dir / 'output_test.json'

    if not output_file.exists():
        print(f"Error: Could not find {output_file}")
        return

    print(f"Loading {output_file}...")
    data = load_output(output_file)

    # Check if there's actual game data
    total_games = 0
    for subweek, games in data.get('subweeks', {}).items():
        total_games += len(games)

    if total_games == 0:
        print("\nNo game data found in output_test.json!")
        print("The file shows errors for all games - need to fix the simulation first.")
        print("\nError summary from file:")
        errors = data.get('errors', [])
        if errors:
            print(f"  Total errors: {len(errors)}")
            print(f"  Sample error: {errors[0].get('error', 'unknown')}")
        return

    print("Analyzing timing diagnostics...")
    plays_with_timing, speed_buckets, contact_type_timing, game_count = analyze_timing(data)

    if not plays_with_timing:
        print("\nNo timing diagnostics found in the game data.")
        print("This could mean:")
        print("  1. Games ran but didn't record timing data")
        print("  2. The timing diagnostics weren't enabled")
        return

    print_report(plays_with_timing, speed_buckets, contact_type_timing, game_count)


if __name__ == '__main__':
    main()
