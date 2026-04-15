import math
import random


def clamp(value, min_val, max_val):
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


class PitchEvent:
    """
    Sequential Pipeline for pitcher/batter interaction.

    Phases:
    0.   Pitch Selection - choose pitch and intended location (battery IQ)
    0.5  Consistency Roll - per-pitch variance based on pitch.consist
    0.55 Consecutive Pitch Debuff - repeated pitch type degrades attributes
    0.6  Arm Angle Familiarity - novelty buff / familiarity debuff
    0.75 Handedness Adjustment - modify batter stats for matchup
    0.8  Plate Approach - contact/power stat trades, swing rate modifiers
    1.   Location Quality + HBP check
    2.   Recognition - eye vs deception/velocity
    3.   Swing Decision - discipline vs control + velocity suppression + approach
    3a.  Take Outcome - ball/strike with catcher framing
    4.   Contact Execution - contact vs pitch attributes (uses InsideContact/OutsideContact)
    5.   Contact Type - power shifts config distribution (BattedBallEvent)
    6.   Direction - batter spray chart
    """

    # Config constants (can be moved to baselines later)
    SWING_SHIFT_MAX = 0.12
    CONTACT_SHIFT_MAX = 0.15
    HBP_BASE_RATE = 0.003
    FRAME_MIN = 0.01
    FRAME_MAX = 0.05
    FOUL_RATE = 0.45

    # Relative advantage system constants
    ADVANTAGE_DIVISOR = 50  # Maps 30-point edge to ~0.6 advantage
    DISCIPLINE_SWING_MODIFIER = 0.20  # ±12% per 30-point edge
    EYE_CONTACT_MODIFIER = 0.20  # ±12% per 30-point edge
    BASE_SWING_ON_STRIKE = 0.70  # Base swing rate on strikes
    BASE_SWING_ON_BALL = 0.30  # Base chase rate on balls
    BASE_CONTACT_RATE = 0.75  # Base contact rate at parity

    # Plate approach constants
    APPROACH_STAT_MOD = 5       # ±5 stat trade for contact/power approaches
    APPROACH_SWING_MOD = 0.05   # ±5% swing rate for aggressive/patient

    # Pitching approach constants
    PITCHING_APPROACH_CONTROL_MOD = 15   # ±15 pgencontrol for aggressive/finesse
    PITCHING_APPROACH_HOLD_MOD = 0.05    # ±5% flat strike rate for aggressive/finesse
    PITCHING_APPROACH_THROWPOWER_MOD = 5 # ±5 throwpower for power/location

    # Control-driven location constants
    PGENCONTROL_LOCATION_WEIGHT = 0.70  # pgencontrol share of blended control (pcntrl gets 0.30)

    # Wild pitch probability parameters
    WP_CONTROL_WEIGHT = 0.60      # blended control importance in WP score
    WP_CONSIST_WEIGHT = 0.40      # consistency degrade importance in WP score
    WP_FLOOR = 0.0005             # elite pitcher minimum (~1 per 2000 pitches)
    WP_CEILING = 0.025            # worst case (~2.5% per pitch)

    def __init__(self, action):
        self.action = action
        self.game = action.game
        self.batter = action.game.battingteam.currentbatter
        self.pitcher = action.game.pitchingteam.currentpitcher
        self.catcher = action.game.pitchingteam.catcher

        # Config baselines
        self.insideswing = action.game.baselines.insideswing
        self.outsideswing = action.game.baselines.outsideswing
        self.insidecontact = action.game.baselines.insidecontact
        self.outsidecontact = action.game.baselines.outsidecontact

        self.batted_ball_event = None

        # Store effective stats (will be modified by handedness)
        self.eff_contact = self.batter.contact
        self.eff_power = self.batter.power
        self.eff_eye = self.batter.eye
        self.eff_discipline = self.batter.discipline

        # Initialize phase tracking variables
        self.swing_decision = None
        self.contact_result = None
        self.swing_prob = None
        self.contact_prob = None
        self.consist_degrade = None
        self.blended_control = None
        self.hold_prob = None

        # New phase tracking variables
        self.consecutive_repeat_count = 0
        self.arm_angle_modifier = 0
        self.arm_angle_times_seen = 0
        self.plate_approach = getattr(self.batter, 'plate_approach', 'normal')
        self.pitching_approach = getattr(self.pitcher, 'pitching_approach', 'normal')
        self.eff_pthrowpower = getattr(self.pitcher, 'pthrowpower', 50)
        self.eff_pgencontrol = getattr(self.pitcher, 'pgencontrol', 50)
        self.hold_prob_approach_modifier = 0.0
        self.velocity_swing_modifier = 0
        self.approach_swing_modifier = 0
        self.battery_iq = 0
        self.wild_pitch_triggered = False
        self.wp_probability = 0.0
        self.pitch_selection_weights = None

        # Matchup advantages (calculated after consistency roll)
        self.advantages = None

        # Run the pipeline
        self.outcome = self.run_pipeline()
        self.pitcher.pitchingstats.Adder("pitches_thrown", 1)

    def run_pipeline(self):
        """Execute the sequential pipeline phases."""

        # Phase 0: Pitch Selection (with battery IQ)
        self.pitch, self.intended_location = self.phase0_pitch_selection()

        # Phase 0.5: Consistency Roll - may degrade pitch attributes
        self.eff_pcntrl, self.eff_pbrk, self.eff_pacc = self.phase05_consistency_roll()

        # Phase 0.55: Consecutive Pitch Debuff
        self.eff_pcntrl, self.eff_pbrk, self.eff_pacc = self.phase055_consecutive_pitch_debuff()

        # Phase 0.6: Arm Angle Familiarity
        self.eff_pcntrl, self.eff_pbrk, self.eff_pacc = self.phase06_arm_angle_familiarity()

        # Phase 0.75: Handedness Adjustment
        self.phase075_handedness_adjustment()

        # Phase 0.8: Plate Approach stat modifiers
        self.phase08_plate_approach()

        # Phase 0.9: Pitching Approach modifiers
        self.phase09_pitching_approach()

        # Calculate matchup advantages (after effective stats are set)
        self.advantages = self.calculate_matchup_advantages()

        # Phase 1: Location Quality + HBP check
        result = self.phase1_location_quality()
        if result == "HBP":
            return ["HBP", "Hit By Pitch", self.pitch.name]
        self.final_location = result

        # Phase 1b: Wild Pitch Check (after location determined, uses blended_control + consist_degrade)
        self.phase1b_wild_pitch_check()

        # Phase 2: Recognition
        self.recognition_score = self.phase2_recognition()

        # Phase 3: Swing Decision
        self.swing_decision = self.phase3_swing_decision()

        if self.swing_decision == "Take":
            # Phase 3a: Take Outcome
            return self.phase3a_take_outcome()

        # Phase 4: Contact Execution
        self.contact_result = self.phase4_contact_execution()

        if self.contact_result == "Whiff":
            return ["Strike", "Swinging", self.pitch.name]
        elif self.contact_result == "Foul":
            return ["Strike", "Foul", self.pitch.name]
        else:  # InPlay
            # Phase 5 & 6: Contact Type and Direction (in BattedBallEvent)
            self.batted_ball_event = BattedBallEvent(self)
            return self.batted_ball_event.outcome

    def phase0_pitch_selection(self):
        """
        Select pitch and intended location.

        Battery IQ (psequencing + catchsequence) blends strategy weights
        toward the optimal pitch, factoring in consecutive repeat debuff.
        """
        pitchlist = [
            self.pitcher.pitch1,
            self.pitcher.pitch2,
            self.pitcher.pitch3,
            self.pitcher.pitch4,
            self.pitcher.pitch5
        ]

        # Base strategy weights
        strategy_weights = getattr(self.pitcher, 'pitchchoices', None)
        if not strategy_weights or len(strategy_weights) != 5:
            strategy_weights = [5, 4, 3, 2, 1]

        # Calculate battery IQ (normalized 20-100 → 0.0-1.0)
        psequencing = getattr(self.pitcher, 'psequencing', 50)
        catchsequence = getattr(self.catcher, 'catchsequence', 50)
        raw_iq = (psequencing + catchsequence) / 2.0
        battery_iq = clamp((raw_iq - 20) / 80.0, 0.0, 1.0)

        max_blend = self.game.baselines.battery_iq_weight
        blend_factor = battery_iq * max_blend

        # Preview effective ratings for each pitch (considering consecutive debuff)
        pitcher_id = self.pitcher.id
        last_pitch = self.game.pitcher_last_pitch.get(pitcher_id)
        count = self.game.pitcher_consecutive_count.get(pitcher_id, 0)
        scale = self.game.baselines.consecutive_pitch_debuff_scale

        effective_ratings = []
        for pitch in pitchlist:
            rating = pitch.ovr
            # Preview debuff if this pitch were selected
            if last_pitch == pitch.name:
                preview_count = count + 1
            else:
                preview_count = 0

            if preview_count > 0:
                debuff_pct = min(scale * (preview_count ** 2) / 100.0, 0.30)
                rating *= (1.0 - debuff_pct)

            effective_ratings.append(rating)

        # Build optimal weights proportional to effective ratings
        total_rating = sum(effective_ratings)
        if total_rating > 0:
            optimal_weights = [r / total_rating * 15 for r in effective_ratings]
        else:
            optimal_weights = list(strategy_weights)

        # Blend strategy weights with optimal weights based on battery IQ
        final_weights = [
            sw * (1 - blend_factor) + ow * blend_factor
            for sw, ow in zip(strategy_weights, optimal_weights)
        ]

        # Store for snapshot
        self.battery_iq = round(battery_iq, 3)
        self.pitch_selection_weights = [round(w, 2) for w in final_weights]

        pitch = random.choices(pitchlist, final_weights, k=1)[0]
        location = "Inside"  # Intent is always to throw a strike; Phase 1 determines execution

        return pitch, location

    def phase05_consistency_roll(self):
        """
        Per-pitch variance based on pitch.consist.

        Distribution: right-skewed — mode at 0, tail toward max_degrade.
        Most pitches execute near full strength; disasters are rare but real.

        Both the tail length (max_degrade) and the skew exponent vary with consist:
          - Low consist: long tail (large max_degrade) + flat exponent (frequent degradation)
          - High consist: short tail (small max_degrade) + steep exponent (rare disasters)

        Baseline defaults:
          consist=20  → max_degrade=0.45, exponent=1.2  (avg ~21%, 90th pct ~36%)
          consist=50  → max_degrade=0.30, exponent=1.8  (avg ~11%, 90th pct ~25%)
          consist=80  → max_degrade=0.16, exponent=2.4  (avg ~5%,  90th pct ~13%)
          consist=110 → max_degrade=0.05, exponent=3.0  (avg ~1%,  90th pct ~4%)
        """
        consist = max(self.pitch.consist, 20)
        consist_normalized = (consist - 20) / 90  # 0.0 to 1.0

        bl = self.game.baselines
        max_degrade = bl.consist_degrade_max - (consist_normalized * (bl.consist_degrade_max - bl.consist_degrade_min))
        exponent = bl.consist_exponent_low + (consist_normalized * (bl.consist_exponent_high - bl.consist_exponent_low))

        # Right-skewed draw: U^exponent clusters near 0, tail reaches max_degrade
        degrade_roll = (random.random() ** exponent) * max_degrade
        self.consist_degrade = degrade_roll

        eff_pcntrl = self.pitch.pcntrl * (1 - degrade_roll)
        eff_pbrk = self.pitch.pbrk * (1 - degrade_roll)
        eff_pacc = self.pitch.pacc * (1 - degrade_roll)

        return eff_pcntrl, eff_pbrk, eff_pacc

    def phase055_consecutive_pitch_debuff(self):
        """
        Debuff pitch attributes when the same pitch type is thrown consecutively.
        Uses increasing returns (quadratic) — slight at first, snowballs on long runs.
        """
        pitcher_id = self.pitcher.id
        pitch_name = self.pitch.name
        scale = self.game.baselines.consecutive_pitch_debuff_scale

        last_pitch = self.game.pitcher_last_pitch.get(pitcher_id)
        count = self.game.pitcher_consecutive_count.get(pitcher_id, 0)

        if last_pitch == pitch_name:
            count += 1
        else:
            count = 0

        # Update state for next pitch
        self.game.pitcher_last_pitch[pitcher_id] = pitch_name
        self.game.pitcher_consecutive_count[pitcher_id] = count
        self.consecutive_repeat_count = count

        if count == 0:
            return self.eff_pcntrl, self.eff_pbrk, self.eff_pacc

        # Quadratic debuff: count=1: 1.5%, count=2: 6%, count=3: 13.5%, count=4: 24%
        debuff_pct = scale * (count ** 2) / 100.0
        debuff_pct = min(debuff_pct, 0.30)  # Cap at 30%

        multiplier = 1.0 - debuff_pct
        return (
            self.eff_pcntrl * multiplier,
            self.eff_pbrk * multiplier,
            self.eff_pacc * multiplier,
        )

    def phase06_arm_angle_familiarity(self):
        """
        Arm angle familiarity: pitcher gets a buff on first encounter,
        then neutral, then increasing debuff as batter adjusts.

        1st time seeing arm angle: +increment (novelty)
        2nd time: 0 (neutral)
        3rd time: -increment (batter adjusting)
        4th time: -2*increment, etc.
        """
        batter_id = self.batter.id
        arm_angle = getattr(self.pitcher, 'armangle', None)
        increment = self.game.baselines.arm_angle_familiarity_increment

        if not arm_angle or arm_angle == "":
            self.arm_angle_modifier = 0
            self.arm_angle_times_seen = 0
            return self.eff_pcntrl, self.eff_pbrk, self.eff_pacc

        # Initialize history if needed
        if batter_id not in self.game.batter_arm_angle_history:
            self.game.batter_arm_angle_history[batter_id] = {}

        history = self.game.batter_arm_angle_history[batter_id]
        times_seen = history.get(arm_angle, 0)

        # Only increment on first pitch of at-bat (avoid counting per-pitch)
        is_first_pitch = (self.game.currentstrikes == 0 and self.game.currentballs == 0)
        if is_first_pitch:
            history[arm_angle] = times_seen + 1

        # modifier: 1st(0)=+1, 2nd(1)=0, 3rd(2)=-1, 4th(3)=-2 ...
        modifier = -(times_seen - 1)
        modifier = min(modifier, 1)  # Cap buff at +1

        scaled_modifier = modifier * increment
        self.arm_angle_modifier = scaled_modifier
        self.arm_angle_times_seen = times_seen

        return (
            self.eff_pcntrl + scaled_modifier,
            self.eff_pbrk + scaled_modifier,
            self.eff_pacc + scaled_modifier,
        )

    def phase075_handedness_adjustment(self):
        """Modify batter stats based on handedness matchup."""
        mod_amount = 2
        min_stat = 1
        max_stat = 99

        # Switch hitters get no adjustment
        if self.batter.handedness[0] == "S":
            return

        # Same-side matchup (e.g., RHB vs RHP) - pitcher advantage
        if self.batter.handedness[0] == self.pitcher.handedness[1]:
            self.eff_contact = max(self.batter.contact - mod_amount, min_stat)
            self.eff_power = max(self.batter.power - mod_amount, min_stat)
            self.eff_eye = max(self.batter.eye - mod_amount, min_stat)
            self.eff_discipline = max(self.batter.discipline - mod_amount, min_stat)
        # Opposite-side matchup - batter advantage
        else:
            self.eff_contact = min(self.batter.contact + mod_amount, max_stat)
            self.eff_power = min(self.batter.power + mod_amount, max_stat)
            self.eff_eye = min(self.batter.eye + mod_amount, max_stat)
            self.eff_discipline = min(self.batter.discipline + mod_amount, max_stat)

    def phase08_plate_approach(self):
        """
        Apply plate approach stat modifiers.
        - contact: +2 contact, -2 power
        - power: +2 power, -2 discipline
        - aggressive/patient: no stat change (swing rate handled in phase3)
        - normal: no change
        """
        approach = self.plate_approach
        mod = self.APPROACH_STAT_MOD

        if approach == "contact":
            self.eff_contact = min(self.eff_contact + mod, 99)
            self.eff_power = max(self.eff_power - mod, 1)
        elif approach == "power":
            self.eff_power = min(self.eff_power + mod, 99)
            self.eff_discipline = max(self.eff_discipline - mod, 1)

    def phase09_pitching_approach(self):
        """
        Apply pitching approach modifiers.

        Power/Location — throwpower vs pendurance trade (pendurance applied at construction):
          power:    +5 eff_pthrowpower (more velocity, tires faster)
          location: -5 eff_pthrowpower (less velocity, lasts longer)

        Aggressive/Finesse — strike rate vs control trade:
          aggressive: +5% flat hold_prob, -15 eff_pgencontrol
          finesse:    -5% flat hold_prob, +15 eff_pgencontrol
        """
        approach = self.pitching_approach
        tp_mod = self.PITCHING_APPROACH_THROWPOWER_MOD
        ctrl_mod = self.PITCHING_APPROACH_CONTROL_MOD
        hold_mod = self.PITCHING_APPROACH_HOLD_MOD

        if approach == "power":
            self.eff_pthrowpower = min(self.eff_pthrowpower + tp_mod, 99)
        elif approach == "location":
            self.eff_pthrowpower = max(self.eff_pthrowpower - tp_mod, 1)
        elif approach == "aggressive":
            self.eff_pgencontrol = max(self.eff_pgencontrol - ctrl_mod, 1)
            self.hold_prob_approach_modifier = hold_mod
        elif approach == "finesse":
            self.eff_pgencontrol = min(self.eff_pgencontrol + ctrl_mod, 99)
            self.hold_prob_approach_modifier = -hold_mod

    def calculate_matchup_advantages(self):
        """
        Calculate relative advantages for all attribute pairings.

        Returns dict with advantage values (approximately -1.2 to +1.2 range).
        Positive = batter advantage, Negative = pitcher advantage.

        Pairings:
        - Discipline vs pcntrl → BB% (swing decisions on balls)
        - Eye vs pbrk → K% (whiff rate when swinging)
        - Contact vs pcntrl → AVG (batted ball tier quality)
        - Power vs pacc → ISO (barrel vs solid split within quality tier)
        """
        return {
            'discipline': (self.eff_discipline - self.eff_pcntrl) / self.ADVANTAGE_DIVISOR,
            'eye': (self.eff_eye - self.eff_pbrk) / self.ADVANTAGE_DIVISOR,
            'contact': (self.eff_contact - self.eff_pcntrl) / self.ADVANTAGE_DIVISOR,
            'power': (self.eff_power - self.eff_pacc) / self.ADVANTAGE_DIVISOR,
        }

    def phase1_location_quality(self):
        """
        Determine pitch execution and check for HBP.
        Returns "HBP" or final location ("Inside"/"Outside").

        Blends pgencontrol (70%) and eff_pcntrl (30%) into a control score that
        determines the probability the intended strike actually lands in the zone.
        Low control drifts more pitches outside; drift is one-directional (strikes
        can become balls, but intended balls always stay outside).

        Calibration targets:
          blended=0   → ~35% strikes (floor)
          blended=50  → ~52% strikes
          blended=100 → ~70% strikes (ceiling, clamped)
        """
        w = self.PGENCONTROL_LOCATION_WEIGHT
        blended_control = self.eff_pgencontrol * w + self.eff_pcntrl * (1 - w)
        control_norm = clamp(blended_control / 100.0, 0.0, 1.0)

        floor = self.game.baselines.control_strike_floor
        ceiling = self.game.baselines.control_strike_ceiling
        hold_prob = clamp(
            floor + (ceiling - floor) * control_norm + self.hold_prob_approach_modifier,
            0.0, 1.0
        )

        # Store for snapshot
        self.blended_control = blended_control
        self.hold_prob = hold_prob

        # HBP: base rate 0.003, scales from 0.006 (low control) to 0.0015 (high control)
        control_score = max(blended_control, 20)
        control_normalized_hbp = (control_score - 20) / 90
        hbp_rate = self.HBP_BASE_RATE * (2 - control_normalized_hbp)

        if random.random() < hbp_rate:
            return "HBP"

        # Location execution: intended strike stays inside if control holds, else drifts outside
        if random.random() < hold_prob:
            return "Inside"
        else:
            return "Outside"

    def phase1b_wild_pitch_check(self):
        """
        Determine if this pitch is wild enough to get past the catcher.

        Uses blended control (pgencontrol + eff_pcntrl) and the consistency
        degrade roll from phase05.  Good pitchers with high control and
        consistency rarely throw wild pitches.  Fatigued or inconsistent
        pitchers throw them more often.

        This only determines if the PITCH is wild — catcher blocking
        is resolved separately in Action.py.
        """
        # Control factor: lower control = higher WP chance
        control_score = max(self.blended_control, 10)
        control_normalized = (control_score - 10) / 90  # 0.0 (bad) to 1.0 (good)
        control_factor = 1.0 - control_normalized        # invert: bad control = high factor

        # Consistency factor: larger degrade roll = higher WP chance
        # consist_degrade is 0.0 (perfect execution) to ~0.45 (disaster)
        consist_factor = min(self.consist_degrade / 0.45, 1.0)

        # Weighted blend
        wp_score = (control_factor * self.WP_CONTROL_WEIGHT
                    + consist_factor * self.WP_CONSIST_WEIGHT)

        # Scale to probability range
        wp_prob = self.WP_FLOOR + wp_score * (self.WP_CEILING - self.WP_FLOOR)

        self.wp_probability = wp_prob
        self.wild_pitch_triggered = random.random() < wp_prob

    def phase2_recognition(self):
        """
        Batter's ability to read the pitch.
        Returns recognition modifier (0.5 to 1.5).
        """
        pitcher_deception = (self.eff_pbrk + self.eff_pacc) / 2
        pitcher_deception = max(pitcher_deception, 1)  # Prevent division by zero

        recognition_ratio = self.eff_eye / pitcher_deception
        recognition_score = clamp(recognition_ratio, 0.5, 1.5)

        return recognition_score

    def phase3_swing_decision(self):
        """
        Determine if batter swings or takes.

        Modifiers applied:
        - Discipline advantage (discipline vs pcntrl) — zone-dependent
        - Velocity suppression (pthrowpower) — both zones equally
        - Plate approach (aggressive/patient) — both zones equally

        Returns "Swing" or "Take".
        """
        # Get discipline advantage from matchup advantages
        discipline_adv = self.advantages['discipline']

        # Recognition affects the effective discipline advantage
        effective_discipline_adv = discipline_adv * self.recognition_score

        # Discipline modifier (zone-dependent: helps on strikes, hurts on balls)
        discipline_modifier = effective_discipline_adv * self.DISCIPLINE_SWING_MODIFIER

        # Velocity swing suppression (both zones equally)
        max_suppression = self.game.baselines.velocity_swing_suppression_max
        self.velocity_swing_modifier = ((self.eff_pthrowpower - 50) / 49.0) * max_suppression

        # Plate approach swing modifier (both zones equally)
        approach = self.plate_approach
        if approach == "aggressive":
            self.approach_swing_modifier = self.APPROACH_SWING_MOD
        elif approach == "patient":
            self.approach_swing_modifier = -self.APPROACH_SWING_MOD
        else:
            self.approach_swing_modifier = 0.0

        if self.final_location == "Inside":
            # On strikes: high discipline → MORE likely to swing
            base_rate = self.BASE_SWING_ON_STRIKE
            self.swing_prob = clamp(
                base_rate + discipline_modifier - self.velocity_swing_modifier + self.approach_swing_modifier,
                0.05, 0.95
            )
        else:  # Outside (balls)
            # On balls: high discipline → LESS likely to chase
            base_rate = self.BASE_SWING_ON_BALL
            self.swing_prob = clamp(
                base_rate - discipline_modifier - self.velocity_swing_modifier + self.approach_swing_modifier,
                0.05, 0.95
            )

        if random.random() < self.swing_prob:
            return "Swing"
        else:
            return "Take"

    def phase3a_take_outcome(self):
        """
        Determine ball/strike on taken pitch, with catcher framing.
        """
        if self.final_location == "Inside":
            return ["Strike", "Looking", self.pitch.name]
        else:  # Outside
            # Base outcome is Ball, but catcher can frame it
            catchframe = max(self.catcher.catchframe, 20)  # Floor at 20
            frame_normalized = (catchframe - 20) / 90  # 0.0 to 1.0

            # Frame chance: 0.01 at low, 0.05 at high
            frame_chance = self.FRAME_MIN + (frame_normalized * (self.FRAME_MAX - self.FRAME_MIN))

            if random.random() < frame_chance:
                return ["Strike", "Looking", self.pitch.name]  # Framed!
            else:
                return ["Ball", "Looking", self.pitch.name]

    def phase4_contact_execution(self):
        """
        Determine contact outcome when swinging using eye advantage.

        Eye advantage (batter.eye vs pitcher.pbrk) determines:
        - Higher eye → better hand-eye coordination → more contact, fewer whiffs
        - Lower eye → worse hand-eye coordination → more whiffs → higher K%

        Recognition score also modifies the effective advantage.
        Returns "Whiff", "Foul", or "InPlay".
        """
        # Get eye advantage from matchup advantages
        eye_adv = self.advantages['eye']

        # Recognition affects the effective eye advantage
        # Good recognition helps make contact, poor recognition hurts
        effective_eye_adv = eye_adv * self.recognition_score

        # Calculate contact probability modifier
        # +0.6 advantage (30-point batter edge) → +12% contact rate
        eye_modifier = effective_eye_adv * self.EYE_CONTACT_MODIFIER

        # Apply location-based adjustment
        if self.final_location == "Inside":
            # Inside pitches are generally easier to make contact on
            location_bonus = 0.05
        else:  # Outside
            # Outside pitches are harder to make solid contact
            location_bonus = -0.05

        # Calculate final contact probability
        self.contact_prob = self.BASE_CONTACT_RATE + eye_modifier + location_bonus
        self.contact_prob = clamp(self.contact_prob, 0.40, 0.95)

        # Roll for contact
        if random.random() < self.contact_prob:
            # Contact made - split between InPlay and Foul
            if random.random() < self.FOUL_RATE:
                return "Foul"
            else:
                return "InPlay"
        else:
            return "Whiff"

    def get_phase_snapshot(self):
        """Return a snapshot of all interaction phase data for logging/export."""
        return {
            # Phase 0: Pitch Selection (battery IQ)
            "pitch_name": self.pitch.name if hasattr(self, 'pitch') else None,
            "pitch_ovr": round(self.pitch.ovr, 1) if hasattr(self, 'pitch') else None,
            "intended_location": getattr(self, 'intended_location', None),
            "final_location": getattr(self, 'final_location', None),
            "battery_iq": self.battery_iq,
            "pitch_selection_weights": self.pitch_selection_weights,

            # Phase 0.5: Consistency
            "pitch_consist": round(self.pitch.consist, 1) if hasattr(self, 'pitch') else None,
            "consist_degrade_pct": round(self.consist_degrade * 100, 2) if self.consist_degrade else 0,

            # Phase 0.55: Consecutive Pitch Debuff
            "consecutive_repeat_count": self.consecutive_repeat_count,
            "consecutive_debuff_pct": round(
                min(self.game.baselines.consecutive_pitch_debuff_scale * (self.consecutive_repeat_count ** 2) / 100.0, 0.30) * 100, 2
            ) if self.consecutive_repeat_count > 0 else 0,

            # Phase 0.6: Arm Angle Familiarity
            "arm_angle": getattr(self.pitcher, 'armangle', None),
            "arm_angle_times_seen": self.arm_angle_times_seen,
            "arm_angle_modifier": self.arm_angle_modifier,

            # Effective pitch attributes (after all pitch modifier phases)
            "eff_pcntrl": round(self.eff_pcntrl, 1) if hasattr(self, 'eff_pcntrl') else None,
            "eff_pbrk": round(self.eff_pbrk, 1) if hasattr(self, 'eff_pbrk') else None,
            "eff_pacc": round(self.eff_pacc, 1) if hasattr(self, 'eff_pacc') else None,

            # Phase 0.75: Handedness
            "batter_hand": self.batter.handedness[0] if hasattr(self, 'batter') else None,
            "pitcher_hand": self.pitcher.handedness[1] if hasattr(self, 'pitcher') else None,

            # Phase 0.8: Plate Approach
            "plate_approach": self.plate_approach,

            # Effective batter stats (after handedness + plate approach)
            "eff_contact": round(self.eff_contact, 1),
            "eff_power": round(self.eff_power, 1),
            "eff_eye": round(self.eff_eye, 1),
            "eff_discipline": round(self.eff_discipline, 1),

            # Phase 0.9: Pitching Approach
            "pitching_approach": self.pitching_approach,
            "eff_pthrowpower": round(self.eff_pthrowpower, 1),
            "eff_pgencontrol": round(self.eff_pgencontrol, 1),
            "hold_prob_approach_modifier": round(self.hold_prob_approach_modifier, 3),

            # Pitcher general control
            "pgencontrol": round(self.pitcher.pgencontrol, 1) if hasattr(self, 'pitcher') else None,
            # Phase 1: Control-driven location
            "blended_control": round(self.blended_control, 1) if self.blended_control is not None else None,
            "hold_prob": round(self.hold_prob, 3) if self.hold_prob is not None else None,

            # Matchup advantages (batter vs pitcher)
            "adv_discipline": round(self.advantages['discipline'], 3) if self.advantages else None,
            "adv_eye": round(self.advantages['eye'], 3) if self.advantages else None,
            "adv_contact": round(self.advantages['contact'], 3) if self.advantages else None,
            "adv_power": round(self.advantages['power'], 3) if self.advantages else None,

            # Phase 2: Recognition
            "recognition_score": round(self.recognition_score, 3) if hasattr(self, 'recognition_score') else None,

            # Phase 3: Swing Decision
            "swing_prob": round(self.swing_prob, 3) if self.swing_prob else None,
            "swing_decision": self.swing_decision,
            "velocity_swing_modifier": round(self.velocity_swing_modifier, 4),
            "approach_swing_modifier": round(self.approach_swing_modifier, 4),

            # Phase 4: Contact (if swing)
            "contact_prob": round(self.contact_prob, 3) if self.contact_prob else None,
            "contact_result": self.contact_result,

            # Catcher framing
            "catcher_frame": round(self.catcher.catchframe, 1) if hasattr(self, 'catcher') else None,

            # Phase 1b: Wild Pitch
            "wp_probability": round(self.wp_probability, 5) if self.wp_probability else None,
            "wild_pitch_triggered": self.wild_pitch_triggered,
        }


