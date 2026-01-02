from ast import Pass
import random
import Stats as stats
import numpy as np
from operator import attrgetter
from dataclasses import dataclass, field
from typing import Optional, List, Set, Tuple


# ============================================================================
# DATA STRUCTURES FOR DECISION TREE DEFENSE
# ============================================================================

@dataclass
class RunnerState:
    """Tracks a runner's state during a play."""
    player_id: int
    player: object  # Player object reference
    current_base: int  # 0=home, 1=first, 2=second, 3=third, 4=scored
    target_base: int
    progress: float = 0.0  # 0.0 to 1.0 (percentage to target)
    is_forced: bool = False
    speed_rating: float = 50.0
    basereaction: float = 50.0  # Reaction to ball contact (jump timing)
    baserunning: float = 50.0   # Route efficiency and decision quality
    is_out: bool = False
    earned_run: bool = True  # True until error occurs


@dataclass
class FielderState:
    """Tracks a fielder's state during a play."""
    position: str
    player: object  # Player object reference
    has_ball: bool = False
    location: str = ""  # zone identifier


@dataclass
class PlayState:
    """Tracks the overall state of a defensive play."""
    ball_location: str = ""
    ball_holder: Optional[FielderState] = None
    runners: List[RunnerState] = field(default_factory=list)
    outs_this_play: int = 0
    force_bases: Set[int] = field(default_factory=set)  # bases where force play applies
    play_active: bool = True
    contact_type: str = ""
    batted_ball_outcome: str = ""  # Will be determined by play resolution


# ============================================================================
# TIME CALCULATOR - Calculates timing for all play elements
# ============================================================================

