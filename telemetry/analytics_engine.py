import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Tuple, Any

from telemetry_state import(
    TelemetryState,
    CarState,
    SessionState,
    LapRecord,
)
from packet_parser import(
    _ms_to_time_str,
    TYRE_COMPOUNDS_VISUAL,
    ERS_DEPLOY_MODES,
)

## SECTION 1: Insight Types, Priorities, and Insight Dataclass

class InsightPriority(Enum):
    CRITICAL = 0        ## Interrupt anything
    WARNING = 1         ## Say within 3 seconds
    ADVISORY = 2        ## Queue for next appropriate moment
    INFO = 3            ## Background, say when nothing else queued

class InsightType(Enum):
    ## Lap Timing
    LAP_COMPLETED = auto()          ## Lap time
    SECTOR_DELTA = auto()           ## Sector time vs Personal best
    PERSONAL_BEST = auto()          ## New PB lap
    THEORETICAL_BEST = auto()       ## Ideal lap
    ## Tyre Management
    TYRE_WEAR_WARNING = auto()      ## Wear above threshold, laps estimate
    TYRE_WEAR_CRITICAL = auto()     ## Wear above 80%, pit soon
    TYRE_TEMP_COLD = auto()         ## Tyres below operating window
    TYRE_TEMP_OVERHEATING = auto()  ## Tyres above operating window
    TYRE_BLISTER_WARNING = auto()   ## Blistering detected
    TYRE_DEGREDATION_RATE = auto()  ## How fast tyres are wearing per lap
    ## Fuel Management
    FUEL_DELTA = auto()             ## Fuel laps vs Race laps remaining
    FUEL_SAVE_REQUIRED = auto()     ## Fuel short, switch to lean
    FUEL_RICH_AVAILABLE = auto()    ## Fuel surplus, can use rich
    FUEL_CRITICAL = auto()          ## Fuel very low
    ## ERS Management
    ERS_STORE_LOW = auto()          ## ERS depleted
    ERS_HARVEST_LOW = auto()        ## Harvesting less than usual
    ERS_DEPLOY_SUGGESTION = auto()  ## Good moment to use overtake
    ## Braking Zone
    BRAKING_POINT_LATE = auto()     ## Braking later than PB, time lost
    BRAKING_POINT_EARLY = auto()    ## Braking earlier than PB, time lost
    TRAIL_BRAKE_DETECTED = auto()   ## Carrying brake into corner
    ## Race Strategy
    UNDERCUT_WINDOW = auto()        ## Gap to car ahead in undercut range
    OVERCUT_POSSIBLE = auto()       ## Car ahead pitted, stay out
    PIT_WINDOW_OPEN = auto()        ## Inside the games ideal pit window
    PIT_WINDOW_CLOSING = auto()     ## Approaching latest pit lap
    ## Safety Car/Flags
    SAFETY_CAR_DEPLOYED = auto()    ## Safety car deployed
    SAFETY_CAR_ENDING = auto()      ## Safety car ending
    RED_FLAG = auto()               ## Red flag
    YELLOW_FLAG = auto()            ## Yellow flag
    ## Damage/Reliability
    DAMAGE_WING = auto()            ## Wing damage detected
    DAMAGE_FLOOR = auto()           ## Floor damage detected
    DAMAGE_ENGINE = auto()          ## Engine damage detected
    DAMAGE_GEARBOX = auto()         ## Gearbox damage detected
    ENGINE_BLOWN = auto()           ## Terminal damage
    DRS_FAULT = auto()              ## DRS not working
    ## Position/Race
    POSITION_GAINED = auto()        ## Position gained
    POSITION_LOST = auto()          ## Position lost
    GAP_TO_AHEAD = auto()           ## Gap to car ahead
    GAP_TO_LEADER = auto()          ## Gap to leader
    OVERTAKE_DETECTED = auto()      ## Overtake
    FASTEST_LAP = auto()            ## Fastest lap

@dataclass
class Insight:
    insight_type: InsightType           ## What the insight type is
    priority: InsightPriority           ## Priority of insight
    timestamp: float                    ## time.perf_counter() when generated
    session_time: float                 ## session clock (seconds)
    data: Dict[str, Any]                ## payload - keys depend on insight_type
    message: str = ""                   ## pre-built plain-English summary
    lap_number: Optional[int] = None    ## lap this insight relates to
    vehicle_idx: Optional[int] = None   ## car this insight relates to (None = player)

    def __repr__(self) -> str:
        return(
            f"Insight({self.insight_type.name})"
            f"{self.priority.name}"
            f"lap={self.lap_number}"
            f"msg={self.message!r}"
        )

## SECTION 2: AnalyticsConfig

@dataclass
class AnalyticsConfig:
    ##Tyre Thresholds
    tyre_wear_warning_pct: float = 50.0     ## % wear triggers WARNING
    tyre_wear_critical_pct: float = 75.0    ## % wear triggers CRITICAL
    tyre_temp_cold_surface: int = 75        ## below this = cold
    tyre_temp_hot_surface: int = 115        ## above this = overheating
    tyre_blister_warning: int = 20          ## blister % triggers WARNING
    ## Fuel Thresholds
    fuel_save_delta_laps: float = -1.5      ## fuel_remaining_laps - laps_left < this -> save
    fuel_rich_delta_laps: float = 3.0       ## fuel surplus > this -> can go rich
    fuel_critical_laps: float = 0.5         ## fuel_remaining_laps below this -> critical
    ## ERS Thresholds
    ers_low_pct: float = 15.0               ## ERS store below this -> LOW warning
    ers_harvest_drop_pct: float = 30.0      ## if harvesting 30% less than avg -> warn
    ## Braking Thresholds
    brake_threshold: float = 0.75           ## brake input above this = braking event
    braking_early_delta_m: float = 15.0     ## braking > 15m earlier than best -> warn
    braking_late_delta_m: float = 10.0      ## braking > 10m later than best -> note
    min_speed_for_braking: int = 120        ## km/h minimum to track a braking event
    ## Strategy Thresholds
    undercut_gap_threshold_s: float = 2.2   ## gap to car ahead to flag undercut
    undercut_tyre_age_min: int = 8          ## rival must have at least this many tyre laps
    pit_window_warning_laps: int = 3        ## laps before latest pit -> warn
    ## Position Change
    gap_report_interval_s: float = 60.0     ## report live gap every N seconds
    ## Cooldowns: how long before insight can fire again
    cooldown_tyre_warning_s: float = 60.0
    cooldown_fuel_s: float = 20.0
    cooldown_ers_s: float = 15.0
    cooldown_braking_s: float = 10.0
    cooldown_strategy_s: float = 45
    cooldown_damage_s: float = 20.0
    cooldown_gap_s: float = 60.0

