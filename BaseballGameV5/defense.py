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
        "gap_reach_bonus": 2.5,      # Extra time for gap hits (between OF)
        "line_reach_bonus": 2.0,     # Extra time down the line
        "deep_chase_bonus": 1.5,     # Ball over fielder's head
        "outfield_retrieval": 1.5,   # Pick up and set in OF
        "infield_retrieval": 0.4,    # Pick up and set in IF
        "hard_hit_bonus": 0.5,       # Less reaction time on barrels/solids
        "base_reach_time": 0.5,      # Fielder already in position
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
    def runner_time(runner: RunnerState) -> float:
        """
        Calculate time for runner to reach their target base.

        Args:
            runner: RunnerState with current_base, target_base, speed_rating, progress

        Returns:
            Time in seconds for runner to reach target
        """
        base_key = (runner.current_base, runner.target_base)
        base_time = TimeCalculator.BASE_RUNNING_TIMES.get(base_key, 4.0)

        # Speed modifier: 50 rating = 1.0x, each point = 1%
        # 80 speed = 0.7x time (30% faster), 20 speed = 1.3x time (30% slower)
        speed_mod = 1.0 - ((runner.speed_rating - 50) * 0.01)

        # Account for progress already made
        remaining = 1.0 - runner.progress

        return base_time * speed_mod * remaining

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
                         fielder_pos: str, fielder_player) -> float:
        """
        Total time from bat contact until fielder can throw.

        This is the key method for determining XBH - it calculates
        the full time window during which runners can advance.

        total_time = ball_travel_time + fielder_reach_time + ball_retrieval_time

        Args:
            contact_type: Type of contact (barrel, flare, etc.)
            depth: Where ball lands (deep_of, middle_of, etc.)
            direction: Ball direction (center left, far right, etc.)
            fielder_pos: Position of primary fielder
            fielder_player: Player object for the fielder

        Returns:
            Total time in seconds until fielder can throw
        """
        # 1. Ball travel time (existing method)
        ball_time = TimeCalculator.ball_travel_time(contact_type, depth)

        # 2. Fielder reach time (new)
        fielder_speed = getattr(fielder_player, 'speed', 50) if fielder_player else 50
        reach_time = TimeCalculator.fielder_reach_time(
            depth, direction, fielder_pos, contact_type, fielder_speed
        )

        # 3. Ball retrieval time (new)
        is_outfield = depth in TimeCalculator.OUTFIELD_DEPTHS
        retrieval_time = TimeCalculator.ball_retrieval_time(contact_type, is_outfield)

        return ball_time + reach_time + retrieval_time


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
            runner_time = TimeCalculator.runner_time(runner)

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
        runner_time = TimeCalculator.runner_time(runner)

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

    # Default fielding weights (fallback)
    # Order: out, single, double, triple
    DEFAULT_FIELDINGWEIGHTS = {
        "barrel": [100.25, 0.30, 0.30, 0.15],
        "solid": [100.40, 0.35, 0.20, 0.05],
        "flare": [100.55, 0.35, 0.08, 0.02],
        "burner": [100.65, 0.30, 0.04, 0.01],
        "under": [100.50, 0.35, 0.12, 0.03],
        "topped": [100.75, 0.22, 0.02, 0.01],
        "weak": [100.80, 0.18, 0.01, 0.01],
    }

    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.test = self.gamestate.game.baselines.threestepaway
        self.distweights = self.gamestate.game.baselines.distweights
        self.distoutcomes = self.gamestate.game.baselines.distoutcomes
        self.defensivealignment = self.gamestate.game.baselines.defensivealignment
        self.fieldingweights = self.gamestate.game.baselines.fieldingweights
        self.fieldingoutcomes = self.gamestate.game.baselines.fieldingoutcomes
        self.errorlist = []
        self.defensiveactions = []

        self.contacttype = self.gamestate.outcome[0]
        self.direction = self.gamestate.outcome[1]

        # Determine what type of batted ball and where it goes (preserved logic)
        # Use fallback weights if contact type missing or weights sum to zero
        self.specificweights = self._get_distweights(self.contacttype)
        self.depth = fielding.PickDepth(self)
        self.fieldingdefender = fielding.PickDefender(self)
        self.airball_bool = fielding.AirballBool(self.contacttype)
        self.adjustedfieldingweights = fielding.ModWeights(
            self.fieldingdefender,
            self._get_fieldingweights(self.contacttype),
            self.depth,
            self.airball_bool,
            self.gamestate.game.baselines.fieldingmod,
            self.gamestate.game.baselines.fieldingmultiplier
        )

        # Determine initial outcome (preserved - determines if ball is fieldable)
        self.initial_outcome = fielding.OutcomeChooser(self)

        # Initialize play state with new decision tree system
        self.play_state = self._initialize_play_state()

        # Process the play using decision tree
        self.batted_ball_outcome = self._process_play()

        # Convert play state back to base_situation format for compatibility
        self.base_situation = self._build_base_situation()

        # Build the defenseoutcome tuple (format unchanged)
        self.defenseoutcome = (
            self.contacttype,
            self.direction,
            self.fieldingdefender,
            self.batted_ball_outcome,
            self.base_situation,
            self.errorlist,
            self.defensiveactions
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

    def _is_catchable_play(self) -> bool:
        """
        Determine if this is a catchable fly ball based on physics.

        Ground balls can never be caught - they must be fielded.
        Air balls can be caught based on trajectory and fielder position.

        Returns:
            True if ball is in the air and can be caught, False otherwise
        """
        # Ground ball contact types - these can NEVER be caught
        GROUND_BALL_TYPES = ["topped", "weak"]

        # If it's a ground ball, it can't be caught
        if self.contacttype in GROUND_BALL_TYPES:
            return False

        # If depth is homerun, it's gone (handled separately)
        if self.depth == 'homerun':
            return False

        # For air balls, check if fielder can reach it
        # Gap hits and line drives are harder to catch
        is_gap = self.direction in ["center left", "center right"]
        is_line = self.direction in ["far left", "far right"]
        is_deep = "deep" in self.depth.lower()

        # Hard-hit balls to gaps/lines are less likely to be caught
        if self.contacttype in ["barrel", "solid"]:
            if is_gap and is_deep:
                # Deep gap - very hard to catch
                return random.random() < 0.3
            elif is_gap:
                # Gap hit - hard to catch
                return random.random() < 0.5
            elif is_line:
                # Down the line - hard to catch
                return random.random() < 0.5
            elif is_deep:
                # Deep fly - moderately hard
                return random.random() < 0.6

        # Flares and burners to outfield gaps
        if self.contacttype in ["flare", "burner"]:
            if is_gap:
                return random.random() < 0.4
            elif is_line:
                return random.random() < 0.5

        # Default: use OutcomeChooser result for infield flies and routine plays
        return self.initial_outcome == 'out'

    def _process_play(self) -> str:
        """
        Process the entire play using decision tree logic.

        Uses physics-based determination of catch vs hit:
        - Ground balls always go to timing-based fielding
        - Air balls to gaps/lines have reduced catch probability
        - Routine fly balls can be caught

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
            return self.initial_outcome

        # Determine if this is a catchable fly ball using physics
        is_catch_attempt = self._is_catchable_play()

        if is_catch_attempt:
            # FLY BALL CATCH ATTEMPT
            # Runners only advance during ball flight (tag up rules)
            ball_time = TimeCalculator.ball_travel_time(self.contacttype, self.depth)
            self._advance_runners_during_flight(ball_time)

            error_on_catch, d_action = Error_Catch(self, None, self.fieldingdefender)
            self.defensiveactions.append(d_action)

            if error_on_catch:
                # Fielding error - ball gets away, becomes a hit
                self._mark_runs_unearned()
                self._advance_all_runners(1)  # Extra base on error
                return 'single'
            else:
                # Successful catch - ball fielded
                fielder_state.has_ball = True
                self.play_state.ball_holder = fielder_state

                # On fly ball out, batter is out immediately
                batter_runner = next(
                    (r for r in self.play_state.runners if r.current_base == 0),
                    None
                )
                if batter_runner:
                    batter_runner.is_out = True
                    self.play_state.outs_this_play += 1
                    self.gamestate.game.outcount += 1
                    self.defensiveactions.append(f"out at bat (fly)")

                    # Award putout to fielder who caught the fly ball
                    if hasattr(self.fieldingdefender, 'fieldingstats'):
                        self.fieldingdefender.fieldingstats.Adder("putouts", 1)

                    # Update force state
                    DefenseDecisionTree.update_force_state_after_out(
                        self.play_state, 1
                    )

                # Check if more outs possible (tag up situations)
                if self._can_continue_play():
                    self._defense_loop()

                return 'out'
        else:
            # HIT PLAY - Ball lands fair (ground ball, gap hit, or dropped)
            # Calculate TOTAL time until fielder can throw
            # This includes: ball flight + fielder reach + ball retrieval
            total_time = TimeCalculator.total_field_time(
                self.contacttype,
                self.depth,
                self.direction,
                fielder_state.position,
                fielder_state.player
            )

            # Advance runners for the FULL time window
            # This is what allows doubles and triples to occur naturally
            self._advance_runners_for_time(total_time)

            # Now fielder has the ball
            fielder_state.has_ball = True
            self.play_state.ball_holder = fielder_state

            # Run the defense loop for any throw plays
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
        runner_time = TimeCalculator.runner_time(target_runner)

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

        Args:
            available_time: Total time in seconds that runners can advance
        """
        for runner in self.play_state.runners:
            if runner.is_out:
                continue

            time_remaining = available_time

            while time_remaining > 0 and runner.current_base < 4:
                # Calculate time to next base
                base_key = (runner.current_base, runner.target_base)
                base_time = TimeCalculator.BASE_RUNNING_TIMES.get(base_key, 4.0)

                # Speed modifier: 50 rating = 1.0x, each point = 1%
                # 80 speed = 0.7x time (30% faster), 20 speed = 1.3x time
                speed_mod = 1.0 - ((runner.speed_rating - 50) * 0.01)
                speed_mod = max(speed_mod, 0.5)  # Cap at 50% faster

                # Time needed to complete remaining progress to next base
                time_to_next = base_time * speed_mod * (1 - runner.progress)

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
                    if (base_time * speed_mod) > 0:
                        progress_made = time_remaining / (base_time * speed_mod)
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

        return self.initial_outcome

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

    def _get_fieldingweights(self, contacttype: str) -> list:
        """
        Get fielding weights for a contact type with fallback to defaults.

        Args:
            contacttype: The type of contact (barrel, solid, flare, etc.)

        Returns:
            List of weights for fielding outcomes
        """
        # Try to get from config
        weights = self.fieldingweights.get(contacttype)

        # Check if weights exist and have valid values
        if weights and len(weights) >= 4:
            return weights

        # Fall back to defaults
        default = fielding.DEFAULT_FIELDINGWEIGHTS.get(contacttype)
        if default:
            return default

        # Ultimate fallback - favor outs
        return [100.50, 0.35, 0.12, 0.03]

    # =========================================================================
    # PRESERVED HELPER METHODS (used by both old and new systems)
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
        elif contacttype == "barrel" or "solid" or "flare" or "under":
            airball_bool = True
        else:
            airball_bool = False
        return airball_bool

    def ModWeights(defender, fieldingodds, depth, airball_bool, mod, multiplier):
        if defender == None:
            return [0,0,0,0]
        
        if airball_bool == True:
            ab = 'air'
        else:
            ab = 'ground'
        if '_of' in depth:
            d = 'outfield'
        else:
            d = 'infield'

        #print(f"Type:{ab} In/Out:{d}")

        outodds = fieldingodds[0]
        singleodds = fieldingodds[1]
        doubleodds = fieldingodds[2]
        tripleodds = fieldingodds[3]
        sumvalue = sum([outodds, singleodds, doubleodds, tripleodds])
        skills = [defender.fieldcatch, defender.fieldreact, defender.fieldspot, defender.speed]
        skillsweight = mod[ab][d]

        modifier = (((np.average(skills, weights=skillsweight))/50)+multiplier)/(multiplier+1)

        outodds *= modifier
        singleodds /= modifier
        doubleodds /= modifier
        tripleodds /= modifier
        listofodds = [outodds, singleodds, doubleodds, tripleodds]
        # Ensure no division by zero
        total_odds = sum(listofodds)
        if total_odds <= 0:
            processedodds = [0.25, 0.25, 0.25, 0.25]  # Equal distribution fallback
        else:
            processedodds = [x / total_odds for x in listofodds]
        outodds = processedodds[0]
        singleodds = processedodds[1]
        doubleodds = processedodds[2]
        tripleodds = processedodds[3]
        processedlistofodds = [outodds, singleodds, doubleodds, tripleodds]
        return processedlistofodds

    def OutcomeChooser(self):
        if self.depth == 'homerun':
            outcome = 'homerun'
        else:
            outcomes = self.gamestate.game.baselines.fieldingoutcomes
            weights = self.adjustedfieldingweights

            # Ensure valid weights (non-negative, no NaN)
            weights = [max(0, w) if w == w else 0 for w in weights]

            # Fallback if all weights are zero
            if sum(weights) <= 0:
                weights = [1] * len(outcomes) if outcomes else [1, 1, 1, 1]

            outcome = random.choices(outcomes, weights, k=1)[0]
        return outcome 
    
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