class TimeCalculator:
    """Calculates timing for runners, throws, and catches."""

    # Base running times in seconds (from home plate perspective)
    # Average MLB times: home-to-first ~4.3s, base-to-base ~3.8s
    BASE_RUNNING_TIMES = {
        (0, 1): 4.3,   # home to first
        (1, 2): 3.8,   # first to second
        (2, 3): 3.8,   # second to third
        (3, 4): 3.8,   # third to home
    }

    # =========================================================================
    # TIMING CONSTANTS - Tunable values for physics-based hit outcomes
    # =========================================================================

    # Gap detection - directions that fall between outfielders
    GAP_DIRECTIONS = {
        "center left": ["leftfield", "centerfield"],
        "center right": ["centerfield", "rightfield"],
    }

    # Line directions - down the foul lines (corner outfielders must chase)
    LINE_DIRECTIONS = ["far left", "far right"]

    # Time additions (seconds) - TUNABLE for game balance
    TIMING_CONSTANTS = {
        "gap_reach_bonus": 3.5,      # Extra time for gap hits (between OF)
        "line_reach_bonus": 3.0,     # Extra time down the line
        "deep_chase_bonus": 2.0,     # Ball over fielder's head
        "outfield_retrieval": 2.0,   # Pick up and set in OF
        "infield_retrieval": 0.8,    # Pick up and set in IF (was 0.4 - too fast)
        "hard_hit_bonus": 0.5,       # Less reaction time on barrels/solids
        "base_reach_time": 0.5,      # Fielder already in position

        # Reaction time settings (fieldreact impact)
        "base_reaction_time": 0.5,   # Reaction time for 50-rated fieldreact
        "reaction_time_range": 0.6,  # Total range (0.2s to 0.8s across 20-80 rating)

        # Variance settings (per-play randomness)
        "defense_variance_std": 0.1, # Std dev for defense timing (±0.2s is ~2 std devs)
        "runner_variance_std": 0.1,  # Std dev for runner timing

        # Baserunning settings
        "runner_jump_per_point": 0.01,   # Seconds per basereaction point (±0.3s for 80/20)
        "route_efficiency_per_point": 0.00167,  # ~5% range over 60 points (80 vs 20)

        # Tag-up settings
        "tag_up_delay_base": 0.3,    # Base delay to tag up (50-rated basereaction)
        "tag_up_delay_range": 0.4,   # Range: 0.1s (80 rating) to 0.5s (20 rating)
    }

    # Depths where tag-up is viable (fly balls deep enough to tag up)
    TAG_UP_DEPTHS = ["deep_of", "middle_of", "shallow_of"]

    # Throw distance multiplier by depth for tag-up plays
    # Standard THROW_DISTANCES assume fielder at normal depth
    # Tag-ups happen at varying depths - deeper catches give more time
    TAG_UP_DEPTH_MULTIPLIER = {
        "deep_of": 1.8,      # Deep catches give runner very good chance to tag
        "middle_of": 1.5,    # Medium catches give runner good chance to tag
        "shallow_of": 1.2,   # Shallow OF catches - risky but possible for fast runners
    }

    # Depth zones considered outfield
    OUTFIELD_DEPTHS = ["homerun", "deep_of", "middle_of", "shallow_of"]

    # Hard-hit contact types (less reaction time for fielders)
    HARD_HIT_TYPES = ["barrel", "solid"]

    # Throw distances in feet between positions and bases
    THROW_DISTANCES = {
        # Infielders to bases
        ("pitcher", 1): 60,      # pitcher to first
        ("pitcher", 2): 67,      # pitcher to second
        ("pitcher", 3): 60,      # pitcher to third
        ("pitcher", 4): 60,      # pitcher to home
        ("catcher", 1): 90,      # catcher to first
        ("catcher", 2): 127,     # catcher to second
        ("catcher", 3): 90,      # catcher to third
        ("firstbase", 1): 0,     # first baseman at first
        ("firstbase", 2): 90,    # first baseman to second
        ("firstbase", 3): 127,   # first baseman to third
        ("firstbase", 4): 90,    # first baseman to home
        ("secondbase", 1): 90,   # second baseman to first
        ("secondbase", 2): 45,   # second baseman to second (covering)
        ("secondbase", 3): 90,   # second baseman to third
        ("secondbase", 4): 127,  # second baseman to home
        ("shortstop", 1): 90,    # shortstop to first
        ("shortstop", 2): 45,    # shortstop to second (covering)
        ("shortstop", 3): 90,    # shortstop to third
        ("shortstop", 4): 127,   # shortstop to home
        ("thirdbase", 1): 127,   # third baseman to first
        ("thirdbase", 2): 90,    # third baseman to second
        ("thirdbase", 3): 0,     # third baseman at third
        ("thirdbase", 4): 90,    # third baseman to home
        # Outfielders to bases
        ("leftfield", 1): 200,   # left field to first
        ("leftfield", 2): 180,   # left field to second
        ("leftfield", 3): 160,   # left field to third
        ("leftfield", 4): 220,   # left field to home
        ("centerfield", 1): 220, # center field to first
        ("centerfield", 2): 180, # center field to second
        ("centerfield", 3): 220, # center field to third
        ("centerfield", 4): 240, # center field to home
        ("rightfield", 1): 160,  # right field to first
        ("rightfield", 2): 180,  # right field to second
        ("rightfield", 3): 200,  # right field to third
        ("rightfield", 4): 220,  # right field to home
    }

    # Base positions for covering throws
    BASE_COVERAGE = {
        1: ["firstbase", "pitcher"],
        2: ["shortstop", "secondbase"],
        3: ["thirdbase", "shortstop"],
        4: ["catcher", "pitcher"],
    }

    @staticmethod
    def runner_time(runner: RunnerState, include_variance: bool = True) -> Tuple[float, float]:
        """
        Calculate time for runner to reach their target base.

        Args:
            runner: RunnerState with current_base, target_base, speed_rating, progress
            include_variance: Whether to include per-play variance (default True)

        Returns:
            Tuple of (time in seconds, variance applied)
        """
        base_key = (runner.current_base, runner.target_base)
        base_time = TimeCalculator.BASE_RUNNING_TIMES.get(base_key, 4.0)

        # Speed modifier: 50 rating = 1.0x, each point = 1%
        # 80 speed = 0.7x time (30% faster), 20 speed = 1.3x time (30% slower)
        speed_mod = 1.0 - ((runner.speed_rating - 50) * 0.01)

        # Account for progress already made
        remaining = 1.0 - runner.progress

        base_result = base_time * speed_mod * remaining

        # Add variance if requested
        variance = TimeCalculator.runner_variance() if include_variance else 0.0
        result = base_result + variance

        return max(result, 0.1), variance  # Floor at 0.1s

    @staticmethod
    def throw_time(fielder_pos: str, target_base: int, throw_power: float) -> float:
        """
        Calculate time for throw to reach target base.

        Args:
            fielder_pos: Position name of thrower
            target_base: Target base number (1-4, where 4 is home)
            throw_power: Thrower's throw power rating

        Returns:
            Time in seconds for throw to arrive
        """
        distance = TimeCalculator.THROW_DISTANCES.get(
            (fielder_pos, target_base), 100
        )

        # Base throw speed ~90 mph = 132 ft/s at rating 50
        # Higher rating = faster throw
        throw_speed = 132 * (throw_power / 50)

        return distance / throw_speed if throw_speed > 0 else 999

    @staticmethod
    def catch_transfer_time(fielder_player, is_force: bool) -> float:
        """
        Calculate time to catch ball and apply tag or touch base.

        Args:
            fielder_player: Player object catching the ball
            is_force: True if force play (just touch base), False if tag required

        Returns:
            Time in seconds for catch and tag/touch
        """
        base_time = 0.3 if is_force else 0.8  # Tags take longer

        # fieldcatch affects catch time
        catch_rating = getattr(fielder_player, 'fieldcatch', 50)
        catch_mod = 1.0 - ((catch_rating - 50) * 0.005)

        return base_time * catch_mod

    @staticmethod
    def reaction_time(fieldreact: float) -> float:
        """
        Calculate fielder reaction time based on fieldreact rating.

        Args:
            fieldreact: Player's fieldreact rating (1-99, baseline 50)

        Returns:
            Reaction time in seconds
            - fieldreact 80: ~0.2s (fast first step)
            - fieldreact 50: ~0.5s (average)
            - fieldreact 20: ~0.8s (slow to react)
        """
        tc = TimeCalculator.TIMING_CONSTANTS
        base = tc["base_reaction_time"]

        # Linear scale: each point away from 50 = 1% of range
        modifier = (50 - fieldreact) / 50
        reaction = base + (modifier * tc["reaction_time_range"] / 2)

        return max(reaction, 0.1)  # Floor at 0.1s

    @staticmethod
    def fieldspot_modifier(fieldspot: float) -> float:
        """
        Calculate reach time modifier based on fieldspot rating.

        Better fieldspot = better routes = faster arrival.
        Only applies to non-caught balls (HIT PATH).

        Args:
            fieldspot: Player's fieldspot rating (1-99, baseline 50)

        Returns:
            Multiplier for reach time (0.925 to 1.075 for ratings 80-20)
        """
        # 0.25% per point
        return 1.0 - ((fieldspot - 50) * 0.0025)

    @staticmethod
    def defense_variance() -> float:
        """
        Generate per-play variance for defense timing.
        Normal distribution with std dev ~0.1s (so ±0.2s is ~2 std devs).

        Returns:
            Variance in seconds (typically -0.2 to +0.2)
        """
        tc = TimeCalculator.TIMING_CONSTANTS
        variance = random.gauss(0, tc["defense_variance_std"])
        return max(-0.3, min(0.3, variance))  # Clamp to ±0.3s

    @staticmethod
    def runner_variance() -> float:
        """
        Generate per-play variance for runner timing.
        Normal distribution with std dev ~0.1s.

        Returns:
            Variance in seconds (typically -0.2 to +0.2)
        """
        tc = TimeCalculator.TIMING_CONSTANTS
        variance = random.gauss(0, tc["runner_variance_std"])
        return max(-0.3, min(0.3, variance))  # Clamp to ±0.3s

    @staticmethod
    def route_efficiency_modifier(baserunning: float) -> float:
        """
        Calculate base-to-base time modifier from route efficiency.

        Better baserunning = more efficient routes = faster times.

        Args:
            baserunning: Player's baserunning rating (1-99, baseline 50)

        Returns:
            Multiplier for base-to-base time
            - baserunning 80: ~0.95x (5% faster)
            - baserunning 50: 1.00x (baseline)
            - baserunning 20: ~1.05x (5% slower)
        """
        tc = TimeCalculator.TIMING_CONSTANTS
        return 1.0 - ((baserunning - 50) * tc["route_efficiency_per_point"])

    @staticmethod
    def runner_jump_bonus(basereaction: float) -> float:
        """
        Calculate time bonus/penalty from runner's reaction to contact.

        Better basereaction = quicker read = effective head start.

        Args:
            basereaction: Player's basereaction rating (1-99, baseline 50)

        Returns:
            Time bonus in seconds (positive = more time to advance)
            - basereaction 80: +0.3s head start
            - basereaction 50: +0.0s (baseline)
            - basereaction 20: -0.3s delayed start
        """
        tc = TimeCalculator.TIMING_CONSTANTS
        return (basereaction - 50) * tc["runner_jump_per_point"]

    @staticmethod
    def tag_up_delay(basereaction: float) -> float:
        """
        Calculate time for runner to read fly ball catch and begin sprint.

        Better basereaction = tags up faster after catch.

        Args:
            basereaction: Player's basereaction rating (1-99, baseline 50)

        Returns:
            Tag-up delay in seconds
            - basereaction 80: ~0.1s (quick read)
            - basereaction 50: ~0.3s (average)
            - basereaction 20: ~0.5s (slow read)
        """
        tc = TimeCalculator.TIMING_CONSTANTS
        base = tc["tag_up_delay_base"]
        # Linear scale: each point away from 50 adjusts delay
        modifier = (50 - basereaction) / 50
        delay = base + (modifier * tc["tag_up_delay_range"] / 2)
        return max(delay, 0.05)  # Floor at 0.05s

    @staticmethod
    def ball_travel_time(contact_type: str, depth: str) -> float:
        """
        Calculate time for batted ball to reach fielder.

        Args:
            contact_type: Type of contact (barrel, solid, flare, etc.)
            depth: Where ball lands (infield, shallow_of, deep_of, etc.)

        Returns:
            Time in seconds for ball to reach fielder
        """
        # Base times by contact type and depth
        # Grounders are faster to field, fly balls take longer
        ground_types = ["topped", "weak", "groundball"]
        air_types = ["barrel", "solid", "flare", "under"]

        if contact_type in ground_types:
            # Ground balls - quick to reach infielders
            if "of" in depth.lower():
                return 3.5  # Through to outfield
            else:
                return 1.5  # To infielders
        else:
            # Air balls
            if "deep" in depth.lower():
                return 4.0
            elif "shallow" in depth.lower():
                return 2.5
            else:
                return 3.0

    @staticmethod
    def get_covering_fielder(target_base: int, throwing_fielder_pos: str) -> str:
        """
        Determine which fielder covers the target base.

        Args:
            target_base: Base number (1-4)
            throwing_fielder_pos: Position of fielder making throw

        Returns:
            Position name of covering fielder
        """
        coverage = TimeCalculator.BASE_COVERAGE.get(target_base, ["pitcher"])

        # Return first option that isn't the thrower
        for pos in coverage:
            if pos != throwing_fielder_pos:
                return pos

        return coverage[0]  # Fallback

    # =========================================================================
    # PHYSICS-BASED TIMING METHODS - For XBH determination
    # =========================================================================

    @staticmethod
    def fielder_reach_time(depth: str, direction: str, fielder_pos: str,
                           contact_type: str, fielder_speed: float = 50) -> float:
        """
        Calculate time for fielder to reach ball after it lands.

        Accounts for:
        - Gap hits (ball between fielders)
        - Down the line hits
        - Ball over fielder's head (deep)
        - Fielder reaction/speed rating

        Args:
            depth: Where the ball lands (deep_of, middle_of, etc.)
            direction: Ball direction (center left, far right, etc.)
            fielder_pos: Position of primary fielder
            contact_type: Type of contact (barrel, flare, etc.)
            fielder_speed: Fielder's speed rating (default 50)

        Returns:
            Time in seconds for fielder to reach ball
        """
        tc = TimeCalculator.TIMING_CONSTANTS
        base_time = tc["base_reach_time"]

        # Check if this is a gap hit (ball between outfielders)
        is_gap_hit = False
        gap_fielders = TimeCalculator.GAP_DIRECTIONS.get(direction, [])
        if gap_fielders and fielder_pos in gap_fielders:
            is_gap_hit = True
            base_time += tc["gap_reach_bonus"]

        # Check if this is down the line
        is_line_hit = direction in TimeCalculator.LINE_DIRECTIONS
        if is_line_hit:
            base_time += tc["line_reach_bonus"]

        # Check if ball is over fielder's head (deep outfield)
        is_deep = "deep" in depth.lower()
        if is_deep:
            base_time += tc["deep_chase_bonus"]

        # Hard hit balls give fielders less reaction time
        if contact_type in TimeCalculator.HARD_HIT_TYPES:
            base_time += tc["hard_hit_bonus"]

        # Speed modifier: faster fielders reach ball quicker
        # 50 rating = 1.0x, each point = 0.5% change
        speed_mod = 1.0 - ((fielder_speed - 50) * 0.005)
        base_time *= max(speed_mod, 0.5)  # Cap at 50% reduction

        return base_time

    @staticmethod
    def ball_retrieval_time(contact_type: str, is_outfield: bool) -> float:
        """
        Time to pick up ball and set to throw.

        Ground balls that get through need chasing.
        Fly balls caught on run need plant time.

        Args:
            contact_type: Type of contact (barrel, topped, etc.)
            is_outfield: True if ball is in outfield

        Returns:
            Time in seconds to retrieve ball and prepare throw
        """
        tc = TimeCalculator.TIMING_CONSTANTS

        if is_outfield:
            return tc["outfield_retrieval"]
        else:
            return tc["infield_retrieval"]

    @staticmethod
    def total_field_time(contact_type: str, depth: str, direction: str,
                         fielder_pos: str, fielder_player,
                         include_variance: bool = True) -> Tuple[float, dict]:
        """
        Total time from bat contact until fielder can throw.

        This is the key method for determining XBH - it calculates
        the full time window during which runners can advance.

        NEW FORMULA:
        total_time = ball_travel + reaction + (reach × speed_mod × fieldspot_mod)
                     + retrieval + defense_variance

        Args:
            contact_type: Type of contact (barrel, flare, etc.)
            depth: Where ball lands (deep_of, middle_of, etc.)
            direction: Ball direction (center left, far right, etc.)
            fielder_pos: Position of primary fielder
            fielder_player: Player object for the fielder
            include_variance: Whether to include per-play variance (default True)

        Returns:
            Tuple of (total_time in seconds, components_dict for diagnostics)
        """
        # Get fielder attributes
        fielder_speed = getattr(fielder_player, 'speed', 50) if fielder_player else 50
        fielder_react = getattr(fielder_player, 'fieldreact', 50) if fielder_player else 50
        fielder_spot = getattr(fielder_player, 'fieldspot', 50) if fielder_player else 50

        # 1. Ball travel time
        ball_time = TimeCalculator.ball_travel_time(contact_type, depth)

        # 2. Reaction time (NEW - fieldreact based)
        react_time = TimeCalculator.reaction_time(fielder_react)

        # 3. Fielder reach time with speed modifier
        reach_time = TimeCalculator.fielder_reach_time(
            depth, direction, fielder_pos, contact_type, fielder_speed
        )

        # 4. Apply fieldspot modifier to reach time (NEW)
        fieldspot_mod = TimeCalculator.fieldspot_modifier(fielder_spot)
        reach_time_modified = reach_time * fieldspot_mod

        # 5. Ball retrieval time
        is_outfield = depth in TimeCalculator.OUTFIELD_DEPTHS
        retrieval_time = TimeCalculator.ball_retrieval_time(contact_type, is_outfield)

        # 6. Per-play variance (NEW)
        defense_var = TimeCalculator.defense_variance() if include_variance else 0.0

        total = ball_time + react_time + reach_time_modified + retrieval_time + defense_var

        # Build components dict for diagnostics
        components = {
            'ball_travel': round(ball_time, 3),
            'reaction_time': round(react_time, 3),
            'reach_time_base': round(reach_time, 3),
            'fieldspot_modifier': round(fieldspot_mod, 3),
            'reach_time_modified': round(reach_time_modified, 3),
            'retrieval_time': round(retrieval_time, 3),
            'defense_variance': round(defense_var, 3),
            'fielder_fieldreact': fielder_react,
            'fielder_fieldspot': fielder_spot,
            'fielder_speed': fielder_speed,
        }

        return max(total, 0.5), components  # Floor at 0.5s