## SECTION 3: Base Analyser Class

class BaseAnalyser:
    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        self.state = state
        self.config = config
        ## Mpas InsightType -> wall-clock time of last fire
        self._last_fired: Dict[InsightType, float] = {}

    def analyse(self) -> List[Insight]:
        raise NotImplementedError
    
    def _on_cooldown(self, insight_type: InsightType, cooldown_s: float) -> bool:
        last = self._last_fired.get(insight_type, 0.0)
        return (time.perf_counter() - last) < cooldown_s
    
    def _mark_fired(self, insight_type: InsightType) -> None:
        self._last_fired[insight_type] = time.perf_counter()

    def _make_insight(
            self,
            insight_type: InsightType,
            priority: InsightPriority,
            data: Dict[str, Any],
            message: str,
            lap_number: Optional[int] = None,
            vehicle_idx: Optional[int] = None,
    ) -> Insight:
        p = self.state.player
        session_time = p.lap_data_ts or 0.0 if p else 0.0
        return Insight(
            insight_type = insight_type,
            priority = priority,
            timestamp = time.perf_counter(),
            session_time = session_time,
            data = data,
            message = message,
            lap_number = lap_number or (p.current_lap_num if p else None),
            vehicle_idx = vehicle_idx,
        )
    
    @property
    def player(self) -> Optional[CarState]:
        return self.state.player
    
    @property
    def session(self) -> SessionState:
        return self.state.session

## SECTION 4: LapAnalyser

class LapAnalyser(BaseAnalyser):
    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._last_known_lap: Optional[int] = None
        self._prev_best_ms: Optional[int] = None

    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None or p.current_lap_num is None:
            return []
        
        current_lap = p.current_lap_num

        ## Initialise on first call
        if self._last_known_lap is None:
            self._last_known_lap = current_lap
            return []
        
        ## No new lap
        if current_lap == self._last_known_lap:
            return []
        
        ## Lap num incremented
        completed_lap_num = self._last_known_lap
        self._last_known_lap = current_lap

        return self._on_lap_completed(completed_lap_num, p)
    
    def _on_lap_completed(self, lap_num: int, p: CarState) -> List[Insight]:
        insights = []
        lap_time_ms = p.last_lap_time_ms or 0
        if lap_time_ms == 0:
            return []
        
        lap_record = self.state.get_player_lap_record(lap_num)

        ## Lap Completed Insight
        insights.append(self._make_insight(
            insight_type = InsightType.LAP_COMPLETED,
            priority = InsightPriority.INFO,
            data = {
                "lap_number": lap_num,
                "lap_time_ms": lap_time_ms,
                "lap_time_str": _ms_to_time_str(lap_time_ms),
                "sector1_ms": lap_record.sector1_time_ms if lap_record else 0,
                "sector2_ms": lap_record.sector2_time_ms if lap_record else 0,
                "sector3_ms": lap_record.sector3_time_ms if lap_record else 0,
                "lap_valid": not (p.current_lap_invalid or False),
            },
            message = f"Lap {lap_num}: {_ms_to_time_str(lap_time_ms)}",
            lap_number = lap_num,
        ))

        ## Personal Best Check
        best = self.state.get_best_lap_record()
        if best and best.lap_number == lap_num:
            delta_ms = 0
            prev_best = self._prev_best_ms
            if prev_best:
                delta_ms = lap_time_ms - prev_best

            insights.append(self._make_insight(
                insight_type = InsightType.PERSONAL_BEST,
                priority = InsightPriority.INFO,
                data = {
                    "lap_time_ms": lap_time_ms,
                    "lap_time_str": _ms_to_time_str(lap_time_ms),
                    "delta_ms": delta_ms,
                    "delta_str": _format_delta_ms(delta_ms),
                },
                message = f"Personal best! {_ms_to_time_str(lap_time_ms)} ({_format_delta_ms(delta_ms)})",
                lap_number = lap_num,
            ))
        self._prev_best_ms = best.lap_time_ms if best else None

        ## Sector Delta vs Personal Best
        if lap_record and best and best.lap_number != lap_num:
            for sector_num, (cur_ms, best_ms, label) in enumerate([
                (lap_record.sector1_time_ms, best.sector1_time_ms, "S1"),
                (lap_record.sector2_time_ms, best.sector2_time_ms, "S2"),
                (lap_record.sector3_time_ms, best.sector3_time_ms, "S3"),
            ], start = 1):
                if cur_ms > 0 and best_ms > 0:
                    delta = cur_ms - best_ms
                    insights.append(self._make_insight(
                        insight_type = InsightType.SECTOR_DELTA,
                        priority = InsightPriority.INFO,
                        data = {
                            "sector": sector_num,
                            "label": label,
                            "current_ms": cur_ms,
                            "best_ms": best_ms,
                            "delta_ms": delta,
                            "delta_str": _format_delta_ms(delta)
                        },
                        message = f"{label}: {_format_delta_ms(delta)} vs PB",
                        lap_number = lap_num,
                    ))
            
            ## Theoretical Best
            theory_ms = self._compute_theoretical_best()
            if theory_ms > 0:
                delta_to_theory = lap_time_ms - theory_ms
                if delta_to_theory > 200:
                    insights.append(self._make_insight(
                        insight_type = InsightType.THEORETICAL_BEST_BEST,
                        priority = InsightPriority.INFO,
                        data = {
                            "theoretical_ms": theory_ms,
                            "theoretical_str": _ms_to_time_str(theory_ms),
                            "delta_ms": delta_to_theory,
                            "delta_str": _format_delta_ms(delta_to_theory),
                        },
                        message = (
                            f"Theoretical best: {_ms_to_time_str(theory_ms)} "
                            f"({_format_delta_ms(delta_to_theory)} off this lap)"
                        ),
                        lap_number = lap_num,
                    ))

            return insights
        
        def _compute_theoretical_best(self) -> int:
            history = self.sate.lap_history
            if len(history) < 2:
                return 0
            
            best_s1 = min((r.sector1_time_ms for r in history if r.sector1_time_ms > 0), default = 0)
            best_s2 = min((r.sector2_time_ms for r in history if r.sector2_time_ms > 0), default = 0)
            best_s3 = min((r.sector3_time_ms for r in history if r.sector3_time_ms > 0), default = 0)

            if best_s1 == 0 or best_s2 == 0 or best_s3 == 0:
                return 0
            return best_s1 + best_s2 + best_s3
        
