import random


def clamp(value, min_val, max_val):
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


class PitchEvent:
    """
    Sequential Pipeline for pitcher/batter interaction.

    Phases:
    0.   Pitch Selection - choose pitch and intended location
    0.5  Consistency Roll - per-pitch variance based on pitch.consist
    0.75 Handedness Adjustment - modify batter stats for matchup
    1.   Location Quality + HBP check
    2.   Recognition - eye vs deception/velocity
    3.   Swing Decision - discipline vs control (uses InsideSwing/OutsideSwing)
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

        # Matchup advantages (calculated after consistency roll)
        self.advantages = None

        # Run the pipeline
        self.outcome = self.run_pipeline()
        self.pitcher.pitchingstats.Adder("pitches_thrown", 1)

    def run_pipeline(self):
        """Execute the sequential pipeline phases."""

        # Phase 0: Pitch Selection
        self.pitch, self.intended_location = self.phase0_pitch_selection()

        # Phase 0.5: Consistency Roll - may degrade pitch attributes
        self.eff_pcntrl, self.eff_pbrk, self.eff_pacc = self.phase05_consistency_roll()

        # Phase 0.75: Handedness Adjustment
        self.phase075_handedness_adjustment()

        # Calculate matchup advantages (after effective stats are set)
        self.advantages = self.calculate_matchup_advantages()

        # Phase 1: Location Quality + HBP check
        result = self.phase1_location_quality()
        if result == "HBP":
            return ["HBP", "Hit By Pitch", self.pitch.name]
        self.final_location = result

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
        """Select pitch and intended location."""
        pitchlist = [
            self.pitcher.pitch1,
            self.pitcher.pitch2,
            self.pitcher.pitch3,
            self.pitcher.pitch4,
            self.pitcher.pitch5
        ]
        pitchodds = [5, 4, 3, 2, 1]

        pitch = random.choices(pitchlist, pitchodds, k=1)[0]
        location = random.choices(["Inside", "Outside"], [1, 1], k=1)[0]

        return pitch, location

    def phase05_consistency_roll(self):
        """
        Per-pitch variance based on pitch.consist.
        Low consist = left-tail degradation (can crater).
        High consist = floor near 0% degradation.
        """
        consist = max(self.pitch.consist, 20)  # Floor at 20
        consist_normalized = (consist - 20) / 90  # 0.0 to 1.0

        # Max possible degradation decreases as consist increases
        # At consist=20: max_degrade = 0.20 (can lose up to 20%)
        # At consist=110: max_degrade = 0.02 (almost no variance)
        max_degrade = 0.20 - (consist_normalized * 0.18)

        # Roll for actual degradation (left-tail: 0 to max_degrade)
        degrade_roll = random.random() * max_degrade
        self.consist_degrade = degrade_roll  # Store for snapshot

        # Apply to pitch attributes for THIS pitch only
        eff_pcntrl = self.pitch.pcntrl * (1 - degrade_roll)
        eff_pbrk = self.pitch.pbrk * (1 - degrade_roll)
        eff_pacc = self.pitch.pacc * (1 - degrade_roll)

        return eff_pcntrl, eff_pbrk, eff_pacc

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
        """
        control_score = (self.pitcher.pgencontrol + self.eff_pcntrl) / 2
        control_score = max(control_score, 20)  # Floor at 20
        control_normalized = (control_score - 20) / 90  # 0.0 to 1.0

        # HBP: base rate 0.003, scales from 0.006 (low control) to 0.0015 (high control)
        hbp_rate = self.HBP_BASE_RATE * (2 - control_normalized)

        if random.random() < hbp_rate:
            return "HBP"

        # For now, location stays as intended (drift can be added later)
        return self.intended_location

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
        Determine if batter swings or takes using discipline advantage.

        Discipline advantage (batter.discipline vs pitcher.pcntrl) determines:
        - On strikes (Inside): Higher discipline → more swings (recognizes hittable pitches)
        - On balls (Outside): Higher discipline → fewer swings (avoids chasing)

        Recognition score also modifies the effective advantage.
        Returns "Swing" or "Take".
        """
        # Get discipline advantage from matchup advantages
        discipline_adv = self.advantages['discipline']

        # Recognition affects the effective discipline advantage
        # Good recognition amplifies discipline, poor recognition mutes it
        effective_discipline_adv = discipline_adv * self.recognition_score

        # Calculate swing probability modifier
        # +0.6 advantage (30-point batter edge) → +12% modifier
        discipline_modifier = effective_discipline_adv * self.DISCIPLINE_SWING_MODIFIER

        if self.final_location == "Inside":
            # On strikes: high discipline → MORE likely to swing
            base_rate = self.BASE_SWING_ON_STRIKE
            self.swing_prob = clamp(base_rate + discipline_modifier, 0.05, 0.95)
        else:  # Outside (balls)
            # On balls: high discipline → LESS likely to chase
            base_rate = self.BASE_SWING_ON_BALL
            self.swing_prob = clamp(base_rate - discipline_modifier, 0.05, 0.95)

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
            # Pitch info
            "pitch_name": self.pitch.name if hasattr(self, 'pitch') else None,
            "pitch_ovr": round(self.pitch.ovr, 1) if hasattr(self, 'pitch') else None,
            "intended_location": getattr(self, 'intended_location', None),
            "final_location": getattr(self, 'final_location', None),

            # Phase 0.5: Consistency
            "pitch_consist": round(self.pitch.consist, 1) if hasattr(self, 'pitch') else None,
            "consist_degrade_pct": round(self.consist_degrade * 100, 2) if self.consist_degrade else 0,

            # Effective pitch attributes (after consistency roll)
            "eff_pcntrl": round(self.eff_pcntrl, 1) if hasattr(self, 'eff_pcntrl') else None,
            "eff_pbrk": round(self.eff_pbrk, 1) if hasattr(self, 'eff_pbrk') else None,
            "eff_pacc": round(self.eff_pacc, 1) if hasattr(self, 'eff_pacc') else None,

            # Phase 0.75: Handedness
            "batter_hand": self.batter.handedness[0] if hasattr(self, 'batter') else None,
            "pitcher_hand": self.pitcher.handedness[1] if hasattr(self, 'pitcher') else None,

            # Effective batter stats (after handedness adjustment)
            "eff_contact": round(self.eff_contact, 1),
            "eff_power": round(self.eff_power, 1),
            "eff_eye": round(self.eff_eye, 1),
            "eff_discipline": round(self.eff_discipline, 1),

            # Pitcher general control
            "pgencontrol": round(self.pitcher.pgencontrol, 1) if hasattr(self, 'pitcher') else None,

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

            # Phase 4: Contact (if swing)
            "contact_prob": round(self.contact_prob, 3) if self.contact_prob else None,
            "contact_result": self.contact_result,

            # Catcher framing
            "catcher_frame": round(self.catcher.catchframe, 1) if hasattr(self, 'catcher') else None,
        }


class BattedBallEvent:
    """
    Phase 5 & 6: Contact Type and Direction.

    Contact Type Determination (Tier System):
    - Contact advantage shifts probability between tiers (Quality/Neutral/Poor)
    - Power advantage affects Barrel vs Solid split within Quality tier only
    - All base rates come from config data

    Tier Structure:
    - Quality: Barrel, Solid (~13% base)
    - Neutral: Flare, Burner (~25% base)
    - Poor: Topped, Under, Weak (~62% base)
    """

    # Tier redistribution constants
    CONTACT_TIER_SHIFT_FACTOR = 0.40  # 40% shift per 30-point advantage
    POWER_BARREL_SHIFT = 0.30  # ±18% barrel share per 30-point edge
    MIN_PROBABILITY = 0.001  # Minimum probability floor

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

        # Normalize odds
        odds = {k: v / total for k, v in self.base_odds.items()}

        # Calculate tier base probabilities
        self.quality_base = odds["barrel"] + odds["solid"]
        self.neutral_base = odds["flare"] + odds["burner"]
        self.poor_base = odds["topped"] + odds["under"] + odds["weak"]

        # Store within-tier shares from config
        if self.quality_base > 0:
            self.barrel_share_of_quality = odds["barrel"] / self.quality_base
        else:
            self.barrel_share_of_quality = 0.5

        if self.neutral_base > 0:
            self.flare_share_of_neutral = odds["flare"] / self.neutral_base
        else:
            self.flare_share_of_neutral = 0.5

        if self.poor_base > 0:
            self.topped_share_of_poor = odds["topped"] / self.poor_base
            self.under_share_of_poor = odds["under"] / self.poor_base
            # weak is the remainder
        else:
            self.topped_share_of_poor = 0.33
            self.under_share_of_poor = 0.33

    def phase5_contact_type(self):
        """
        Determine batted ball contact type using tier system.

        Pipeline:
        1. Get contact advantage (batter.contact vs pitch.pcntrl)
        2. Redistribute tier probabilities based on contact advantage
        3. Roll for tier (Quality/Neutral/Poor)
        4. Roll for type within tier:
           - Quality: Power advantage determines Barrel vs Solid split
           - Neutral: Config ratio determines Flare vs Burner
           - Poor: Config ratio determines Topped vs Under vs Weak
        """
        # Get advantages
        contact_adv = self.advantages['contact']
        power_adv = self.advantages['power']

        # Step 1: Redistribute tiers based on contact advantage
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

        # Store final odds for tuning export (reconstructed from tier system)
        self.final_odds = self._reconstruct_final_odds(quality_prob, neutral_prob, poor_prob, power_adv)

        return contact_type

    def _redistribute_tiers(self, contact_adv):
        """
        Apply contact advantage to shift tier probabilities.

        Positive contact advantage (batter edge):
        - Shifts probability from Poor → Neutral and Quality

        Negative contact advantage (pitcher edge):
        - Shifts probability from Quality and Neutral → Poor
        """
        quality = self.quality_base
        neutral = self.neutral_base
        poor = self.poor_base

        if contact_adv > 0:
            # Batter advantage: shift from Poor to Neutral/Quality
            shift = contact_adv * self.CONTACT_TIER_SHIFT_FACTOR
            poor_reduction = poor * shift

            # 40% of shifted probability goes to Quality, 60% to Neutral
            quality_gain = poor_reduction * 0.4
            neutral_gain = poor_reduction * 0.6

            quality = quality + quality_gain
            neutral = neutral + neutral_gain
            poor = poor - poor_reduction
        else:
            # Pitcher advantage: shift from Quality/Neutral to Poor
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
        Roll within Quality tier, applying power advantage.

        Power advantage affects Barrel vs Solid split:
        - Positive power advantage → more Barrel
        - Negative power advantage → more Solid
        """
        # Base barrel share from config
        base_barrel = self.barrel_share_of_quality

        # Power shifts barrel/solid split
        # +0.6 advantage (30-point edge) → +18% barrel share
        barrel_share = base_barrel + (power_adv * self.POWER_BARREL_SHIFT)
        barrel_share = clamp(barrel_share, 0.05, 0.95)

        self.barrel_share = barrel_share  # Store for tuning export

        if random.random() < barrel_share:
            return 'barrel'
        else:
            return 'solid'

    def _roll_neutral_tier(self):
        """Roll within Neutral tier using config ratios."""
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
        # Calculate barrel share based on power advantage
        barrel_share = self.barrel_share_of_quality + (power_adv * self.POWER_BARREL_SHIFT)
        barrel_share = clamp(barrel_share, 0.05, 0.95)

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