# ============================================================================
# DEFENSE DECISION TREE - Makes strategic decisions for defense
# ============================================================================

class DefenseDecisionTree:
    """Makes strategic decisions for defense during a play."""

    # Minimum time margin (seconds) to attempt a play
    SAFE_MARGIN = 0.2

    @staticmethod
    def calculate_force_bases(runners: List[RunnerState]) -> Set[int]:
        """
        Calculate which bases have force plays.

        Force play exists when all bases behind are occupied (starting from home).
        Batter always forces to first. Runner on first forces to second, etc.

        Args:
            runners: List of RunnerState objects

        Returns:
            Set of base numbers where force plays apply
        """
        force_bases = set()
        occupied = {r.current_base for r in runners if not r.is_out}

        # Batter always forces to first
        if 0 in occupied:
            force_bases.add(1)

            # Check chain: 0->1->2->3
            if 1 in occupied:
                force_bases.add(2)
                if 2 in occupied:
                    force_bases.add(3)
                    if 3 in occupied:
                        force_bases.add(4)

        return force_bases

    @staticmethod
    def choose_target(play_state: PlayState, fielder: FielderState) -> Optional[Tuple[int, RunnerState]]:
        """
        Decide which base to throw to.

        Priority:
        1. Lead runner if out is achievable (maximize damage)
        2. Force play at nearest base with achievable out
        3. Batter-runner at first if achievable
        4. None if no play available

        Args:
            play_state: Current PlayState
            fielder: FielderState of fielder with ball

        Returns:
            Tuple of (target_base, runner) or None if no play
        """
        if not play_state.runners:
            return None

        # Get active runners (not out, still running)
        active_runners = [
            r for r in play_state.runners
            if not r.is_out and r.current_base < 4
        ]

        if not active_runners:
            return None

        best_target = None
        best_margin = -999
        best_runner = None

        # Sort by target base descending (lead runner first)
        for runner in sorted(active_runners, key=lambda r: r.target_base, reverse=True):
            target_base = runner.target_base

            # Skip if runner already reached base
            if runner.progress >= 1.0:
                continue

            # Calculate timing
            throw_time = TimeCalculator.throw_time(
                fielder.position, target_base, fielder.player.throwpower
            )

            # Add catch/transfer time
            is_force = target_base in play_state.force_bases
            catch_time = TimeCalculator.catch_transfer_time(fielder.player, is_force)

            total_defense_time = throw_time + catch_time
            runner_time, _ = TimeCalculator.runner_time(runner, include_variance=False)

            # Margin = how much longer runner takes than defense
            # Positive margin = defense beats runner
            margin = runner_time - total_defense_time

            # Need positive margin for out
            if margin > DefenseDecisionTree.SAFE_MARGIN and margin > best_margin:
                best_target = target_base
                best_margin = margin
                best_runner = runner

        if best_target is not None:
            return (best_target, best_runner)

        return None

    @staticmethod
    def runner_should_advance(runner: RunnerState, play_state: PlayState) -> bool:
        """
        Decide if a runner should try to advance.

        Args:
            runner: The runner considering advancing
            play_state: Current play state

        Returns:
            True if runner should advance, False if should hold
        """
        # Forced runners MUST advance
        if runner.is_forced:
            return True

        # If ball not yet fielded, runners advance
        if not play_state.ball_holder:
            return True

        # Calculate if safe to advance
        throw_time = TimeCalculator.throw_time(
            play_state.ball_holder.position,
            runner.target_base,
            play_state.ball_holder.player.throwpower
        )

        is_force = runner.target_base in play_state.force_bases
        catch_time = TimeCalculator.catch_transfer_time(
            play_state.ball_holder.player, is_force
        )

        total_defense_time = throw_time + catch_time
        runner_time, _ = TimeCalculator.runner_time(runner, include_variance=False)

        # Advance if runner beats throw by comfortable margin
        return runner_time < total_defense_time - 0.3

    @staticmethod
    def update_force_state_after_out(play_state: PlayState, out_base: int):
        """
        Update force bases after recording an out.

        When a runner is out, the force situation can change.

        Args:
            play_state: Current PlayState (modified in place)
            out_base: Base where out was recorded
        """
        # Recalculate forces based on remaining runners
        play_state.force_bases = DefenseDecisionTree.calculate_force_bases(
            [r for r in play_state.runners if not r.is_out]
        )

    @staticmethod
    def has_remaining_play(play_state: PlayState, current_fielder: FielderState) -> bool:
        """
        Check if defense can make another play after recording an out.

        Args:
            play_state: Current PlayState
            current_fielder: Fielder who just caught the ball

        Returns:
            True if another out is possible
        """
        result = DefenseDecisionTree.choose_target(play_state, current_fielder)
        return result is not None