## SECTION 5: Tyre Analyser

class TyreAnalyser(BaseAnalyser):
    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._wear_history: List[Tuple[int, float]] = []
        self._last_sampled_lap: Optional[int] = None
        self._cold_tyre_fired: bool = False
    
    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None or p.tyres_wear is None:
            return []
        
        insights = []
        max_wear = max(p.tyres_wear)
        current_lap = p.current_lap_num or 0

        if current_lap != self._last_sampled_lap and current_lap > 0:
            self._wear_history.append((current_lap, max_wear))
            self._last_sampled_lap = current_lap
            if len(self._wear_history) > 20:
                self._wear_history.pop(0)

        if max_wear >= self.config.tyre_wear_critical_pct:
            if not self._on_cooldown(InsightType.TYRE_WEAR_CRITICAL,
                                     self.config.cooldown_tyre_warning_s):
                laps_est = self._estimate_laps_remaining(max_wear)
                insights.append(self._make_insight(
                    insight_type = InsightType.TYRE_WEAR_CRITICAL,
                    priority = InsightPriority.CRITICAL,
                    data = {
                        "max_wear_pct": max_wear,
                        "wear_all": p.tyres_wear,
                        "laps_remaining": laps_est,
                        "compound": p.visual_tyre_compound,
                    },
                    message = (
                        f"Tyre wear critical: {max_wear:.0f}%. "
                        f"Estimated {laps_est} laps remaining."
                    ),
                ))
                self._mark_fired(InsightType.TYRE_WEAR_CRITICAL)
        
        elif max_wear >= self.config.tyre_wear_warning_pct:
            if not self._on_cooldown(InsightType.TYRE_WEAR_WARNING,
                                     self.config.cooldown_tyre_warning_s):
                laps_est = self._estimate_laps_remaining(max_wear)
                insights.append(self._make_insight(
                    insight_type = InsightType.TYRE_WEAR_WARNING,
                    priority = InsightPriority.WARNING,
                    data = {
                        "max_wear_pct": max_wear,
                        "wear_all": p.tyres_wear,
                        "laps_remaining": laps_est,
                        "compound": p.visual_tyre_compound,
                    },
                    message = (
                        f"Tyre wear at {max_wear:.0f}%. "
                        f"Estimated {laps_est} laps left in this set."
                    ),
                ))
                self._mark_fired(InsightType.TYRE_WEAR_WARNING)

            if len(self._wear_history) >= 5:
                if not self._on_cooldown(InsightType.TYRE_DEGREDATION_RATE, 60.0):
                    rate = self._compute_wear_rate()
                    if rate > 0:
                        laps_to_critical = (
                            (self.config.tyre_wear_critical_pct - max_wear) / rate
                            if rate > 0 else 99
                        )
                        insights.append(self._make_insight(
                            insight_type = InsightType.TYRE_DEGREDATION_RATE,
                            priority = InsightPriority.ADVISORY,
                            data = {
                                "wear_per_lap_pct": round(rate, 2),
                                "laps_to_critical": round(laps_to_critical,1 ),
                                "current_wear_pct": max_wear,
                            },
                            message = (
                                f"Tyre degredation: {rate:.1f}% per lap. "
                                f"~{laps_to_critical:.0f} laps to critical."
                            ),
                        ))
                        self._mark_fired(InsightType.TYRE_DEGREDATION_RATE)

            insights += self._check_temperatures(p)

            if p.tyre_blisters is not None:
                max_blister = max(p.tyre_blisters)
                if max_blister >= self.config.tyre_blister_warning:
                    if not self._on_cooldown(InsightType.TYRE_BLISTER_WARNING,
                                             self.config.cooldown_tyre_warning_s):
                        insights.append(self._make_insight(
                            insight_type = InsightType.TYRE_BLISTER_WARNING,
                            priority = InsightPriority.WARNING,
                            data = {
                                "max_blister_pct": max_blister,
                                "blisters_all": p.tyre_blisters,
                            },
                            message = f"Tyre blistering detected: {max_blister}%.",
                        ))
                        self._mark_fired(InsightType.TYRE_BLISTER_WARNING)

            return insights
        
        def _check_temperatures(self, p: CarState) -> List[Insight]:
            insights = []
            if p.tyres_surface_temp is None:
                return []
            avg_temp = sum(p.tyres_surface_temp) / 4
            cold = self.config.tyre_temp_cold_surface
            hot = self.config.tyre_tempt_hot_surface
            if avg_temp < cold:
                if not self._cold_tyre_fired:
                    if not self._on_cooldown(InsightType.TYRE_TEMP_COLD, 60.0):
                        insights.append(self._make_insight(
                            insight_type = InsightType.TYRE_TEMP_COLD,
                            priority = InsightPriority.ADVISORY,
                            data = {
                                "avg_temp_c": round(avg_temp, 1),
                                "temps_all": p.tyres_surface_temp,
                                "target_min_c": cold,
                            },
                            message = (
                                f"Tyres cold: {avg_temp:.0f}°C"
                                f"Target above {cold}°C"
                                ),
                        ))
                        self._mark_fired(InsightType.TYRE_TEMP_COLD)
                        self._cold_tyre_fired = True
            elif avg_temp >= cold + 10:
                self._cold_tyre_fired = False

            if avg_temp < hot:
                            if not self._cold_tyre_fired:
                                if not self._on_cooldown(InsightType.TYRE_TEMP_OVERHEATING, 30.0):
                                    insights.append(self._make_insight(
                                        insight_type = InsightType.TYRE_TEMP_OVERHEATING,
                                        priority = InsightPriority.WARNING,
                                        data = {
                                            "avg_temp_c": round(avg_temp, 1),
                                            "temps_all": p.tyres_surface_temp,
                                            "target_max_c": hot,
                                        },
                                        message = (
                                            f"Tyres overheating: {avg_temp:.0f}°C"
                                            f"Ease up to protect the rubber"
                                            ),
                                    ))
                                    self._mark_fired(InsightType.TYRE_TEMP_OVERHEATING)
            return insights

        def _estimate_laps_remaining(self, current_wear: float) -> float:
            rate = self._compute_wear_rate()
            if rate <= 0:
                p = self.player
                age = p.tyres_age_laps if p and p.tyres_age_laps else 1
                if age > 0 and current_wear > 0:
                    rate = current_wear / age
                else:
                    return 99.0

            remaining = (self.config.tyre_wear_critical_pct - current_wear) / rate
            return max (0.0, round(remaining, 1))

        def _compute_wear_rate(self) -> float:
            if len(self._wear_history) < 3:
                return 0.0
            laps = [x[0] for x in self.wear_history]
            wears = [x[1] for x in self.wear_history]
            n = len(laps)
            mean_lap = sum(laps)/n
            mean_wear = sum(wears)/n
            numerator = sum((1-mean_lap) * (w-mean_wear) for 1, w in zip(laps, wears))
            denominator = sum((1-mean_lap) ** 2 for l in laps)
            if denominator == 0:
                return 0.0
            slope = numerator/denominator
            return max(0.0, slope)

        def reset_for_new_stint(self) -> None:
            self._wear_history.clear()
            self._last_sampled_lap = None
            self._cold_tyre_fired = False
            self._last_fired.clear()

