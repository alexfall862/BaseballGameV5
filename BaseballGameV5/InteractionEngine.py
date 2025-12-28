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
    FOUL_RATE = 0.30

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
        location = random.choices(["Inside", "Outside"], [1, 1.5], k=1)[0]

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
        mod_amount = 5
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
        Determine if batter swings or takes.
        Uses InsideSwing/OutsideSwing as config anchors.
        Returns "Swing" or "Take".
        """
        pitcher_control = (self.pitcher.pgencontrol + self.eff_pcntrl) / 2
        pitcher_control = max(pitcher_control, 1)  # Prevent division by zero

        discipline_ratio = self.eff_discipline / pitcher_control

        # Recognition affects discipline effectiveness
        effective_discipline_ratio = discipline_ratio * self.recognition_score

        # Calculate bounded shift
        shift = (effective_discipline_ratio - 1.0) * self.SWING_SHIFT_MAX
        shift = clamp(shift, -self.SWING_SHIFT_MAX, self.SWING_SHIFT_MAX)

        if self.final_location == "Inside":
            self.swing_prob = clamp(self.insideswing + shift, 0.05, 0.95)
        else:  # Outside
            # Good discipline = LESS chasing on balls outside the zone
            self.swing_prob = clamp(self.outsideswing - shift, 0.05, 0.95)

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
        Determine contact outcome when swinging.
        Uses InsideContact/OutsideContact as config anchors.
        Returns "Whiff", "Foul", or "InPlay".
        """
        pitcher_difficulty = (self.eff_pbrk + self.eff_pcntrl) / 2
        pitcher_difficulty = max(pitcher_difficulty, 1)  # Prevent division by zero

        contact_ratio = self.eff_contact / pitcher_difficulty

        # Recognition also affects contact
        effective_contact_ratio = contact_ratio * self.recognition_score

        # Calculate bounded shift
        shift = (effective_contact_ratio - 1.0) * self.CONTACT_SHIFT_MAX
        shift = clamp(shift, -self.CONTACT_SHIFT_MAX, self.CONTACT_SHIFT_MAX)

        if self.final_location == "Inside":
            self.contact_prob = clamp(self.insidecontact + shift, 0.20, 0.98)
        else:  # Outside
            self.contact_prob = clamp(self.outsidecontact + shift, 0.20, 0.98)

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
    Power shifts config distribution, batter spray splits determine direction.
    """

    # Config constants
    POWER_BASELINE = 50
    POWER_RANGE = 40
    POWER_MAX_REDISTRIBUTION = 0.08

    def __init__(self, pitchevent):
        self.pitchevent = pitchevent
        self.batter = pitchevent.batter
        self.pitcher = pitchevent.pitcher
        self.game = pitchevent.game

        # Get effective power (with handedness adjustment already applied)
        self.eff_power = pitchevent.eff_power

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

        # Store raw stats for tuning export
        self.raw_batter_contact = self.batter.contact
        self.raw_batter_power = self.batter.power
        self.raw_pitch_ovr = pitchevent.pitch.ovr

        # Run phases
        self.contact_type = self.phase5_contact_type()
        self.direction = self.phase6_direction()
        self.outcome = [self.contact_type, self.direction, pitchevent.pitch.name]

    def phase5_contact_type(self):
        """
        Determine quality of contact.
        Power shifts probability between quality tiers.
        """
        # Normalize base odds to sum to 1
        total = sum(self.base_odds.values())
        if total <= 0:
            total = 1

        odds = {k: v / total for k, v in self.base_odds.items()}

        # Calculate power shift
        power_shift = (self.eff_power - self.POWER_BASELINE) / self.POWER_RANGE
        power_shift = clamp(power_shift, -1.0, 1.0)

        # Amount to redistribute
        redistribution = abs(power_shift) * self.POWER_MAX_REDISTRIBUTION

        # Tier definitions
        quality_tier = ["barrel", "solid"]
        neutral_tier = ["flare", "burner"]
        poor_tier = ["under", "topped", "weak"]

        if power_shift > 0:
            # High power: steal from neutral/poor, give to quality
            # Calculate how much to take from each tier
            neutral_total = sum(odds[k] for k in neutral_tier)
            poor_total = sum(odds[k] for k in poor_tier)
            source_total = neutral_total + poor_total

            if source_total > 0:
                # Take proportionally from neutral and poor
                for key in neutral_tier + poor_tier:
                    take_fraction = odds[key] / source_total
                    odds[key] -= redistribution * take_fraction
                    odds[key] = max(odds[key], 0.001)

                # Give proportionally to quality
                quality_total = sum(odds[k] for k in quality_tier)
                if quality_total > 0:
                    for key in quality_tier:
                        give_fraction = odds[key] / quality_total
                        odds[key] += redistribution * give_fraction
        else:
            # Low power: steal from quality, give to neutral
            quality_total = sum(odds[k] for k in quality_tier)

            if quality_total > 0:
                # Take proportionally from quality
                for key in quality_tier:
                    take_fraction = odds[key] / quality_total
                    odds[key] -= redistribution * take_fraction
                    odds[key] = max(odds[key], 0.001)

                # Give proportionally to neutral
                neutral_total = sum(odds[k] for k in neutral_tier)
                if neutral_total > 0:
                    for key in neutral_tier:
                        give_fraction = odds[key] / neutral_total
                        odds[key] += redistribution * give_fraction

        # Normalize again after redistribution
        total = sum(odds.values())
        odds = {k: v / total for k, v in odds.items()}

        # Store final odds for tuning export
        self.final_odds = {k: round(v, 4) for k, v in odds.items()}

        # Roll for contact type
        outcomes = list(odds.keys())
        weights = list(odds.values())

        # Safety check for valid weights
        weights = [max(0, w) if w == w else 0 for w in weights]
        if sum(weights) <= 0:
            weights = [1] * len(weights)

        contact_type = random.choices(outcomes, weights=weights, k=1)[0]
        return contact_type

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
            "effective_power": round(self.eff_power, 1),
            "power_shift": round((self.eff_power - self.POWER_BASELINE) / self.POWER_RANGE, 3),
            "final_odds": self.final_odds
        }

    def __repr__(self):
        return f"BattedBallEvent: {self.contact_type} to {self.direction}"