class fielding():
    # Enable timing diagnostics for tuning analysis
    ENABLE_TIMING_DIAGNOSTICS = True

    # Default distance weights for each contact type (fallback when not in config)
    # Order: homerun, deep_of, middle_of, shallow_of, deep_if, middle_if, shallow_if, mound, catcher
    DEFAULT_DISTWEIGHTS = {
        "barrel": [0.15, 0.35, 0.25, 0.15, 0.05, 0.03, 0.01, 0.01, 0.0],
        "solid": [0.05, 0.25, 0.30, 0.25, 0.08, 0.04, 0.02, 0.01, 0.0],
        "flare": [0.0, 0.10, 0.25, 0.35, 0.15, 0.10, 0.03, 0.02, 0.0],
        "burner": [0.0, 0.05, 0.15, 0.30, 0.20, 0.20, 0.07, 0.03, 0.0],
        "under": [0.0, 0.15, 0.35, 0.35, 0.10, 0.03, 0.01, 0.01, 0.0],
        "topped": [0.0, 0.0, 0.05, 0.10, 0.15, 0.35, 0.25, 0.08, 0.02],
        "weak": [0.0, 0.0, 0.02, 0.08, 0.10, 0.30, 0.35, 0.12, 0.03],
    }

    # Situation categories derived from depth + direction
    GAP_DIRECTIONS = ["center left", "center right"]
    LINE_DIRECTIONS = ["far left", "far right"]
    OUTFIELD_DEPTHS = ["deep_of", "middle_of", "shallow_of"]
    INFIELD_DEPTHS = ["deep_if", "middle_if", "shallow_if", "mound", "catcher"]

    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.test = self.gamestate.game.baselines.threestepaway
        self.distweights = self.gamestate.game.baselines.distweights
        self.distoutcomes = self.gamestate.game.baselines.distoutcomes
        self.defensivealignment = self.gamestate.game.baselines.defensivealignment
        # Load catch_rates (new system)
        self.catch_rates = getattr(
            self.gamestate.game.baselines, 'catch_rates', {}
        )
        self.errorlist = []
        self.defensiveactions = []
        self.catch_probability = None  # Set in _is_out_play if applicable
        self.timing_diagnostics = None  # Set if ENABLE_TIMING_DIAGNOSTICS is True

        self.contacttype = self.gamestate.outcome[0]
        self.direction = self.gamestate.outcome[1]

        # Determine what type of batted ball and where it goes (preserved logic)
        # Use fallback weights if contact type missing or weights sum to zero
        self.specificweights = self._get_distweights(self.contacttype)
        self.depth = fielding.PickDepth(self)
        self.fieldingdefender = fielding.PickDefender(self)
        self.airball_bool = fielding.AirballBool(self.contacttype)

        # Derive situation category from depth + direction
        self.situation = self._derive_situation()

        # Initialize play state with new decision tree system
        self.play_state = self._initialize_play_state()

        # Process the play using decision tree
        self.batted_ball_outcome = self._process_play()

        # Convert play state back to base_situation format for compatibility
        self.base_situation = self._build_base_situation()

        # Build the defenseoutcome tuple (extended with timing diagnostics)
        self.defenseoutcome = (
            self.contacttype,
            self.direction,
            self.fieldingdefender,
            self.batted_ball_outcome,
            self.base_situation,
            self.errorlist,
            self.defensiveactions,
            self.timing_diagnostics  # New: timing data for tuning analysis
        )

    def _initialize_play_state(self) -> PlayState:
        """Initialize PlayState from game state."""
        game = self.gamestate.game
        batter = game.battingteam.currentbatter

        runners = []

        # Add batter as runner from home
        if batter:
            runners.append(RunnerState(
                player_id=batter.id,
                player=batter,
                current_base=0,
                target_base=1,
                progress=0.0,
                is_forced=True,  # Batter always forced to run
                speed_rating=getattr(batter, 'speed', 50),
                basereaction=getattr(batter, 'basereaction', 50),
                baserunning=getattr(batter, 'baserunning', 50),
                earned_run=True
            ))

        # Add runners on bases
        if game.on_firstbase:
            runners.append(RunnerState(
                player_id=game.on_firstbase.id,
                player=game.on_firstbase,
                current_base=1,
                target_base=2,
                progress=0.0,
                is_forced=True,  # Forced by batter
                speed_rating=getattr(game.on_firstbase, 'speed', 50),
                basereaction=getattr(game.on_firstbase, 'basereaction', 50),
                baserunning=getattr(game.on_firstbase, 'baserunning', 50),
                earned_run=True
            ))

        if game.on_secondbase:
            # Forced only if first base occupied
            is_forced = game.on_firstbase is not None
            runners.append(RunnerState(
                player_id=game.on_secondbase.id,
                player=game.on_secondbase,
                current_base=2,
                target_base=3,
                progress=0.0,
                is_forced=is_forced,
                speed_rating=getattr(game.on_secondbase, 'speed', 50),
                basereaction=getattr(game.on_secondbase, 'basereaction', 50),
                baserunning=getattr(game.on_secondbase, 'baserunning', 50),
                earned_run=True
            ))

        if game.on_thirdbase:
            # Forced only if first and second occupied
            is_forced = game.on_firstbase is not None and game.on_secondbase is not None
            runners.append(RunnerState(
                player_id=game.on_thirdbase.id,
                player=game.on_thirdbase,
                current_base=3,
                target_base=4,
                progress=0.0,
                is_forced=is_forced,
                speed_rating=getattr(game.on_thirdbase, 'speed', 50),
                basereaction=getattr(game.on_thirdbase, 'basereaction', 50),
                baserunning=getattr(game.on_thirdbase, 'baserunning', 50),
                earned_run=True
            ))

        # Calculate initial force bases
        force_bases = DefenseDecisionTree.calculate_force_bases(runners)

        return PlayState(
            ball_location=self.depth,
            ball_holder=None,
            runners=runners,
            outs_this_play=0,
            force_bases=force_bases,
            play_active=True,
            contact_type=self.contacttype
        )

    def _is_out_play(self) -> bool:
        """
        Determine if the defense makes the play using catch_rates config.

        This applies to ALL contact types:
        - Fly balls: probability fielder catches the ball
        - Ground balls: probability fielder fields cleanly and makes the throw

        The catch_rates config provides tunable out probabilities per
        contact type and situation (derived from depth + direction).

        Returns:
            True if defense makes the play (pending error checks), False otherwise
        """
        # If depth is homerun, it's gone (handled separately)
        if self.depth == 'homerun':
            return False

        # Look up out rate from config
        # Format: catch_rates[contacttype][situation] = probability
        contact_rates = self.catch_rates.get(self.contacttype, {})
        out_probability = contact_rates.get(self.situation)

        # If no config found, use sensible defaults based on situation
        if out_probability is None:
            DEFAULT_CATCH_RATES = {
                "deep_gap": 0.30,
                "gap": 0.50,
                "deep_line": 0.45,
                "line": 0.55,
                "deep": 0.60,
                "routine_of": 0.92,
                "routine_if": 0.97,
            }
            out_probability = DEFAULT_CATCH_RATES.get(self.situation, 0.70)

        # Store probability for debugging output
        self.catch_probability = out_probability

        # Roll against out probability
        return random.random() < out_probability

    def _process_play(self) -> str:
        """
        Process the entire play using decision tree logic.

        Uses catch_rates to determine if defense makes the play:
        - All contact types use catch_rates for out probability
        - Fly balls: error check on catch
        - Ground balls: error check on throw and catch
        - Non-outs use physics timing for XBH determination

        Returns:
            Final outcome string (out, single, double, triple, homerun)
        """
        # Handle home runs immediately
        if self.depth == 'homerun':
            self._handle_homerun()
            return 'homerun'

        # Create fielder state for primary fielder
        if self.fieldingdefender:
            fielder_state = FielderState(
                position=self.fieldingdefender.lineup,
                player=self.fieldingdefender,
                has_ball=False,
                location=self.depth
            )
        else:
            # No fielder (shouldn't happen except for HR)
            return 'single'

        # Calculate field time for runner advancement (now returns tuple with components)
        total_time, field_components = TimeCalculator.total_field_time(
            self.contacttype,
            self.depth,
            self.direction,
            fielder_state.position,
            fielder_state.player,
            include_variance=True
        )

        # Determine if defense makes the play (applies to ALL contact types)
        is_out_attempt = self._is_out_play()

        if is_out_attempt:
            # DEFENSE MAKES THE PLAY - check for errors
            if self.airball_bool:
                # FLY BALL - runners advance during flight (tag up rules)
                ball_time = TimeCalculator.ball_travel_time(self.contacttype, self.depth)
                self._advance_runners_during_flight(ball_time)

                # Check for catching error only
                error_on_play, d_action = Error_Catch(self, None, self.fieldingdefender)
                self.defensiveactions.append(d_action)
            else:
                # GROUND BALL - runners advance while ball is fielded
                self._advance_non_batter_runners(total_time)

                # Check for throwing AND catching errors
                first_baseman = self.gamestate.game.pitchingteam.firstbase
                error_throw, error_catch, d_action = Error_Throw_Catch(
                    self, self.fieldingdefender, first_baseman
                )
                self.defensiveactions.append(d_action)
                error_on_play = error_throw or error_catch

            if error_on_play:
                # Error - ball gets away, becomes a hit
                self._mark_runs_unearned()
                self.errorlist.append(self.fieldingdefender)
                self._advance_all_runners(1)  # Extra base on error
                return 'single'
            else:
                # Successful play - batter is out
                fielder_state.has_ball = True
                self.play_state.ball_holder = fielder_state

                batter_runner = next(
                    (r for r in self.play_state.runners if r.current_base == 0),
                    None
                )
                if batter_runner:
                    batter_runner.is_out = True
                    self.play_state.outs_this_play += 1
                    self.gamestate.game.outcount += 1

                    if self.airball_bool:
                        self.defensiveactions.append("out at bat (fly)")
                        # Award putout to fielder who caught
                        if hasattr(self.fieldingdefender, 'fieldingstats'):
                            self.fieldingdefender.fieldingstats.Adder("putouts", 1)

                        # Handle tag-up opportunities for runners on base
                        # (sac flies, advancing on deep flies)
                        ball_time = TimeCalculator.ball_travel_time(self.contacttype, self.depth)
                        self._handle_tag_up(ball_time)
                    else:
                        self.defensiveactions.append("out at 1st (ground ball)")
                        # Award putout to first baseman, assist to fielder
                        first_baseman = self.gamestate.game.pitchingteam.firstbase
                        if hasattr(first_baseman, 'fieldingstats'):
                            first_baseman.fieldingstats.Adder("putouts", 1)
                        if hasattr(self.fieldingdefender, 'fieldingstats'):
                            self.fieldingdefender.fieldingstats.Adder("assists", 1)

                    # Update force state
                    DefenseDecisionTree.update_force_state_after_out(
                        self.play_state, 1
                    )

                # Check if more outs possible (tag up or double play)
                if self._can_continue_play():
                    self._defense_loop()

                return 'out'
        else:
            # HIT PLAY - Defense doesn't make the play
            # Advance runners for the FULL time window
            # This is what allows doubles and triples to occur naturally

            # Capture batter speed BEFORE advancement for diagnostics
            batter_runner = next(
                (r for r in self.play_state.runners if r.current_base == 0),
                None
            )
            batter_speed = batter_runner.speed_rating if batter_runner else 50

            # First, advance ALL runners during field time
            self._advance_runners_for_time(total_time)

            # On outfield hits, non-batter runners get EXTRA time during the throw
            # This is critical for R2 scoring on singles, R1 advancing to 3rd, etc.
            # The batter's advancement is limited by throw to their target base,
            # but existing runners can keep advancing during the throw home
            is_outfield_hit = self.depth in TimeCalculator.OUTFIELD_DEPTHS
            if is_outfield_hit:
                # Calculate throw time from outfielder to home (longest throw)
                throw_time_home = TimeCalculator.throw_time(
                    fielder_state.position, 4, fielder_state.player.throwpower
                )
                # Non-batter runners advance during the full throw time
                # They keep running until the ball reaches the infield
                self._advance_non_batter_runners(throw_time_home)

            # Now fielder has the ball
            fielder_state.has_ball = True
            self.play_state.ball_holder = fielder_state

            # Capture timing diagnostics BEFORE defense loop
            if fielding.ENABLE_TIMING_DIAGNOSTICS and batter_runner:
                # Calculate what the throw-out timing would be
                throw_time = TimeCalculator.throw_time(
                    fielder_state.position, 1, fielder_state.player.throwpower
                )
                catch_time = TimeCalculator.catch_transfer_time(
                    self.gamestate.game.pitchingteam.firstbase, True
                )
                defense_time = throw_time + catch_time
                runner_time_remaining, runner_var = TimeCalculator.runner_time(batter_runner, include_variance=True)

                # Calculate extra time given to non-batter runners on outfield hits
                extra_runner_time = 0
                if is_outfield_hit:
                    throw_time_home = TimeCalculator.throw_time(
                        fielder_state.position, 4, fielder_state.player.throwpower
                    )
                    extra_runner_time = throw_time_home

                self.timing_diagnostics = {
                    # Batter/runner info
                    'batter_speed': batter_speed,
                    'runner_progress': round(batter_runner.progress, 3),
                    'runner_time_remaining': round(runner_time_remaining, 3),
                    'runner_variance': round(runner_var, 3),

                    # Field time breakdown (from field_components)
                    'field_time': round(total_time, 3),
                    'ball_travel': field_components.get('ball_travel', 0),
                    'reaction_time': field_components.get('reaction_time', 0),
                    'reach_time_base': field_components.get('reach_time_base', 0),
                    'fieldspot_modifier': field_components.get('fieldspot_modifier', 1.0),
                    'reach_time_modified': field_components.get('reach_time_modified', 0),
                    'retrieval_time': field_components.get('retrieval_time', 0),
                    'defense_variance': field_components.get('defense_variance', 0),

                    # Extra advancement time for non-batter runners (throw time)
                    'extra_runner_time': round(extra_runner_time, 3),
                    'total_runner_time': round(total_time + extra_runner_time, 3),

                    # Fielder attributes
                    'fielder_position': fielder_state.position,
                    'fielder_throw_power': getattr(fielder_state.player, 'throwpower', 50),
                    'fielder_fieldreact': field_components.get('fielder_fieldreact', 50),
                    'fielder_fieldspot': field_components.get('fielder_fieldspot', 50),
                    'fielder_speed': field_components.get('fielder_speed', 50),

                    # Throw timing
                    'throw_time': round(throw_time, 3),
                    'catch_time': round(catch_time, 3),
                    'defense_total': round(defense_time, 3),

                    # Final margin calculation
                    'timing_margin': round(runner_time_remaining - defense_time, 3),
                    'would_be_out': runner_time_remaining > defense_time,
                }

            # Run the defense loop for any throw plays on runners
            self._defense_loop()

            # Determine final outcome based on where batter ended up
            return self._determine_final_outcome()

    def _defense_loop(self):
        """
        Main decision loop - continues until no play available or 3 outs.
        """
        max_iterations = 5  # Safety limit
        iteration = 0

        while self.play_state.play_active and iteration < max_iterations:
            iteration += 1

            # Check if we have max outs
            if self.play_state.outs_this_play >= 3:
                self.play_state.play_active = False
                break

            # Defense decides where to throw
            target_result = DefenseDecisionTree.choose_target(
                self.play_state,
                self.play_state.ball_holder
            )

            if target_result is None:
                # No play available - hold ball
                self.defensiveactions.append(
                    f"{self.play_state.ball_holder.position} holds"
                )
                self.play_state.play_active = False
                break

            target_base, target_runner = target_result

            # Attempt the throw
            throw_result = self._attempt_throw(target_base, target_runner)

            if throw_result == "error":
                # Error on throw - runners advance
                self._mark_runs_unearned()
                self._advance_all_runners(1)
                self.play_state.play_active = False

            elif throw_result == "out":
                # Out recorded
                target_runner.is_out = True
                self.play_state.outs_this_play += 1
                self.gamestate.game.outcount += 1
                self.defensiveactions.append(f"out at {target_base}")

                # Update force state after out
                DefenseDecisionTree.update_force_state_after_out(
                    self.play_state, target_base
                )

                # Check for more plays (double/triple play)
                if not DefenseDecisionTree.has_remaining_play(
                    self.play_state, self.play_state.ball_holder
                ):
                    self.play_state.play_active = False

            else:
                # Runner safe
                self.defensiveactions.append(f"safe at {target_base}")
                target_runner.progress = 1.0
                target_runner.current_base = target_base
                self.play_state.play_active = False

    def _attempt_throw(self, target_base: int, target_runner: RunnerState) -> str:
        """
        Attempt a throw to a base.

        Returns:
            "out", "safe", or "error"
        """
        # Store thrower for assist tracking
        thrower = self.play_state.ball_holder.player

        # Get covering fielder
        covering_pos = TimeCalculator.get_covering_fielder(
            target_base,
            self.play_state.ball_holder.position
        )

        try:
            covering_player = [
                p for p in self.gamestate.game.pitchingteam.battinglist
                if p.lineup == covering_pos
            ][0]
        except (IndexError, AttributeError):
            covering_player = self.gamestate.game.pitchingteam.currentpitcher

        # Check for throwing error
        throw_error, throw_action = Error_Throw(
            self,
            self.play_state.ball_holder.player,
            covering_player
        )

        if throw_error:
            self.errorlist.append(f"Throwing error by {self.play_state.ball_holder.position}")
            self.defensiveactions.append(throw_action)
            return "error"

        # Check for catching error
        catch_error, catch_action = Error_Catch(self, self.play_state.ball_holder.player, covering_player)
        self.defensiveactions.append(f"{throw_action} {catch_action}")

        if catch_error:
            self.errorlist.append(f"Catching error by {covering_pos}")
            return "error"

        # Calculate timing
        throw_time = TimeCalculator.throw_time(
            self.play_state.ball_holder.position,
            target_base,
            self.play_state.ball_holder.player.throwpower
        )

        is_force = target_base in self.play_state.force_bases
        catch_time = TimeCalculator.catch_transfer_time(covering_player, is_force)

        total_defense_time = throw_time + catch_time
        runner_time, runner_var = TimeCalculator.runner_time(target_runner, include_variance=True)

        # Update ball holder to catching fielder
        self.play_state.ball_holder = FielderState(
            position=covering_pos,
            player=covering_player,
            has_ball=True,
            location=f"base_{target_base}"
        )
        self.fieldingdefender = covering_player

        # Determine out or safe
        if total_defense_time < runner_time:
            # Out recorded - award assist to thrower, putout to catcher
            if hasattr(thrower, 'fieldingstats'):
                thrower.fieldingstats.Adder("assists", 1)
            if hasattr(covering_player, 'fieldingstats'):
                covering_player.fieldingstats.Adder("putouts", 1)
            return "out"
        else:
            return "safe"

    def _advance_runners_during_flight(self, flight_time: float):
        """Advance runners based on ball flight time."""
        for runner in self.play_state.runners:
            if runner.is_out:
                continue

            # Calculate how much progress runner makes during ball flight
            base_time = TimeCalculator.BASE_RUNNING_TIMES.get(
                (runner.current_base, runner.target_base), 4.0
            )
            speed_mod = 1.0 - ((runner.speed_rating - 50) * 0.01)
            runner_base_time = base_time * speed_mod

            # Progress is portion of base-to-base completed
            if runner_base_time > 0:
                progress = min(flight_time / runner_base_time, 1.0)
                runner.progress = progress

                # If runner completed the base, advance them
                if progress >= 1.0 and runner.target_base <= 4:
                    runner.current_base = runner.target_base
                    if runner.target_base < 4:
                        runner.target_base += 1
                        runner.progress = 0.0

    def _advance_runners_for_time(self, available_time: float):
        """
        Advance runners continuously through available time window.

        This is the key method for physics-based XBH determination.
        Runners keep moving until:
        - They score (base 4)
        - Time runs out
        - They're tagged out

        This allows runners to reach 2nd, 3rd, or even score during
        the time it takes the fielder to retrieve and throw.

        Now includes:
        - Jump bonus from basereaction (faster reaction = more effective time)
        - Route efficiency from baserunning (better routes = faster base-to-base)

        Args:
            available_time: Total time in seconds that runners can advance
        """
        for runner in self.play_state.runners:
            if runner.is_out:
                continue

            # Apply jump bonus based on basereaction
            # High basereaction = runner gets a head start (more effective time)
            jump_bonus = TimeCalculator.runner_jump_bonus(runner.basereaction)
            time_remaining = available_time + jump_bonus

            # Get route efficiency modifier based on baserunning
            route_mod = TimeCalculator.route_efficiency_modifier(runner.baserunning)

            while time_remaining > 0 and runner.current_base < 4:
                # Calculate time to next base
                base_key = (runner.current_base, runner.target_base)
                base_time = TimeCalculator.BASE_RUNNING_TIMES.get(base_key, 4.0)

                # Speed modifier: 50 rating = 1.0x, each point = 1%
                # 80 speed = 0.7x time (30% faster), 20 speed = 1.3x time
                speed_mod = 1.0 - ((runner.speed_rating - 50) * 0.01)
                speed_mod = max(speed_mod, 0.5)  # Cap at 50% faster

                # Time needed to complete remaining progress to next base
                # Now includes route efficiency modifier
                time_to_next = base_time * speed_mod * route_mod * (1 - runner.progress)

                if time_remaining >= time_to_next:
                    # Runner makes it to next base
                    runner.current_base = runner.target_base
                    runner.progress = 0.0
                    time_remaining -= time_to_next

                    # Set up for next base if not scored
                    if runner.current_base < 4:
                        runner.target_base = runner.current_base + 1
                else:
                    # Partial progress toward next base
                    effective_base_time = base_time * speed_mod * route_mod
                    if effective_base_time > 0:
                        progress_made = time_remaining / effective_base_time
                        runner.progress += progress_made
                        runner.progress = min(runner.progress, 0.99)  # Don't complete base
                    time_remaining = 0

    def _advance_all_runners(self, bases: int):
        """Advance all runners by specified number of bases."""
        for runner in self.play_state.runners:
            if runner.is_out:
                continue

            runner.current_base = min(runner.current_base + bases, 4)
            runner.target_base = min(runner.current_base + 1, 4)
            runner.progress = 1.0 if runner.current_base == runner.target_base else 0.0

    def _handle_homerun(self):
        """Handle home run - all runners score."""
        for runner in self.play_state.runners:
            runner.current_base = 4  # Scored
            runner.target_base = 4
            runner.progress = 1.0
        self.defensiveactions.append("home run")

    def _mark_runs_unearned(self):
        """Mark all potential runs as unearned due to error."""
        for runner in self.play_state.runners:
            runner.earned_run = False

    def _can_continue_play(self) -> bool:
        """Check if defense can make more plays."""
        if not self.play_state.ball_holder:
            return False
        if self.play_state.outs_this_play >= 3:
            return False
        return DefenseDecisionTree.has_remaining_play(
            self.play_state,
            self.play_state.ball_holder
        )

    def _determine_final_outcome(self) -> str:
        """Determine the final outcome based on play state."""
        # If any outs recorded, it's an out play
        if self.play_state.outs_this_play > 0:
            return 'out'

        # Find where the batter ended up
        batter_runner = next(
            (r for r in self.play_state.runners if r.player_id == self.gamestate.game.battingteam.currentbatter.id),
            None
        )

        if batter_runner:
            if batter_runner.current_base >= 4:
                return 'homerun'  # Inside the park
            elif batter_runner.current_base == 3:
                return 'triple'
            elif batter_runner.current_base == 2:
                return 'double'
            else:
                return 'single'

        # Fallback (should never reach here in normal play)
        return 'single'

    def _advance_non_batter_runners(self, available_time: float):
        """
        Advance runners other than the batter for the given time.

        Used after a ground ball out - other runners still advance
        during the play.

        Now includes:
        - Jump bonus from basereaction (faster reaction = more effective time)
        - Route efficiency from baserunning (better routes = faster base-to-base)

        Args:
            available_time: Time in seconds runners can advance
        """
        for runner in self.play_state.runners:
            if runner.is_out:
                continue
            # Skip the batter (current_base == 0 or already marked out)
            if runner.current_base == 0:
                continue

            # Apply jump bonus based on basereaction
            jump_bonus = TimeCalculator.runner_jump_bonus(runner.basereaction)
            time_remaining = available_time + jump_bonus

            # Get route efficiency modifier based on baserunning
            route_mod = TimeCalculator.route_efficiency_modifier(runner.baserunning)

            while time_remaining > 0 and runner.current_base < 4:
                base_key = (runner.current_base, runner.target_base)
                base_time = TimeCalculator.BASE_RUNNING_TIMES.get(base_key, 4.0)

                speed_mod = 1.0 - ((runner.speed_rating - 50) * 0.01)
                speed_mod = max(speed_mod, 0.5)

                # Include route efficiency modifier
                time_to_next = base_time * speed_mod * route_mod * (1 - runner.progress)

                if time_remaining >= time_to_next:
                    runner.current_base = runner.target_base
                    runner.progress = 0.0
                    time_remaining -= time_to_next

                    if runner.current_base < 4:
                        runner.target_base = runner.current_base + 1
                else:
                    effective_base_time = base_time * speed_mod * route_mod
                    if effective_base_time > 0:
                        progress_made = time_remaining / effective_base_time
                        runner.progress += progress_made
                        runner.progress = min(runner.progress, 0.99)
                    break

    def _handle_tag_up(self, ball_flight_time: float):
        """
        Handle tag-up opportunities after a fly ball catch.

        Runners who can tag up and beat the throw will advance.
        Evaluated from lead runner backward (3rd → 2nd → 1st) to prevent
        invalid states like R2 staying while R1 advances past them.

        Only applies when:
        - Less than 2 outs before the catch
        - Fly ball caught in deep enough territory (deep_of, middle_of)

        Args:
            ball_flight_time: Time the ball was in the air (affects tag timing)
        """
        # Only allow tag-up on deep enough flies
        if self.depth not in TimeCalculator.TAG_UP_DEPTHS:
            # DEBUG
            # print(f"TAG-UP: depth {self.depth} not in {TimeCalculator.TAG_UP_DEPTHS}")
            return

        # Need less than 3 outs to tag up (the fly out just added one)
        current_outs = self.gamestate.game.currentouts + self.play_state.outs_this_play
        if current_outs >= 3:
            # DEBUG
            # print(f"TAG-UP: too many outs ({current_outs})")
            return

        # Get the outfielder who caught the ball (will throw home or to base)
        catcher_player = self.gamestate.game.pitchingteam.catcher
        fielder_pos = self.fieldingdefender.lineup if self.fieldingdefender else "centerfield"
        fielder_throw_power = getattr(self.fieldingdefender, 'throwpower', 50) if self.fieldingdefender else 50

        # Sort runners by current base (descending) to evaluate lead runners first
        # This prevents R2 from staying while R1 advances past them
        eligible_runners = [
            r for r in self.play_state.runners
            if not r.is_out and r.current_base > 0 and r.current_base < 4
        ]
        eligible_runners.sort(key=lambda r: r.current_base, reverse=True)

        # Track which bases become blocked (runner ahead didn't advance)
        blocked_bases = set()

        for runner in eligible_runners:
            target_base = runner.current_base + 1

            # Can't advance if the base ahead is blocked
            if target_base in blocked_bases:
                blocked_bases.add(runner.current_base)  # This base now blocks runners behind
                continue

            # Calculate tag-up timing
            # 1. Return time - if runner went partway during flight, they need to get back
            #    In reality, runners on fly balls don't run full speed - they go partway
            #    and freeze to see if it's caught. Cap progress at 0.4 (40% of the way)
            #    for more realistic return times.
            base_key = (runner.current_base, runner.target_base)
            base_time = TimeCalculator.BASE_RUNNING_TIMES.get(base_key, 4.0)
            speed_mod = 1.0 - ((runner.speed_rating - 50) * 0.01)
            speed_mod = max(speed_mod, 0.5)
            route_mod = TimeCalculator.route_efficiency_modifier(runner.baserunning)

            # Cap progress for tag-up - runners don't run full speed on fly balls
            effective_progress = min(runner.progress, 0.4)
            return_time = base_time * speed_mod * route_mod * effective_progress

            # 2. Tag-up delay - time to read the catch and start running
            tag_delay = TimeCalculator.tag_up_delay(runner.basereaction)

            # 3. Sprint time to next base (full base-to-base)
            sprint_time = base_time * speed_mod * route_mod

            # Total runner time = return + tag delay + sprint
            total_runner_time = return_time + tag_delay + sprint_time

            # Calculate defense time (throw from outfielder to target base)
            # Apply depth multiplier - catches at middle_of/deep_of are further from home
            base_throw_time = TimeCalculator.throw_time(fielder_pos, target_base, fielder_throw_power)
            depth_mult = TimeCalculator.TAG_UP_DEPTH_MULTIPLIER.get(self.depth, 1.0)
            throw_time = base_throw_time * depth_mult

            # Receiver at target base
            if target_base == 4:
                receiver = catcher_player
            elif target_base == 3:
                receiver = self.gamestate.game.pitchingteam.thirdbase
            elif target_base == 2:
                receiver = self.gamestate.game.pitchingteam.shortstop
            else:
                receiver = self.gamestate.game.pitchingteam.firstbase

            catch_time = TimeCalculator.catch_transfer_time(receiver, is_force=False)
            total_defense_time = throw_time + catch_time

            # Decision: Does the runner attempt the tag-up?
            # High baserunning = better at reading if they can make it
            # Add some margin based on baserunning for decision quality
            decision_margin = (runner.baserunning - 50) * 0.005  # ±0.15s at 80/20

            # Runner attempts if they think they can beat the throw
            margin = total_defense_time - total_runner_time + decision_margin

            if margin > 0.1:  # Safe margin - definitely go
                # Runner advances successfully
                runner.current_base = target_base
                runner.target_base = min(target_base + 1, 4)
                runner.progress = 0.0

                if target_base == 4:
                    self.defensiveactions.append(f"scores on sac fly")
                else:
                    self.defensiveactions.append(f"tags to {target_base}")
            elif margin > -0.2:
                # Close play - add variance to determine outcome
                # High baserunning reduces risk of bad read
                variance = TimeCalculator.runner_variance()
                adjusted_margin = margin + variance

                if adjusted_margin > 0:
                    # Runner makes it
                    runner.current_base = target_base
                    runner.target_base = min(target_base + 1, 4)
                    runner.progress = 0.0

                    if target_base == 4:
                        self.defensiveactions.append(f"scores on sac fly (close)")
                    else:
                        self.defensiveactions.append(f"tags to {target_base} (close)")
                else:
                    # Runner held or thrown out (for now, just hold)
                    # Could add thrown out logic later
                    blocked_bases.add(runner.current_base)
            else:
                # Not worth the risk - runner stays
                blocked_bases.add(runner.current_base)

            # Reset runner progress (they've returned to base after the catch)
            runner.progress = 0.0

    def _build_base_situation(self) -> list:
        """
        Convert play state to base_situation format.
        Format: [firstbase_player, secondbase_player, thirdbase_player, [scored_players]]
        """
        first = None
        second = None
        third = None
        scored = []

        for runner in self.play_state.runners:
            if runner.is_out:
                continue

            if runner.current_base == 1:
                first = runner.player
            elif runner.current_base == 2:
                second = runner.player
            elif runner.current_base == 3:
                third = runner.player
            elif runner.current_base >= 4:
                scored.append(runner.player)

        return [first, second, third, scored]

    def _get_distweights(self, contacttype: str) -> list:
        """
        Get distance weights for a contact type with fallback to defaults.

        Args:
            contacttype: The type of contact (barrel, solid, flare, etc.)

        Returns:
            List of weights for distance outcomes
        """
        # Try to get from config
        weights = self.distweights.get(contacttype)

        # Check if weights exist and sum to more than zero
        if weights and sum(weights) > 0:
            return weights

        # Fall back to defaults
        default = fielding.DEFAULT_DISTWEIGHTS.get(contacttype)
        if default:
            return default

        # Ultimate fallback - generic weights favoring middle outcomes
        return [0.05, 0.15, 0.25, 0.25, 0.12, 0.10, 0.05, 0.02, 0.01]

    def _derive_situation(self) -> str:
        """
        Derive situation category from depth + direction for catch_rates lookup.

        Situation categories:
        - deep_gap: Deep outfield + gap direction (hardest to catch)
        - gap: Non-deep outfield + gap direction
        - deep_line: Deep outfield + line direction
        - line: Non-deep outfield + line direction
        - deep: Deep outfield + straight-away
        - routine_of: Shallow/middle outfield + straight-away
        - routine_if: Infield fly ball

        Returns:
            Situation category string
        """
        is_gap = self.direction in fielding.GAP_DIRECTIONS
        is_line = self.direction in fielding.LINE_DIRECTIONS
        is_deep = self.depth == "deep_of"
        is_outfield = self.depth in fielding.OUTFIELD_DEPTHS
        is_infield = self.depth in fielding.INFIELD_DEPTHS

        # Infield first - simplest case
        if is_infield:
            return "routine_if"

        # Outfield situations
        if is_outfield:
            if is_gap:
                return "deep_gap" if is_deep else "gap"
            elif is_line:
                return "deep_line" if is_deep else "line"
            else:
                # Straight-away (center, left, right but not gap/line)
                return "deep" if is_deep else "routine_of"

        # Fallback for homerun or unknown depths
        return "deep"

    # =========================================================================
    # PRESERVED HELPER METHODS
    # =========================================================================

    def PickDepth(self):
        # Ensure we have valid outcomes and weights
        if not self.distoutcomes or not self.specificweights:
            return 'middle_of'  # Safe default

        # Ensure weights sum to more than zero
        if sum(self.specificweights) <= 0:
            # Use uniform weights as fallback
            weights = [1] * len(self.distoutcomes)
        else:
            weights = self.specificweights

        depth = random.choices(self.distoutcomes, weights, k=1)[0]
        return depth
        
    def PickDefender(self):
        if self.depth == 'homerun':
            primary_defender = None
        else:
            weight = 1
            listofweights = []

            # Safely get defender list with fallbacks for missing direction/depth
            try:
                direction_data = self.defensivealignment.get(self.direction, {})
                defenderlist = direction_data.get(self.depth, [])
            except (KeyError, TypeError):
                defenderlist = []

            # If no defenders found, return pitcher as fallback
            if not defenderlist:
                return self.gamestate.game.pitchingteam.currentpitcher

            for item in range(0, len(defenderlist)):
                listofweights.append(weight)
                weight = (weight *.5)

            defenderposition = random.choices(defenderlist, listofweights, k=1)[0]

            try:
                primary_defender = [player for player in self.gamestate.game.pitchingteam.battinglist if player.lineup==defenderposition][0]
            except:
                primary_defender = self.gamestate.game.pitchingteam.currentpitcher

        return primary_defender

    def AirballBool(contacttype):
        if contacttype == "homerun":
            airball_bool = None
        elif contacttype in ("barrel", "solid", "flare", "under"):
            airball_bool = True
        else:
            # topped, weak, burner = ground balls
            airball_bool = False
        return airball_bool