## SECTION 6: Fuel Analyser

class FuelAnalyser(BaseAnalyser):
    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._fuel_per_lap_history: List[float] = []
        self._lap_lap_fuel: Optional[float] = None
        self._last_lap_num: Optional[int] = None

    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None:
            return []
        if not self.session.is_race:
            return []
        if p.fuel_remaining_laps is None or p.fuel_remaining_laps == 0:
            return []
        insights = []

        self._track_consumption(p)

        laps_left = self.state.laps_remaining()
        if laps_left is None:
            return []
        delta = p.fuel_remaining_laps - laps_left

        if p.fuel_remaining_laps < self.config.fuel_critical_laps:
            if not self._on_cooldown(InsightType.FUEL_CRITICAL, self.config.cooldown_fuel_s):
                insights.append(self._make_insight(
                    insight_type= InsightType.FUEL_CRITICAL,
                    priority = InsightPriority.CRITICAL,
                    data = {
                        "fuel_remaining_laps": round(p.fuel_remaining_laps, 2),
                        "laps_left": laps_left,
                        "delta_laps": round(delta, 2),
                        "fuel_in_tank_kg": round(p.fuel_in_tank or 0, 2),
                    },
                    message = (
                        f"CRITICAL: Fuel for only {p.fuel_remaining_laps:.1f} laps. "
                        f"{laps_left} laps remaining. Push to lean immediately"
                    ),
                ))
                self._mark_fired(InsightType.FUEL_CRITICAL)

        elif delta < self.config.fuel_save_delta_laps:
                    if not self._on_cooldown(InsightType.FUEL_SAVE_REQUIRED, self.config.cooldown_fuel_s):
                        laps_short = abs(delta)
                        insights.append(self._make_insight(
                            insight_type= InsightType.FUEL_SAVE_REQUIRED,
                            priority = InsightPriority.WARNING,
                            data = {
                                "fuel_remaining_laps": round(p.fuel_remaining_laps, 2),
                                "laps_left": laps_left,
                                "delta_laps": round(delta, 2),
                                "current_mix": p.fuel_mix,
                            },
                            message = (
                                f"Fuel save required. Short by {laps_short:.1f} laps. "
                                f"Switch to lean mix"
                            ),
                        ))
                        self._mark_fired(InsightType.FUEL_SAVE_REQUIRED)

        elif delta > self.config.fuel_save_delta_laps:
                            if not self._on_cooldown(InsightType.FUEL_RICH_AVAILABLE, self.config.cooldown_fuel_s):
                                insights.append(self._make_insight(
                                    insight_type= InsightType.FUEL_RICH_AVAILABLE,
                                    priority = InsightPriority.ADVISORY,
                                    data = {
                                        "fuel_remaining_laps": round(p.fuel_remaining_laps, 2),
                                        "laps_left": laps_left,
                                        "delta_laps": round(delta, 2),
                                        "surplus_kg": round((delta * self._avg_fuel_per_lap()),  2),
                                    },
                                    message = (
                                        f"Fuel surplus of {delta:.1f} laps. "
                                        f"Switch to rich mix"
                                    ),
                                ))
                                self._mark_fired(InsightType.FUEL_RICH_AVAILABLE)

        else:
            if not self._on_cooldown(InsightType.FUEL_DELTA, 60.0):
                sign = "+" if delta >= 0 else ""
                insights.append(self._make_insight(
                    insight_type= InsightType.FUEL_DELTA,
                    priority = InsightPriority.INFO,
                    data = {
                        "fuel_remaining_laps": round(p.fuel_remaining_laps, 2),
                        "laps_left": laps_left,
                        "delta_laps": round(delta, 2),
                    },
                    message = f"Fuel delta: {sign}{delta:.1f} laps."
                ))
                self._mark_fired(InsightType.FUEL_DELTA)

        return insights

    def _track_consumption(self, p:CarState) -> None:
        lap = p.current_lap_num
        fuel = p.fuel_in_tank
        if lap is None or fuel is None:
            return
        if self._last_lap_num is not None and lap != self._last_lap_num:
            if self._lap_lap_fuel is not None and fuel < self._lap_lap_fuel:
                consumed = self._lap_lap_fuel - fuel
                self._fuel_per_lap_history.append(consumed)
                if len(self._fuel_per_lap_history) > 15:
                    self._fuel_per_lap_history.pop(0)

        self._lap_lap_fuel = fuel
        self._last_lap_num = lap

    def _avg_fuel_per_lap(self) -> float:
        if not self._fuel_per_lap_history:
            return 1.8
        return sum(self._fuel_per_lap_history) / len(self._fuel_per_lap_history)