class BattedBallEvent:
    """
    Phase 5 & 6: Contact Type and Direction.

    Contact Type Determination (Tier System):
    - Contact advantage shifts probability between tiers (Quality/Neutral/Poor)
    - Power advantage affects Barrel vs Solid split within Quality tier only
    - All base rates come from config data

    Tier Structure:
    - Quality: Barrel + Solid (contact expands, power splits)
    - Neutral: Flare, Burner (fixed config ratio)
    - Poor: Topped, Under, Weak (fixed config ratio)

    Both contact and power use exponential curves:
    - Contact (exponent=2): controls quality tier size
    - Power (exponent=3): controls barrel vs solid within quality
    """

    # Contact → Quality tier size (exponential, batter side only)
    CONTACT_TIER_SHIFT_FACTOR = 0.45
    CONTACT_TIER_EXPONENT = 2.0

    # Power → Barrel share within quality (exponential)
    POWER_BARREL_SHIFT = 0.40
    POWER_BARREL_EXPONENT = 3.0
    POWER_BARREL_MAX = 0.50
    POWER_BARREL_MIN = 0.00001

    MIN_PROBABILITY = 0.001

    def __init__(self, pitchevent):
        self.pitchevent = pitchevent
        self.batter = pitchevent.batter
        self.pitcher = pitchevent.pitcher
        self.game = pitchevent.game

        # Get matchup advantages from PitchEvent
        self.advantages = pitchevent.advantages

        # Config baseline contact odds
        baselines = pitchevent.game.baselines
        self.base_odds = {
            "barrel": baselines.barrelodds,
            "solid": baselines.solidodds,
            "flare": baselines.flareodds,
            "burner": baselines.burnerodds,
            "under": baselines.underodds,
            "topped": baselines.toppedodds,
            "weak": baselines.weakodds
        }

        # Calculate base tier probabilities from config
        self._calculate_base_tiers()

        # Store raw stats for tuning export
        self.raw_batter_contact = self.batter.contact
        self.raw_batter_power = self.batter.power
        self.raw_pitch_ovr = pitchevent.pitch.ovr

        # Run phases
        self.contact_type = self.phase5_contact_type()
        self.direction = self.phase6_direction()
        self.outcome = [self.contact_type, self.direction, pitchevent.pitch.name]

    def _calculate_base_tiers(self):
        """Calculate base tier probabilities from config odds."""
        total = sum(self.base_odds.values())
        if total <= 0:
            total = 1

        odds = {k: v / total for k, v in self.base_odds.items()}

        # Tier base probabilities
        self.quality_base = odds["barrel"] + odds["solid"]
        self.neutral_base = odds["flare"] + odds["burner"]
        self.poor_base = odds["topped"] + odds["under"] + odds["weak"]

        # Within quality: barrel share (power shifts this at runtime)
        if self.quality_base > 0:
            self.barrel_share_of_quality = odds["barrel"] / self.quality_base
        else:
            self.barrel_share_of_quality = 0.5

        # Within neutral: flare share
        if self.neutral_base > 0:
            self.flare_share_of_neutral = odds["flare"] / self.neutral_base
        else:
            self.flare_share_of_neutral = 0.5

        # Within poor: topped/under/weak shares
        if self.poor_base > 0:
            self.topped_share_of_poor = odds["topped"] / self.poor_base
            self.under_share_of_poor = odds["under"] / self.poor_base
        else:
            self.topped_share_of_poor = 0.33
            self.under_share_of_poor = 0.33

    def phase5_contact_type(self):
        """
        Determine batted ball contact type using tier system with exponential curves.

        Pipeline:
        1. Contact advantage redistributes tiers (exponential, batter side only)
        2. Roll for tier (Quality/Neutral/Poor)
        3. Power advantage determines barrel vs solid within Quality (exponential)
        """
        contact_adv = self.advantages['contact']
        power_adv = self.advantages['power']

        # Step 1: Redistribute tiers based on contact advantage (exponential)
        quality_prob, neutral_prob, poor_prob = self._redistribute_tiers(contact_adv)

        # Store tier probabilities for tuning export
        self.tier_probs = {
            'quality': round(quality_prob, 4),
            'neutral': round(neutral_prob, 4),
            'poor': round(poor_prob, 4)
        }

        # Step 2: Roll for tier
        roll = random.random()
        if roll < quality_prob:
            tier = 'quality'
        elif roll < quality_prob + neutral_prob:
            tier = 'neutral'
        else:
            tier = 'poor'

        self.selected_tier = tier

        # Step 3: Roll for type within tier
        if tier == 'quality':
            contact_type = self._roll_quality_tier(power_adv)
        elif tier == 'neutral':
            contact_type = self._roll_neutral_tier()
        else:
            contact_type = self._roll_poor_tier()

        # Store final odds for tuning export
        self.final_odds = self._reconstruct_final_odds(quality_prob, neutral_prob, poor_prob, power_adv)

        return contact_type

    def _redistribute_tiers(self, contact_adv):
        """
        Apply contact advantage to shift tier probabilities (exponential on batter side).

        Positive contact advantage (batter edge):
        - Exponential curve (exponent=2): moderate advantage barely shifts,
          elite advantage significantly expands quality tier
        - Shifts from Poor → Quality and Neutral

        Negative contact advantage (pitcher edge):
        - Linear shift from Quality/Neutral → Poor
        """
        quality = self.quality_base
        neutral = self.neutral_base
        poor = self.poor_base

        if contact_adv > 0:
            # Batter advantage: exponential curve
            exp_adv = abs(contact_adv) ** self.CONTACT_TIER_EXPONENT
            shift = exp_adv * self.CONTACT_TIER_SHIFT_FACTOR
            poor_reduction = poor * shift

            # 40% of shifted probability goes to Quality, 60% to Neutral
            quality_gain = poor_reduction * 0.4
            neutral_gain = poor_reduction * 0.6

            quality = quality + quality_gain
            neutral = neutral + neutral_gain
            poor = poor - poor_reduction
        else:
            # Pitcher advantage: linear (unchanged)
            shift = abs(contact_adv) * self.CONTACT_TIER_SHIFT_FACTOR

            quality_reduction = quality * shift
            neutral_reduction = neutral * shift * 0.5

            quality = quality - quality_reduction
            neutral = neutral - neutral_reduction
            poor = poor + quality_reduction + neutral_reduction

        # Ensure minimums
        quality = max(quality, self.MIN_PROBABILITY)
        neutral = max(neutral, self.MIN_PROBABILITY)
        poor = max(poor, self.MIN_PROBABILITY)

        # Normalize to sum to 1.0
        total = quality + neutral + poor
        return quality / total, neutral / total, poor / total

    def _roll_quality_tier(self, power_adv):
        """
        Roll within Quality tier (barrel vs solid) using exponential power curve.
        """
        base_barrel = self.barrel_share_of_quality
        signed_exp = math.copysign(abs(power_adv) ** self.POWER_BARREL_EXPONENT, power_adv)
        barrel_share = base_barrel + signed_exp * self.POWER_BARREL_SHIFT
        barrel_share = clamp(barrel_share, self.POWER_BARREL_MIN, self.POWER_BARREL_MAX)

        self.barrel_share = barrel_share

        if random.random() < barrel_share:
            return 'barrel'
        else:
            return 'solid'

    def _roll_neutral_tier(self):
        """Roll within Neutral tier using config ratios (flare vs burner)."""
        if random.random() < self.flare_share_of_neutral:
            return 'flare'
        else:
            return 'burner'

    def _roll_poor_tier(self):
        """Roll within Poor tier using config ratios."""
        roll = random.random()
        if roll < self.topped_share_of_poor:
            return 'topped'
        elif roll < self.topped_share_of_poor + self.under_share_of_poor:
            return 'under'
        else:
            return 'weak'

    def _reconstruct_final_odds(self, quality_prob, neutral_prob, poor_prob, power_adv):
        """Reconstruct individual type odds for tuning export."""
        signed_exp = math.copysign(abs(power_adv) ** self.POWER_BARREL_EXPONENT, power_adv)
        barrel_share = self.barrel_share_of_quality + signed_exp * self.POWER_BARREL_SHIFT
        barrel_share = clamp(barrel_share, self.POWER_BARREL_MIN, self.POWER_BARREL_MAX)

        return {
            'barrel': round(quality_prob * barrel_share, 4),
            'solid': round(quality_prob * (1 - barrel_share), 4),
            'flare': round(neutral_prob * self.flare_share_of_neutral, 4),
            'burner': round(neutral_prob * (1 - self.flare_share_of_neutral), 4),
            'topped': round(poor_prob * self.topped_share_of_poor, 4),
            'under': round(poor_prob * self.under_share_of_poor, 4),
            'weak': round(poor_prob * (1 - self.topped_share_of_poor - self.under_share_of_poor), 4)
        }

    def phase6_direction(self):
        """
        Determine field direction using batter spray splits.
        """
        # Get batter's spray splits (default to even if not set)
        left_split = getattr(self.batter, 'left_split', 0.33)
        center_split = getattr(self.batter, 'center_split', 0.34)
        right_split = getattr(self.batter, 'right_split', 0.33)

        # Derive 7-zone spread from 3 splits
        far_left = left_split / 4
        left = left_split / 2
        center = center_split / 2
        right = right_split / 2
        far_right = right_split / 4

        # Center-left and center-right are averages of adjacent zones
        center_left = (left + center) / 2
        center_right = (right + center) / 2

        directions = [
            "far left", "left", "center left", "dead center",
            "center right", "right", "far right"
        ]
        weights = [far_left, left, center_left, center, center_right, right, far_right]

        # Safety check for valid weights
        weights = [max(0, w) if w == w else 0 for w in weights]
        if sum(weights) <= 0:
            weights = [1/7] * 7  # Even distribution fallback

        direction = random.choices(directions, weights=weights, k=1)[0]
        return direction

    def get_modifier_snapshot(self):
        """Return modifier data for tuning export."""
        return {
            "batter_contact": round(self.raw_batter_contact, 1),
            "batter_power": round(self.raw_batter_power, 1),
            "pitch_ovr": round(self.raw_pitch_ovr, 1),
            # Matchup advantages
            "contact_advantage": round(self.advantages['contact'], 3),
            "power_advantage": round(self.advantages['power'], 3),
            # Tier system results
            "tier_probs": self.tier_probs,
            "selected_tier": self.selected_tier,
            "barrel_share": round(getattr(self, 'barrel_share', self.barrel_share_of_quality), 3),
            # Final reconstructed odds
            "final_odds": self.final_odds
        }

    def __repr__(self):
        return f"BattedBallEvent: {self.contact_type} to {self.direction}"