def Error_Throw_Catch(self, thrower, catcher):
    throw, t_action = Error_Catch(self, thrower, catcher)
    catch, c_action = Error_Throw(self, thrower, catcher)
    defensiveaction = str(t_action) + " " + str(c_action)
    return throw, catch, defensiveaction

def Error_Catch(self, thrower, catcher):
    """
    Check if a catching error occurs.

    Returns:
        Tuple of (error_occurred: bool, action_description: str)
    """
    baselines = self.gamestate.game.baselines
    if thrower != None:
        depth = Throw_CatchDepth(thrower)
    elif thrower == None:
        if catcher.lineup == 'leftfield' or catcher.lineup == 'centerfield' or catcher.lineup == 'rightfield':
            depth = 'outfield'
        else:
            depth = 'infield'

    diceroll = np.random.rand()
    cfs = (catcher.fieldspot - 50)/50
    cfr = (catcher.fieldreact - 50)/50
    cfc = (catcher.fieldcatch - 50)/50
    cscores = [cfs, cfr, cfc]
    if depth == 'outfield':
        cweights = [4, 2, 3]
    elif depth == 'infield':
        cweights = [1, 2, 3]
    error_rate = (1+np.average(cscores, weights=cweights))*baselines.error_rate
    if error_rate > diceroll:
        # Error occurred - runner advancement handled by caller
        self.errorlist.append(f"{catcher} catching error!")
        if hasattr(catcher, 'fieldingstats'):
            catcher.fieldingstats.Adder("catching_errors", 1)
        return True, f"error by {catcher.lineup} {catcher.name}"
    else:
        if thrower == None:
            return False, f"Ball caught by {catcher.lineup} {catcher.name}"
        else:
            return False, f"{thrower.lineup} {thrower.name}'s throw caught by {catcher.lineup} {catcher.name}"        