## SECTION 7: ERS Analyser

class ERSAnalyser(BaseAnalyser):
    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._harvest_per_lap: List[float] = []
        self._deploy_per_lap: List[float] = []
        self._last_lap_num: Optional[int] = None

    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None or p.ers_store_energy is None:
            return []

        insights = []
        store_pct = p.ers_store_percent or 0.0
        self._track_lap_ers(p)
        if store_pct < self.config.ers_low_pct:
            if not self._on_cooldown(InsightType.ERS_STORE_LOW, self.config.cooldown_ers_s):
                insights.append(self._make_insight(
                    insight_type = InsightType.ERS_STORE_LOW,
                    priority = InsightPriority.ADVISORY,
                    data = {
                        "store_pct": round(store_pct, 1),
                        "store_joules": round(p.ers_store_energy, 0),
                        "deploy_mode": p.ers_mode_name,
                    },
                    message = (
                        f"ERS store low {store_pct:.0f}%"
                        f"Consider harvesting mode"
                    ),
                ))
                self._mark_fired(InsightType.ERS_STORE_LOW)

        if len(self._harvest_per_lap) >= 4:
            avg_harvest = sum(self._harvest_per_lap) / len(self._harvest_per_lap)
            last_harvest = self._harvest_per_lap[-1]
            if avg_harvest > 0:
                drop_pct = (avg_harvest - last_harvest) / avg_harvest * 100
                if drop_pct > self.config.ers_harvest_drop_pct:
                    if not self._on_cooldown(InsightType.ERS_HARVEST_LOW, self.config.cooldown_ers_s * 2):
                        insights.append(self._make_insight(
                            insight_type = InsightType.ERS_HARVEST_LOW,
                            priority = InsightPriority.ADVISORY,
                            data = {
                                "last_harvest_kj": round(last_harvest/1000, 1),
                                "avg_harvest_kj": round(avg_harvest/1000, 1),
                                "drop_pct": round(drop_pct, 1),
                            },
                            message = (
                                f"ERS harvest down {drop_pct:.0f}% vs average"
                                f"Check braking zones for harvest opportunity"
                            ),
                        ))
                        self._mark_fired(InsightType.ERS_HARVEST_LOW)

        return insights

    def _track_lap_ers(self, p: CarState) -> None:
        lap = p.current_lap_num
        if lap is None or lap == self._last_lap_num:
            return
        if p.ers_harvested_lap_mguk is not None:
            total_harvest = (p.ers_harvested_lap_mguk or 0) + (p.ers_harvested_lap_mguh or 0)
            self._harvest_per_lap.append(total_harvest)
            if len(self._harvest_per_lap) > 20:
                self._harvest_per_lap.pop(0)
        if p.ers_deployed_lap is not None:
            self._deploy_per_lap.append(p.ers_deployed_lap)
            if len(self._deploy_per_lap) > 20:
                self._deploy_per_lap.pop(0)

        self._last_lap_num = lap

## SECTION 8: Braking Analyser

