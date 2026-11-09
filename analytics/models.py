"""
analytics/models.py

Defines the shared data models used throughout the Analytics package.

Unlike telemetry models, these classes represent meaning rather than raw
measurements. They are passed between the engineer modules as the system 
observes, reasons and generates coaching advice.

This file should only contain data models.
It should not perform any calculations or contain business logic.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Any

## Observation Categories

class ObservationCategory(Enum):
    BRAKING = auto()
    CORNERING = auto()
    ACCELERATION = auto()
    TYRES = auto()
    ERS = auto()
    FUEL = auto()
    STRATEGY = auto()
    RACECRAFT = auto()
    TRACK_LIMITS = auto()
    DAMAGE = auto()
    SAFETY_CAR = auto()
    GENERAL = auto()
    CAR_CONTROL = auto()

class ObservationPolarity(Enum):
    POSITIVE = auto()
    NEGATIVE = auto()
    CONTEXT_DEPENDENT = auto()

## Observation Types

"""
Each ObservationType stores static metadata about an observation.

This metadata never changes between laps or sessions and acts as the single
source of truth for describing that observation

Dynamic information such as severity, recommendations and time loss
belongs elsewhere in the reasoning pipeline
"""

class ObservationType(Enum):
    ## Braking
    EARLY_BRAKING = (
        "Early Braking",
        ObservationCategory.BRAKING,
        "Braking begins earlier than reference point, losing time on approach",
        ObservationPolarity.NEGATIVE,
    )
    LATE_BRAKING = (
        "Late Braking",
        ObservationCategory.BRAKING,
        "Braking begins later than the reference point - may be committed or overshot",
        ObservationPolarity.CONTEXT_DEPENDENT,
    )
    BRAKE_LOCKUP = (
        "Brake Lockup",
        ObservationCategory.BRAKING,
        "Brake lock-up detected - tyre flat-spot risk",
        ObservationPolarity.NEGATIVE,
    )
    POOR_BRAKE_RELEASE = (
        "Poor Brake Release",
        ObservationCategory.BRAKING,
        "Brake release is less controlled than optimal",
        ObservationPolarity.NEGATIVE,
    )
    GOOD_BRAKING = (
        "Good Braking",
        ObservationCategory.BRAKING,
        "Braking is consistently well executed",
        ObservationPolarity.POSITIVE,
    )

    ## Cornering
    UNDERSTEER = (
        "Understeer",
        ObservationCategory.CORNERING,
        "Understeer detected during cornering",
        ObservationPolarity.NEGATIVE,
    )
    OVERSTEER = (
        "Oversteer",
        ObservationCategory.CORNERING,
        "Oversteer detected during cornering",
        ObservationPolarity.NEGATIVE,
    )
    MISSED_APEX = (
        "Missed Apex",
        ObservationCategory.CORNERING,
        "Apex was missed during cornering",
        ObservationPolarity.NEGATIVE,
    )
    LOW_CORNER_SPEED = (
        "Low Corner Speed",
        ObservationCategory.CORNERING,
        "Minimum corner speed is below optimal",
        ObservationPolarity.NEGATIVE,
    )
    POOR_RACING_LINE = (
        "Poor Racing Line",
        ObservationCategory.CORNERING,
        "Racing line deviates from the optimal line",
        ObservationPolarity.NEGATIVE,
    )
    GOOD_RACING_LINE = (
        "Good Racing Line",
        ObservationCategory.CORNERING,
        "Optimal racing line maintained",
        ObservationPolarity.POSITIVE,
    )

    ## Acceleration
    LATE_THROTTLE = (
        "Late Throttle",
        ObservationCategory.ACCELERATION,
        "Throttle application begins later than optimal",
        ObservationPolarity.NEGATIVE,
    )
    WHEELSPIN = (
        "Wheelspin",
        ObservationCategory.ACCELERATION,
        "Wheelspin detected under acceleration",
        ObservationPolarity.NEGATIVE,
    )
    POOR_TRACTION = (
        "Poor Traction",
        ObservationCategory.ACCELERATION,
        "Loss of traction detected on corner exit",
        ObservationPolarity.NEGATIVE,
    )
    GOOD_TRACTION = (
        "Good Traction",
        ObservationCategory.ACCELERATION,
        "Strong traction maintained on corner exit",
        ObservationPolarity.POSITIVE,
    )
    LOW_EXIT_SPEED = (
        "Low Exit Speed",
        ObservationCategory.ACCELERATION,
        "Speed at corner exit below optimal",
        ObservationPolarity.NEGATIVE,
    )

    ## Tyres
    HIGH_FRONT_TYRE_TEMPERATURE = (
        "High Front Tyre Temperature",
        ObservationCategory.TYRES,
        "Front tyre temperatures exceed the optimal operating window",
        ObservationPolarity.NEGATIVE,
    )
    HIGH_REAR_TYRE_TEMPERATURE = (
        "High Rear Tyre Temperature",
        ObservationCategory.TYRES,
        "Rear tyre temperatures exceed the optimal operating window",
        ObservationPolarity.NEGATIVE,
    )
    LOW_TYRE_TEMP = (
        "Low Tyre Temperature",
        ObservationCategory.TYRES,
        "Tyre temperatures below the optimal operating window",
        ObservationPolarity.NEGATIVE,
    )
    HIGH_TYRE_DEGRADATION = (
        "High Tyre Degradation",
        ObservationCategory.TYRES,
        "Tyre degradation is higher than expected",
        ObservationPolarity.NEGATIVE,
    )
    TYRE_WEAR_WARNING = (
        "Tyre Wear Warning",
        ObservationCategory.TYRES,
        "Tyre wear approaching the threshold were performance drops significantly",
        ObservationPolarity.NEGATIVE
    )
    TYRE_WEAR_CRITICAL = (
        "Tyre Wear Critical",
        ObservationCategory.TYRES,
        "Tyre wear at a level where failure or severe performance loss is iminent",
        ObservationPolarity.NEGATIVE,
    )
    TYRE_BLISTER = (
        "Tyre Blister",
        ObservationCategory.TYRES,
        "Tyre blistering detected - thermal degredation in progress",
        ObservationPolarity.NEGATIVE,
    )
    GOOD_TYRE_MANAGEMENT = (
        "Good Tyre Management",
        ObservationCategory.TYRES,
        "Tyres are being managed effectively",
        ObservationPolarity.POSITIVE,
    )
    OPTIMAL_TYRE_TEMPERATURE = (
        "Optimal Tyre Temperature",
        ObservationCategory.TYRES,
        "Tyres are within optimal operating window",
        ObservationPolarity.POSITIVE,
    )

    ## ERS
    POOR_ERS_DEPLOYMENT = (
        "Poor ERS Deployment",
        ObservationCategory.ERS,
        "ERS deployment is less effective than optimal",
        ObservationPolarity.NEGATIVE,
    )
    POOR_ERS_HARVESTING = (
        "Poor ERS Harvesting",
        ObservationCategory.ERS,
        "ERS harvesting is less effective than optimal",
        ObservationPolarity.NEGATIVE, 
    )
    ERS_STORE_LOW = (
        "ERS Store Low",
        ObservationCategory.ERS,
        "ERS battery critically low",
        ObservationPolarity.NEGATIVE,
    )
    GOOD_ERS_DEPLOYMENT = (
        "Good ERS Deployment",
        ObservationCategory.ERS,
        "ERS deployment is effective",
        ObservationPolarity.POSITIVE,
    )
    GOOD_ERS_HARVESTING = (
        "Good ERS Harvesting",
        ObservationCategory.ERS,
        "ERS harvesting is effective",
        ObservationPolarity.POSITIVE,
    )

    ## Fuel
    FUEL_SAVE_REQUIRED = (
        "Fuel Save Required",
        ObservationCategory.FUEL,
        "Fuel load below optimal to finish race",
        ObservationPolarity.NEGATIVE,
    )
    FUEL_SURPLUS = (
        "Fuel Surplus",
        ObservationCategory.FUEL,
        "Fuel surplus available",
        ObservationPolarity.CONTEXT_DEPENDENT,
    )
    FUEL_CRITICAL = (
        "Fuel Critical",
        ObservationCategory.FUEL,
        "Fuel level critically low",
        ObservationPolarity.NEGATIVE,
    )

    ## Strategy
    PIT_WINDOW_OPEN = (
        "Pit Window Open",
        ObservationCategory.STRATEGY,
        "Driver is within ideal pit stop window",
        ObservationPolarity.CONTEXT_DEPENDENT,
    )
    PIT_WINDOW_CLOSING = (
        "Pit Window Closing",
        ObservationCategory.STRATEGY,
        "Driver is approaching last viable pit lap",
        ObservationPolarity.NEGATIVE,
    )
    UNDERCUT_OPPORTUNITY = (
        "Undercut Opportunity",
        ObservationCategory.STRATEGY,
        "Gap to car ahead and tyre age makes undercut viable",
        ObservationPolarity.CONTEXT_DEPENDENT,
    )

    ## Racecraft
    GOOD_OVERTAKE = (
        "Good Overtake",
        ObservationCategory.RACECRAFT,
        "Successful overtake executed",
        ObservationPolarity.POSITIVE,
    )
    DEFENDED_POSITION = (
        "Defended Position",
        ObservationCategory.RACECRAFT,
        "Position defended successfully",
        ObservationPolarity.POSITIVE,
    )
    POSITION_GAINED = (
        "Position Gained",
        ObservationCategory.RACECRAFT,
        "Race position gained",
        ObservationPolarity.POSITIVE,
    )
    POSITION_LOST = (
        "Position Lost",
        ObservationCategory.RACECRAFT,
        "Race position lost",
        ObservationPolarity.NEGATIVE,
    )

    ## Track Limits
    TRACK_LIMIT_WARNING = (
        "Track Limit Warning",
        ObservationCategory.TRACK_LIMITS,
        "Track limits warning issued",
        ObservationPolarity.NEGATIVE,
    )

    ## Damage
    WING_DAMAGE = (
        "Wing Damage",
        ObservationCategory.DAMAGE,
        "Front or rear wing damaged",
        ObservationPolarity.NEGATIVE,
    )
    ENGINE_DAMAGE = (
        "Engine Damage",
        ObservationCategory.DAMAGE,
        "Engine damage detected",
        ObservationPolarity.NEGATIVE,
    )
    GEARBOX_DAMAGE = (
        "Gearbox Damage",
        ObservationCategory.DAMAGE,
        "Gearbox damage detected",
        ObservationPolarity.NEGATIVE,
    )
    DRS_FAULT = (
        "DRS Fault",
        ObservationCategory.DAMAGE,
        "DRS system fault",
        ObservationPolarity.NEGATIVE,
    )

    ## Safety Car
    SAFETY_CAR_DEPLOYED = (
        "Safety Car Deployed",
        ObservationCategory.SAFETY_CAR,
        "Safety car deployed - potential pit stop opportunity",
        ObservationPolarity.CONTEXT_DEPENDENT,
    )
    SAFETY_CAR_ENDING = (
        "Safety Car Ending",
        ObservationCategory.SAFETY_CAR,
        "Safety car in this lap",
        ObservationPolarity.CONTEXT_DEPENDENT,
    )
    RED_FLAG = (
        "Red Flag",
        ObservationCategory.SAFETY_CAR,
        "Red flag - session suspended",
        ObservationPolarity.CONTEXT_DEPENDENT,
    )

    ## General
    PERSONAL_BEST_LAP = (
        "Personal Best Lap",
        ObservationCategory.GENERAL,
        "New personal best lap",
        ObservationPolarity.POSITIVE,
    )
    PERSONAL_BEST_SECTOR = (
        "Personal Best Sector",
        ObservationCategory.GENERAL,
        "Personal best sector recorded",
        ObservationPolarity.POSITIVE,
    )
    CONSISTENT_DRIVING = (
        "Consistent Driving",
        ObservationCategory.GENERAL,
        "Driving performance is consistently strong",
        ObservationPolarity.POSITIVE,
    )
    FASTEST_LAP_OF_RACE = (
        "Fastest Lap of Race",
        ObservationCategory.GENERAL,
        "Fastest lap of the race set",
        ObservationPolarity.POSITIVE,
    )

    def __init__(
            self,
            display_name: str,
            category: ObservationCategory,
            description: str,
            polarity: ObservationPolarity
    ):
        self.display_name = display_name
        self.category = category
        self.description = description
        self.polarity = polarity

@dataclass(frozen=True)
class Evidence:
    """
    Numerical facts supporting a single observation
    No interpretation or language, just measurements
    """
    ## Identity
    evidence_id: int
    observation_id: int
    source: str = ""

    ## Core Measurement
    player_value: Optional[float] = None
    reference_value: Optional[float] = None
    delta: Optional[float] = None
    units: str = ""

    ## Time Loss
    time_loss_s: Optional[float] = None

    ## Location
    lap: Optional[int] = None
    track_distance: Optional[float] = None
    corner_id: Optional[int] = None
    session_time: Optional[float] = None

    ## Telemetry Snapshot
    speed_kph: Optional[float] = None
    throttle: Optional[float] = None
    brake: Optional[float] = None
    gear: Optional[int] = None
    tyre_wear_fl: Optional[float] = None
    tyre_wear_fr: Optional[float] = None
    tyre_wear_rl: Optional[float] = None
    tyre_wear_rr: Optional[float] = None
    tyre_temp_fl: Optional[float] = None
    tyre_temp_fr: Optional[float] = None
    tyre_temp_rl: Optional[float] = None
    tyre_temp_rr: Optional[float] = None
    ers_store_pct: Optional[float] = None
    fuel_remaining: Optional[float] = None
    engine_rpm: Optional[int] = None

    ## Reference Driver Identity
    reference_driver: Optional[str] = None

    ## Confidence
    confidence: float = 1.0

    extra: Dict[str, Any] = field(default_factory = dict)

@dataclass(frozen=True)
class Observation:
    """
    A single fact noticed by the engineer
    
    An Observation is a factual record of something that occured at a
    specific point during a session. It contains no reasoning,
    prioritisation or coaching advice

    Example:
        "Brake point is 6 metres early"
    """
    observation_id: int
    observation_type: ObservationType
    lap: int
    session_time: float
    track_distance: float
    corner_id: Optional[int] = None
    source: str = ""
    confidence: float = 1.0
    evidence_id: Optional[int] = None

@dataclass
class Issue:
    """
    A named problem derived from multiple related Observations

    Issues are mutable, the reasoning engine adds observations to them
    over time as new laps are processed. Confidence rises as more
    observations accumulate
    """
    issue_id: int
    observation_type: ObservationType
    corner_id: Optional[int] = None
    observations: List[Observation] = field(default_factory = list)
    evidence_ids: List[int] = field(default_factory = list)

    confidence: float = 0.0
    first_seen_lap: Optional[int] = None
    last_seen_lap: Optional[int] = None
    laps_seen: int = 0

    total_time_loss_s: float = 0.0

    communicated: bool = False
    communicated_lap: Optional[int] = None

    @property
    def category(self) -> ObservationCategory:
        return self.observation_type.category

    @property
    def display_name(self) -> str:
        return self.observation_type.display_name

    @property
    def is_corner_specific(self) -> bool:
        return self.corner_id is not None

    def add_observation(self, obs: Observation, time_loss_s: float = 0.0) -> None:
        self.observations.append(obs)
        if obs.evidence_id is not None:
            self.evidence_ids.append(obs.evidence_id)
        self.laps_seen += 1
        self.total_time_loss_s += time_loss_s
        if self.first_seen_lap is None:
            self.first_seen_lap = obs.lap
        self.last_seen_lap = obs.lap

class PatternScope(Enum):
    SINGLE_CORNER = auto()
    CORNER_TYPE = auto()
    CIRCUIT_WIDE = auto()
    CROSS_SESSION = auto()

@dataclass
class Pattern:
    """
    A recurring driving habit identified from multiple observations

    Patterns are created by the reasoning engine when it detects that
    multiple Issues share a common root cause
    """
    pattern_id: int
    name: str
    description: str
    category: ObservationCategory
    scope: PatternScope = PatternScope.CORNER_TYPE

    issues: List[Issue] = field(default_factory = list)

    corner_types: List[str] = field(default_factory = list)

    confidence: float = 0.0
    total_time_loss_s: float = 0.0

    first_seen_session: Optional[str] = None
    first_seen_lap: Optional[int] = None
    last_seen_lap: Optional[int] = None
    sessions_seen: int = 0
    laps_affected: int = 0

    recommendation_generated: bool = False

    def add_issue(self, issue: Issue) -> None:
        self.issues.append(issue)
        self.total_time_loss_s += issue.total_time_loss_s
        self.laps_affected += issue.laps_seen
        if self.first_seen_lap is None:
            self.first_seen_lap = issue.first_seen_lap
        self.last_seen_lap = issue.last_seen_lap

class RecommendationPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFO = 4

class RecommendationSource(Enum):
    ISSUE = auto()
    PATTERN = auto()
    EVENT = auto()

@dataclass
class Recommendation:
    """
    Actionable coaching derived from an Issue or Pattern
    """
    recommendation_id: int
    priority: RecommendationPriority
    source_type: RecommendationSource
    source_id: int
    observation_type: ObservationType
    category: ObservationCategory

    recommendation_text: str

    corner_id: Optional[int] = None
    corner_name: Optional[str] = None
    lap: Optional[int] = None

    estimated_gain_s: Optional[float] = None
    confidence: float = 0.0

    player_value: Optional[float] = None
    target_value: Optional[float] = None
    delta: Optional[float] = None
    units: str = ""

    reference_type: str = "self_pb"

    created_at: float = field(default_factory = time.perf_counter)
    session_time: Optional[float] = None

    @property
    def is_critical(self) -> bool:
        return self.priority == RecommendationPriority.CRITICAL

@dataclass
class Advice:
    """
    An approved Recommendation scheduled for delivery to the driver
    """
    advice_id: int
    recommendation: Recommendation

    approved_at: float = field(default_factory = time.perf_counter)
    scheduled_lap: Optional[int] = None
    scheduled_time: Optional[float] = None

    personality_id: str = "default"

    use_llm: bool = True
    fallback_template: str = ""

    delivered: bool = False
    delivered_at: Optional[float] = None
    delivery_method: str = ""

    @property
    def priority(self) -> RecommendationPriority:
        return self.recommendation.priority

    @property
    def is_critical(self) -> bool:
        return self.recommendation.is_critical

__all__ = [
    "ObservationCategory",
    "ObservationPolarity",
    "ObservationType",
    "PatternScope",
    "RecommendationPriority",
    "RecommendationSource",
    "Evidence",
    "Observation",
    "Issue",
    "Pattern",
    "Recommendation",
    "Advice",
]