def Error_Throw(self, thrower, catcher):
    """
    Check if a throwing error occurs.

    Returns:
        Tuple of (error_occurred: bool, action_description: str)
    """
    baselines = self.gamestate.game.baselines
    if thrower != None:
        depth = Throw_CatchDepth(thrower)
    else:
        # Default to infield if no thrower
        depth = 'infield'

    diceroll = np.random.rand()
    tta = (thrower.throwacc - 50)/50
    ttp = (thrower.throwpower - 50)/50
    cscores = [tta, ttp]
    if depth == 'outfield':
        cweights = [2, 1]
    elif depth == 'infield':
        cweights = [1, 0]

    error_rate = (1+np.average(cscores, weights=cweights))*baselines.error_rate
    if error_rate > diceroll:
        # Error occurred - runner advancement handled by caller
        self.errorlist.append(f"{thrower} throws it wide!")
        if hasattr(thrower, 'fieldingstats'):
            thrower.fieldingstats.Adder("throwing_errors", 1)
        return True, f"error by {thrower.lineup} {thrower.name}"
    else:
        return False, f"{thrower.lineup} {thrower.name} throws it to {catcher.lineup} {catcher.name}"        

def Throw_CatchDepth(thrower):
    if thrower.lineup == 'leftfield' or thrower.lineup == 'centerfield' or thrower.lineup == 'rightfield':
        return 'outfield'
    else:
        return 'infield'