class BrakingAnalyser(BaseAnalyser):
    POSITION_BIN_M = 10.0

    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._in_braking_event: bool = False
        self._event_start_dist: float = 0.0
        self._event_start_speed: int = 0
        self._event_lap: int = 0

        self._best_profile: Dict[int, Dict] = {}

        self._current_lap_events: List[Dict] = []
        self._last_lap_num: Optional[int] = None

    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None or p.brake is None or p.lap_distance is None:
            return []
        if not p.is_on_track:
            return []
        insights = []
        current_lap = p.current_lap_num or 0

        if self._last_lap_num is not None and current_lap != self._last_lap_num:
            insights += self._evaluate_lap_braking(self._last_lap_num)
            self._update_best_profile()
            self._current_lap_events.clear()

        self._last_lap_num = current_lap

        braking = (p.brake > self.config.brake_threshold and (p.speed_kph or 0) > self.config.min_speed_for_braking)

        if braking and not self._in_braking_event:
            self._in_braking_event = True
            self._event_start_dist = p.lap_distance
            self._event_start_speed = p.speed_kph or 0
            self._event_lap = current_lap
        elif not braking and self._in_braking_event:
            self._in_braking_event = False
            self._current_lap_events.append({
                "dist_m": self._event_start_dist,
                "speed_kph": self._event_start_speed,
                "lap": self._event_lap,
            })
        return insights

    def _evaluate_lap_braking(self, lap_num: int) -> List[Insight]:
        insights = []
        if not self._best_profile or not self._current_lap_events:
            return []
        for event in self._current_lap_events:
            bin_key = self._dist_to_bin(event["dist_m"])
            best = self._best_profile.get(bin.key)
            if best is None or best["count"] < 3:
                continue
            delta_m = event["dist_m"] - best["best_dist_m"]
            if delta_m < -self.confih.braking_early_delta_m:
                if not self._on_cooldown(InsightType.BRAKING_POINT_EARLY,
                                         self.config.cooldown_braking_s):
                    insights.append(self._make_insight(
                        insight_type = InsightType.BRAKING_POINT_EARLY,
                        priority = InsightPriority.ADVISORY,
                        data = {
                            "position_m": round(event["dist_m"], 1),
                            "best_dist_m": round(best["best_dist_m"], 1),
                            "delta_m": round(delta_m, 1),
                            "entry_speed": event["speed_kph"],
                            "lap_number": lap_num,
                        },
                        message = (
                            f"Braking {abs(delta_m):.0f}m early at "
                            f"{event['dist_m']:0.f}m "
                            f"({event['speed_kph']}kph entry). "
                            f"Best is {best['best_dist_m']:.0f}m."
                        ),
                        lap_number = lap_num,
                    ))
                    self._mark_fired(InsightType.BRAKING_POINT_EARLY)
        return insights

    def _update_best_profile(self) -> None:
        for event in self._current_lap_events:
            bin_key = self._dist_to_bin(event["dist_m"])
            existing = self._best_profile.get(bin_key)
            if existing is None:
                self._best_profile[bin_key] = {
                    "best_dist_m": event["dist_m"],
                    "best_speed": event["speed_kph"],
                    "count": 1,
                }
            else:
                if event["dist_m"] > existing["best_dist_m"]:
                    existing["best_dist_m"] = event["dist_m"]
                    existing["best_speed"] = event["speed_kph"]
                existing["count"] += 1

    def _dist_to_bin(self, dist_m: float) -> int:
        return int(dist_m / self.POSITION_BIN_M)

    def get_braking_profile(self) -> Dict:
        return dict(self._best_profile)

## SECTION 9: Strategy Analyser

class StrategyAnalyser(BaseAnalyser):

    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._last_position: Optional[int] = None
        self._last_gap_report_ts: float = 0.0
        self._undercut_flagged: bool = False

    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None:
            return []
        insights = []
        if self.session.is_race:
            insights += self._check_pit_window(p)
            insights += self._check_undercut(p)
            insights += self._check_position_change(p)
            insights += self._check_gap_report(p)
        return insights

    def _check_pit_window(self, p: CarState) -> List[Insight]:
        insights = []
        ideal = self.session.pit_stop_window_ideal_lap
        latest = self.session.pit_stop_window_latest_lap
        lap = p.current_lap_num
        if ideal is None or latest is None or lap is None:
            return []
        if (p.num_pit_stops or 0) >= 1 and self.session.total_laps and self.session.total_laps < 30:
            return[]
        if lap == ideal:
            if not self._on_cooldown(InsightType.PIT_WINDOW_OPEN, self.config.cooldown_strategy_s):
                insights.append(self._make_insight(
                    insight_type = InsightType.PIT_WINDOW_OPEN,
                    priority = InsightPriority.ADVISORY,
                    data = {
                        "ideal_lap": ideal,
                        "latest_lap": latest,
                        "current_lap": lap,
                        "rejoin_pos": self.session.pit_stop_rejoin_position,
                    },
                    message = (
                        f"Pit window open. Ideal this lap. "
                        f"Latest lap {latest}. "
                        f"Rejoin P{self.session.pit_stop_rejoin_position}."
                    ),
                ))
                self._mark_fired(InsightType.PIT_WINDOW_OPEN)

        laps_to_latest = (latest - lap) if latest and lap else None
        if laps_to_latest is not None and 0 < laps_to_latest <= self.config.pit_window_warning_laps:
            if not self._on_cooldown(InsightType.PIT_WINDOW_CLOSING, self.config.cooldown_strategy_s):
                            insights.append(self._make_insight(
                                insight_type = InsightType.PIT_WINDOW_CLOSING,
                                priority = InsightPriority.WARNING,
                                data = {
                                    "latest_lap": latest,
                                    "current_lap": lap,
                                    "laps_to_latest": laps_to_latest,
                                },
                                message = (
                                    f"Pit window closing. Must pit within "
                                    f"{laps_to_latest} laps. Latest: lap {latest}."
                                ),
                            ))
                            self._mark_fired(InsightType.PIT_WINDOW_CLOSING)
        return insights

    def _check_undercut(self, p: CarState) -> List[Insight]:
        insights = []
        gap_s = self.state.player_gap_to_car_ahead()
        if gap_s is None:
            return []
        if gap_s > self.config.undercut_gap_threshold_s:
            self._undercut_flagged = False
            return []
        if p.car_position is None or p.car_position <= 1:
            return []
        car_ahead = self.state.get_car_by_position(p.car_position - 1)
        if car_ahead is None:
            return []
        their_tyre_age = car_ahead.tyres_age_laps or 0
        if their_tyre_age < self.config.undercut_tyre_age_min:
            return []
        if not self._undercut_flagged:
            if not self._on_cooldown(InsightType.UNDERCUT_WINDOW, self.config.cooldown_strategy_s):
                insights.append(self._make_insight(
                    insight_type = InsightType.UNDERCUT_WINDOW,
                    priority = InsightPriority.ADVISORY,
                    data = {
                        "gap_s": round(gap_s, 3),
                        "car_ahead_idx": car_ahead.vehicle_index,
                        "car_ahead_name": car_ahead.name or "?",
                        "their_tyre_age": their_tyre_age,
                        "their_compound": car_ahead.visual_tyre_compound,
                        "our_tyre_age": p.tyres_age_laps or 0,
                    },
                    message = (
                        f"Undercut window: {gap_s:.2f}s to {car_ahead.name or 'car ahead'}. "
                        f"They are on {car_ahead.visual_tyre_compound} "
                        f"aged {their_tyre_age} laps."
                    ),
                ))
                self._mark_fired(InsightType.UNDERCUT_WINDOW)
                self._undercut_flagged = True
        return insights

    def _check_position_change(self, p: CarState) -> List[Insight]:
        insights = []
        current_pos = p.car_position
        if self._last_position is None:
            self._last_position = current_pos
            return []
        if current_pos is None or current_pos == self._last_position:
            return []
        gained = current_pos < self._last_position
        insights.append(self._make_insight(
            insight_type = InsightType.POSITION_GAINED if gained else InsightType.POSITION_LOST,
            priority = InsightPriority.INFO,
            data = {
                "new_position": current_pos,
                "old_position": self._last_position,
                "delta": self._last_position - current_pos,
            },
            message = (
                f"Up to P{current_pos}." if gained
                else f"Down to P{current_pos}."
            ),
        ))
        self._last_position = current_pos
        return insights

    def _check_gap_report(self, p: CarState) -> List[Insight]:
        insights = []
        now = time.perf_counter()
        if now - self._last_gap_report_ts < self.config.gap_report_interval_s:
            return []
        gap_ahead = self.state.player_gap_to_car_ahead()
        gap_leader = self.state.player_gap_to_leader()
        if gap_ahead is not None:
            self._last_gap_report_ts = now
            insights.append(self._make_insight(
                insight_type = InsightType.GAP_TO_AHEAD,
                priority = InsightPriority.INFO,
                data = {
                    "gap_ahead_s": round(gap_ahead, 3),
                    "gap_leader_s": round(gap_leader, 3) if gap_leader else None,
                    "position": p.car_position,
                },
                message = (
                    f"Gap to car ahead: {gap_ahead:.2f}s."
                    + (f" Leader: {gap_leader:.2f}s." if gap_leader is not None else "")
                ),
            ))
        return insights

## SECTION 10: Damage Analyser

class DamageAnalyser(BaseAnalyser):

    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._last_fl_wing: int = 0
        self._last_fr_wing: int = 0
        self._last_rear_wing: int = 0
        self._last_floor: int = 0
        self._last_engine: int = 0
        self._last_gearbox: int = 0
        self._engine_blown_alerted: bool = False
        self._drs_fault_alerted: bool = False

    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None:
            return []
        insights = []
        if p.engine_blown and not self._engine_blown_alerted:
            insights.append(self._make_insight(
                insight_type = InsightType.ENGINE_BLOWN,
                priority = InsightPriority.CRITICAL,
                data = {"engine_blown": True},
                message = "ENGINE FAILURE. Car is done.",
            ))
            self._engine_blown_alerted = True
        if p.drs_fault and not self._drs_fault_alerted:
            insights.append(self._make_insight(
                insight_type = InsightType.DRS_FAULT,
                priority = InsightPriority.WARNING,
                data = {"drs_fault": True},
                message = "DRS fault detected."
            ))
            self._drs_fault_alerted = True
        elif not p.drs_fault:
            self._drs_fault_alerted = False

        fl = p.front_left_wing_damage or 0
        fr = p.front_right_wing_damage or 0
        rear = p.rear_wing_damage or 0
        if fl > self._last_fl_wing + 5 or fr > self._last_fr_wing + 5:
            if not self._on_cooldown(InsightType.DAMAGE_WING, self.config.cooldown_damage_s):
                avg_front = (fl + fr)/2
                insights.append(self._make_insight(
                    insight_type = InsightType.DAMAGE_WING,
                    priority = InsightPriority.WARNING if avg_front > 30 else InsightPriority.INFO,
                    data = {
                        "front_left_pct": fl,
                        "front_right_pct": fr,
                        "rear_pct": rear,
                    },
                ))
                self._mark_fired(InsightType.DAMAGE_WING)
        self._last_fl_wing = fl
        self._last_fr_wing = fr
        self._last_rear_wing = rear

        eng = p.engine_damage or 0
        if eng > self._last_engine + 10:
            if not self._on_cooldown(InsightType.DAMAGE_ENGINE, self.config.cooldown_damage_s):
                insights.append(self._make_insight(
                    insight_type = InsightType.DAMAGE_ENGINE,
                    priority = InsightPriority.WARNING if eng > 50 else InsightPriority.INFO,
                    data = {"engine_damage_pct": eng},
                    message = f"Engine damage: {eng}%."
                ))
                self._mark_fired(InsightType.DAMAGE_ENGINE)
        self._last_engine = eng

        gb = p.gear_box_damage or 0
        if gb > self._last_gearbox + 10:
            if not self._on_cooldown(InsightType.DAMAGE_GEARBOX, self.config.cooldown_damage_s):
                insights.append(self._make_insight(
                    insight_type = InsightType.DAMAGE_GEARBOX,
                    priority = InsightPriority.WARNING if gb > 50 else InsightPriority.INFO,
                    data = {"gearbox_damage_pct": gb},
                    message = f"Gearbox damage: {gb}%."
                ))
                self._mark_fired(InsightType.DAMAGE_ENGINE)
        self._last_gearbox = gb

        return insights

## SECTION 11: Event Analyser