# ============================================================================
# LEGACY CLASS - BasePaths (no longer used by fielding class)
# Runner tracking is now handled by RunnerState/PlayState dataclasses
# Kept for backward compatibility if used elsewhere in codebase
# ============================================================================

class BasePaths():
    """
    DEPRECATED: This class is no longer used by the fielding class.

    Runner tracking is now handled by:
    - RunnerState dataclass: Individual runner state
    - PlayState dataclass: Overall play state including all runners
    - DefenseDecisionTree: Runner decision logic

    This class is kept for backward compatibility only.
    """

    def __init__(self, fielding, batter, firstbase, secondbase, thirdbase, game):
        self.fielding = fielding
        self.batter = batter
        self.firstbase = firstbase
        self.secondbase = secondbase
        self.thirdbase = thirdbase
        self.game = game

        self.baserunner_eval_list = []
        if self.batter != None:
            self.baserunner_eval_list.append(batter)
            self.batter.base = 0
            self.batter.running = True
            self.batter.on_base_pitcher = self.game.pitchingteam.currentpitcher
        if self.firstbase != None:
            self.baserunner_eval_list.append(firstbase)
            self.firstbase.base = 1
        if self.secondbase != None:
            self.baserunner_eval_list.append(secondbase)
            self.secondbase.base = 2
        if self.thirdbase != None:
            self.baserunner_eval_list.append(thirdbase)
            self.thirdbase.base = 3
        self.at_home = []
        self.out = []            

    def __repr__(self):
        return f"Baserunners: {self.baserunner_eval_list} Home: {self.at_home} Out: {self.out}"

    def RunnerOut(self, player):   
        player.base = None
        player.running = None
        player.out = True
        self.game.outcount +=1
        self.baserunner_eval_list.remove(player)

    def RunnerMover(self, outcome):

        def AdvanceRunners(self):

            for runner in self.baserunner_eval_list:



                runner.base+=1
                if len(self.fielding.errorlist) >= 1:
                    runner.earned_bool = False
                if runner.base > 3:
                    #runner.base = None
                    runner.running = None


                    self.at_home.append(runner)
                    self.baserunner_eval_list.remove(runner)

        if outcome == "single":
            AdvanceRunners(self)
        if outcome == "double":
            AdvanceRunners(self)
            AdvanceRunners(self)
        if outcome == "triple":
            AdvanceRunners(self)
            AdvanceRunners(self)
            AdvanceRunners(self)
        if outcome == "throwing error":
            AdvanceRunners(self)
        if outcome == "fielding error":
            pass
        for runner in self.baserunner_eval_list:
            runner.running = None               
                
    def RunnerConverter(self):
        try:
            self.firstbase = [runner for runner in self.baserunner_eval_list if runner.base == 1][0]            
        except:
            self.firstbase = None
                               
        try:
            self.secondbase = [runner for runner in self.baserunner_eval_list if runner.base == 2][0]            
        except:
            self.secondbase = None
                               
        try:
            self.thirdbase = [runner for runner in self.baserunner_eval_list if runner.base == 3][0]            
        except:
            self.thirdbase = None
        return [ self.firstbase, self.secondbase, self.thirdbase, self.at_home]

    def RunnerCheck(self, target, targetbase):
        for runner in self.baserunner_eval_list:
            #print(runner.base, runner.name, runner.speed, runner.baserunning)
            runner.running = None

        if self.batter.base == 0:
            #print("RUNNING")
            self.batter.running = True

    def WhereToThrow(self):
        #print(f"Running WHERE TO THROW")
        try: 
            highestbase = max(self.baserunner_eval_list, key=attrgetter('base')).base
        except: 
            return "no runners", None

        def CheckForForce(self, highestbase):
            if (highestbase == None) or (len(self.baserunner_eval_list) == 0):
                return None, None
            else:
                self.baserunner_eval_list.sort(key=lambda runner: runner.base, reverse=True)
                for player in self.baserunner_eval_list:
                    if player.running == True:
                        target = player 
                        highestbase = player.base
                        return target, highestbase     
                    else: 
                        pass
                return None, None
                
        target, targetbase = CheckForForce(self, highestbase)
        return target, targetbase
    def HandleHomeRun(self):
        for runner in self.baserunner_eval_list:
            self.at_home.append(runner)
            runner.base = None
            runner.running = None
        self.baserunner_eval_list = []

    def DecideToRun(self):
        for baserunner in self.baserunner_eval_list:

            needadvance = [baserunner for runner in self.baserunner_eval_list if (baserunner.base - 1) == runner.base]
            if needadvance != []:
                baserunner.running = True
        if (self.gamestate.game.currentouts + self.gamestate.game.outcount) == self.gamestate.game.rules.outs -1:
            for baserunner in self.baserunner_eval_list:
                baserunner.running = True