class EventAnalyser(BaseAnalyser):

    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._processed_event_times: deque = deque(maxlen=100)

    def analyse(self) -> List[Insight]:
        insights = []
        player_idx = self.state.player_index
        for event in self.state.events:
            if event.wall_time in self._processed_event_times:
                continue
            self._processed_event_times.append(event.wall_time)
            code = event.event_code

            if code == "SCAR":
                insight = self._handle_safety_car(event)
            elif code == "RDFL":
                insight = self._handle_red_flag(event)
            elif code == "FTLP":
                insight = self._handle_fastest_lap(event, player_idx)
            elif code == "OVTK":
                insight = self._handle_overtake(event, player_idx)
            else:
                insight = None
            if insight:
                insights.append(insight)
        return insights

    def _handle_safety_car(self, event) -> Optional[Insight]:
        details = event.details
        sc_type_map = {0: "No Safety Car", 1: "Safety Car", 2: "Virtual Safety Car", 3: "Formation Lap"}
        event_type_map = {0: "deployed", 1: "returning", 2: "returned", 3: "resume race"}
        sc_name = sc_type_map.get(getattr(details, "safety_car_type", 0), "Safety Car")
        ev_name = event_type_map.get(getattr(details, "event_type", 0), "deployed")

        if ev_name in ("deployed",):
            return self._make_insight(
                insight_type = InsightType.SAFETY_CAR_DEPLOYED,
                priority = InsightPriority.WARNING,
                data = {"event_type": ev_name},
                message = f"{sc_name} {ev_name}. Prepare for restart.",
            )
        return None

    def _handle_red_flag(self, event) -> Optional[Insight]:
        return self._make_insight(
            insight_type = InsightType.RED_FLAG,
            priority = InsightPriority.CRITICAL,
            data = {},
            message = "Red flag. Session suspended.",
        )

    def _handle_fastest_lap(self, event, player_idx: int) -> Optional[Insight]:
        details = event.details
        if details is None:
            return None
        is_player = (getattr(details, "vehicle_idx", -1) == player_idx)
        if not is_player:
            return None
        lap_time = getattr(details, "lap_time", 0)
        return self._make_insight(
            insight_type = InsightType.FASTEST_LAP,
            priority = InsightPriority.INFO,
            data = {
                "lap_time_s": lap_time,
                "lap_time_str": _ms_to_time_str(int(lap_time * 1000)),
            },
            message = f"Fastest lap of the race: {_ms_to_time_str(int(lap_time*1000))}.",
        )

    def _handle_overtake(self, event, player_idx: int) -> Optional[Insight]: 
        details = event.details
        if details is None:
            return None
        return self._make_insight(
            insight_type = InsightType.OVERTAKE_DETECTED,
            priority = InsightPriority.INFO,
            data = {
                "overtaking_idx": getattr(details, "overtaking_vehicle_idx", None),
                "being_overtaken_idx": getattr(details, "being_overtaken_vehicle_idx", None),
            },
            message = "Overtake confirmed."
        )

## Section 12: Analytics Engine

class AnalyticsEngine:

    INSIGHT_HISTORY_SIZE = 200

    def __init__(self, state: TelemetryState, config: Optional[AnalyticsConfig] = None):
        self.state = state
        self.config = config or AnalyticsConfig()
        self._analysers: List[BaseAnalyser] = [
            LapAnalyser(state, self.config),
            TyreAnalyser(state, self.config),
            FuelAnalyser(state, self.config),
            ERSAnalyser(state, self.config),
            BrakingAnalyser(state, self.config),
            StrategyAnalyser(state, self.config),
            DamageAnalyser(state, self.config),
            EventAnalyser(state, self.config),
        ]
        self.insight_history: deque = deque(maxlen=self.INSIGHT_HISTORY_SIZE)
        self._tick_count: int = 0
        self._last_tick_ts: float = 0.0

    def tick(self) -> List[Insight]:
        if not self.state.is_live:
            return []
        if self.state.player is None:
            return []
        all_insights: List[Insight] = []
        for analyser in self._analysers:
            try:
                results = analyser.analyse()
                all_insights.extend(results)
            except Exception as e:
                pass

        all_insights.sort(key=lambda i: i.priority.value)

        self.insight_history.extend(all_insights)

        self._tick_count += 1
        self._last_tick_ts = time.perf_counter()

        return all_insights

    def get_recent_insights(self, n: int = 10, priority: Optional[InsightPriority] = None, insight_type: Optional[InsightType] = None) -> List[Insight]:
        results = list(self.insight_history)
        if priority is not None:
            results = [i for i in results if i.priority == priority]
        if insight_type is not None:
            results = [i for i in results if i.insight_type == insight_type]
        return results[-n:][::-1]

    def get_braking_profile(self) -> Dict:
        for analyser in self._analysers:
            if isinstance(analyser, BrakingAnalyser):
                return analyser.get_braking_profile()
        return {}

    def notify_new_stint(self) -> None:
        for analyser in self._analysers:
            if isinstance(analyser, TyreAnalyser):
                analyser.reset_for_new_stint()

    @property
    def tick_count(self) -> int:
        return self._tick_count

    def __repr__(self) -> str:
        return (
            f"AnalysticsEngine("
            f"ticks={self._tick_count}, "
            f"analysers={len(self._analysers)}, "
            f"history={len(self.insight_history)}"
            f")"
        )

## UTILITY HELPERS

def _format_delta_ms(delta_ms: int) -> str:
    if delta_ms == 0:
        return "=0.000"
    sign = "+" if delta_ms > 0 else "-"
    abs_ms = abs(delta_ms)
    secs = abs_ms // 1000
    millis = abs_ms % 1000
    if secs > 0:
        return f"{sign}{secs}.{millis:03d}"
    return f"{sign}0.{millis:03d}"