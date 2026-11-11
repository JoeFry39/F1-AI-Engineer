from __future__ import annotations
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Tuple, Any, Callable, Deque

from telemetry.telemetry_state import(
    TelemetryState,
    CarState,
    SessionState,
    LapRecord,
)
from telemetry.packet_parser import(
    _ms_to_time_str,
    TYRE_COMPOUNDS_VISUAL,
    ERS_DEPLOY_MODES,
)

logger = logging.getLogger(__name__)

def _now() -> float:
    return time.perf_counter()

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
    PENALTY_ISSUED = auto()
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
    RETIREMENT = auto()
    RIVAL_STATUS = auto()

@dataclass
class Insight:
    insight_type: InsightType           ## What the insight type is
    priority: InsightPriority           ## Priority of insight
    timestamp: float                    ## _now() when generated
    session_time: float                 ## session clock (seconds)
    data: Dict[str, Any]                ## payload - keys depend on insight_type
    message: str = ""                   ## pre-built plain-English summary
    lap_number: Optional[int] = None    ## lap this insight relates to
    vehicle_idx: Optional[int] = None   ## car this insight relates to (None = player)
    corner_id: Optional[int] = None     ## set when the insight is about a specific corner
    corner_name: Optional[str] = None

    def __repr__(self) -> str:
        return(
            f"Insight({self.insight_type.name})"
            f"{self.priority.name}"
            f"lap={self.lap_number}"
            f"msg={self.message!r}"
        )

## SECTION 2: AnalyticsConfig

FEEDBACK_MULTIPLIER = {"minimal": 2.0, "normal": 1.0, "detailed": 0.5}

@dataclass
class AnalyticsConfig:
    feedback_level: str = "normal"          ## how chatty the system is
    ##Tyre Thresholds
    tyre_wear_warning_steps: Tuple[int, ...] = (50, 60, 70)     ## % wear triggers WARNING
    tyre_wear_critical_steps: Tuple[int, ...] = (75, 85, 92)    ## % wear triggers CRITICAL
    tyre_temp_cold_surface: int = 75                            ## below this = cold
    tyre_temp_hot_surface: int = 115                            ## above this = overheating
    tyre_temp_hysteresis: int = 10
    tyre_blister_warning: int = 20                              ## blister % triggers WARNING
    tyre_min_samples_for_rate: int = 4
    ## Fuel Thresholds
    fuel_save_delta_laps: float = -1.5                          ## fuel_remaining_laps - laps_left < this -> save
    fuel_rich_delta_laps: float = 3.0                           ## fuel surplus > this -> can go rich
    fuel_critical_laps: float = 0.5                             ## fuel_remaining_laps below this -> critical
    fuel_worsen_steps_laps: float = 0.5                         ## repeat a fuel-save call early
    ## ERS Thresholds
    ers_low_pct: float = 15.0                                   ## ERS store below this -> LOW warning
    ers_rearm_pct: float = 30.0
    ers_harvest_drop_pct: float = 30.0                          ## if harvesting 30% less than avg -> warn
    ## Braking Thresholds
    brake_threshold: float = 0.75                               ## brake input above this = braking event
    brake_release_threshold: float = 0.30
    braking_early_delta_m: float = 15.0                         ## braking > 15m earlier than best -> warn
    braking_late_delta_m: float = 15.0                          ## braking > 15m later than best -> note
    braking_match_window_m: float = 80.0
    min_speed_for_braking: int = 120                            ## km/h minimum to track a braking event
    braking_corner_min_laps: int = 3                            ## same corner coached once per N laps
    braking_max_per_lap: int = 2                                ## at most this many corners per lap
    ## Strategy Thresholds
    undercut_gap_threshold_s: float = 2.2                       ## gap to car ahead to flag undercut
    undercut_tyre_age_min: int = 8                              ## rival must have at least this many tyre laps
    pit_window_warning_laps: int = 3                            ## laps before latest pit -> warn
    ## Cooldowns: how long before insight can fire again
    cooldown_tyre_critical_s: float = 120.0
    cooldown_tyre_temp_s: float = 150.0
    cooldown_tyre_rate_s: float = 300.0
    cooldown_blister_s: float = 180.0
    cooldown_fuel_s: float = 150.0
    cooldown_fuel_critical_s: float = 60.0
    cooldown_fuel_delta_s: float = 300.0
    cooldown_ers_s: float = 90.0
    cooldown_ers_harvest_s: float = 240.0
    cooldown_braking_global_s: float = 45.0
    cooldown_strategy_s: float = 150
    cooldown_damage_s: float = 90.0
    cooldown_gap_s: float = 150.0
    cooldown_position_s: float = 20.0

    def cd(self, base_s: float) -> float:
        return base_s * FEEDBACK_MULTIPLIER.get(self.feedback_level, 1.0)

## SECTION 3: Base Analyser Class

class BaseAnalyser:
    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        self.state = state
        self.config = config
        ## Mpas InsightType -> wall-clock time of last fire
        self._last_fired: Dict[Tuple[InsightType, str], float] = {}

    def analyse(self) -> List[Insight]:
        raise NotImplementedError
    
    def _on_cooldown(self, insight_type: InsightType, cooldown_s: float, key: str = "") -> bool:
        last = self._last_fired.get((insight_type, key))
        return last is not None and (_now() - last) < cooldown_s
    
    def _mark_fired(self, insight_type: InsightType, key: str = "") -> None:
        self._last_fired[(insight_type, key)] = _now()

    def _make_insight(
            self,
            insight_type: InsightType,
            priority: InsightPriority,
            data: Dict[str, Any],
            message: str,
            lap_number: Optional[int] = None,
            vehicle_idx: Optional[int] = None,
            corner_id: Optional[int] = None,
            corner_name: Optional[str] = None,
    ) -> Insight:
        p = self.state.player
        session_time = (p.lap_data_ts or 0.0) if p else 0.0
        return Insight(
            insight_type = insight_type,
            priority = priority,
            timestamp = _now(),
            session_time = session_time,
            data = data,
            message = message,
            lap_number = lap_number if lap_number is not None else (p.current_lap_num if p else None),
            vehicle_idx = vehicle_idx,
            corner_id = corner_id,
            corner_name = corner_name,
        )
    
    @property
    def player(self) -> Optional[CarState]:
        return self.state.player
    
    @property
    def session(self) -> SessionState:
        return self.state.session

## SECTION 4: LapAnalyser

class LapAnalyser(BaseAnalyser):

    RECORD_WAIT_S = 6.0

    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._last_known_lap: Optional[int] = None
        self._prev_best_ms: Optional[int] = None
        self._pending: List[Tuple[int, float]] = []
        self._lap_invalid: Dict[int, bool] = {}

    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None or p.current_lap_num is None:
            return []
        
        lap = p.current_lap_num
        self._lap_invalid[lap] = bool(p.current_lap_invalid)

        ## Initialise on first call
        if self._last_known_lap is None:
            self._last_known_lap = lap
            return []
        
        ## No new lap
        if lap != self._last_known_lap:
            if lap > self._last_known_lap:
                self._pending.append((self._last_known_lap, _now()))
            self._last_known_lap = lap

        insights: List[Insight] = []
        still_waiting = []
        for lap_num, ended_at in self._pending:
            rec = self.state.get_player_lap_record(lap_num)
            if rec is None and (_now() - ended_at) < self.RECORD_WAIT_S:
                still_waiting.append((lap_num, ended_at))
                continue
            insights += self._on_lap_completed(lap_num, rec, p)
        self._pending = still_waiting
        return insights
            
    def _on_lap_completed(self, lap_num: int, rec: Optional[LapRecord], p: CarState) -> List[Insight]:
        lap_time_ms = rec.lap_time_ms if rec else (p.last_lap_time_ms or 0)
        if lap_time_ms <= 0:
            return []
        valid = rec.lap_valid if rec else not bool(p.current_lap_invalid)
        insights = [self._make_insight(
            InsightType.LAP_COMPLETED,
            InsightPriority.INFO,
            data = {
                "lap_number": lap_num,
                "lap_time_ms": lap_time_ms,
                "lap_time_str": _ms_to_time_str(lap_time_ms),
                "sector1_ms": rec.sector1_time_ms if rec else 0,
                "sector2_ms": rec.sector2_time_ms if rec else 0,
                "sector3_ms": rec.sector3_time_ms if rec else 0,
                "lap_valid": valid,
                "in_lap": bool(rec and rec.pit_stop_this_lap),
                "out_lap": bool(rec and rec.is_out_lap),
            },
            message = f"Lap {lap_num}: {_ms_to_time_str(lap_time_ms)}" + ("" if valid else " (lap invalid)"),
            lap_number = lap_num)]
        if not valid or rec is None or rec.pit_stop_this_lap or rec.is_out_lap:
            return insights

        ## Personal Best Check
        best = self.state.get_best_lap_record()
        if best and best.lap_number == lap_num:
            prev = self._prev_best_ms
            delta = (lap_time_ms - prev) if prev else 0
            insights.append(self._make_insight(
                InsightType.PERSONAL_BEST,
                InsightPriority.INFO,
                data={
                    "lap_time_ms": lap_time_ms,
                    "lap_time_str": _ms_to_time_str(lap_time_ms),
                    "delta_ms": delta,
                    "delta_str": _format_delta_ms(delta),
                },
                message=f"Personal best! {_ms_to_time_str(lap_time_ms)}" + (f" ({_format_delta_ms(delta)})" if prev else ""),
                lap_number=lap_num,
            ))
        elif best:
            sectors = []
            for n, cur, ref in((1, rec.sector1_time_ms, best.sector1_time_ms),
                               (2, rec.sector2_time_ms, best.sector2_time_ms),
                               (3, rec.sector3_time_ms, best.sector3_time_ms)):
                if cur > 0 and ref > 0:
                    sectors.append({"sector": n, "current_ms": cur, "best_ms": ref, "delta_ms": cur - ref, "delta_str": _format_delta_ms(cur - ref)})
            if sectors:
                worst = max(sectors, key=lambda s: s["delta_ms"])
                insights.append(self._make_insight(
                    InsightType.SECTOR_DELTA,
                    InsightPriority.INFO,
                    data = {
                        "sectors": sectors,
                        "worst_sector": worst["sector"],
                        "vs_lap": best.lap_number,
                    },
                    message = (f"Lap {_format_delta_ms(lap_time_ms - best.lap_time_ms)} vs your best; "
                               f"biggest loss in sector {worst['sector']} ({worst['delta_str']})."),
                    lap_number=lap_num
                ))
            theory = self._compute_theoretical_best()
            if theory and lap_time_ms - theory > 200:
                insights.append(self._make_insight(
                    InsightType.THEORETICAL_BEST,
                    InsightPriority.INFO,
                    data = {
                        "theoretical_ms": theory,
                        "theoretical_str": _ms_to_time_str(theory),
                        "delta_ms": lap_time_ms - theory,
                        "delta_str": _format_delta_ms(lap_time_ms - theory)
                    },
                    message = (f"Theoretical best {_ms_to_time_str(theory)}, "
                               f"{_format_delta_ms(lap_time_ms - theory)} off this lap."),
                    lap_number=lap_num,))
        if best:
            self._prev_best_ms = best.lap_time_ms
        return insights
        
    def _compute_theoretical_best(self) -> int:
        clean = [r for r in self.state.lap_history if r.lap_valid and not r.pit_stop_this_lap and not r.is_out_lap]
        if len(clean) < 2:
            return 0
        def best(attr: str, valid_attr: str) -> int:
            return min((getattr(r, attr) for r in clean if getattr(r, attr) > 0 and getattr(r, valid_attr)), default=0)
        s1, s2, s3 = (best("sector1_time_ms", "sector1_valid"), best("sector2_time_ms", "sector2_valid"), best("sector3_time_ms", "sector3_valid"))
        return s1 + s2 + s3 if s1 and s2 and s3 else 0
        
## SECTION 5: Tyre Analyser

TYRE_ORDER = ("RL", "RR", "FL", "FR")

def _slope(xs: List[float], ys: List[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    return 0.0 if den == 0 else sum ((x - mx) * (y - my) for x, y in zip(xs, ys)) / den

class TyreAnalyser(BaseAnalyser):
    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._wear_history: List[Tuple[int, float]] = []
        self._last_sampled_age: Optional[int] = None
        self._last_comp: Optional[int] = None
        self._last_age: Optional[int] = None
        self._steps_fired: set = set()
        self._cold_active = False
        self._hot_active = False

    @property
    def wear_history(self) -> List[Tuple[int, float]]:
        return list(self._wear_history)

    def wear_rate(self) -> float:
        if len(self._wear_history) < self.config.tyre_min_samples_for_rate:
            return 0.0
        pts = self._wear_history[-8:]
        return max(0.0, _slope([a for a, _ in pts], [w for _, w in pts]))

    def laps_to_wear(self, current_wear: float, target_pct: float) -> Optional[float]:
        rate = self.wear_rate()
        if rate <= 0:
            p = self.player
            age = (p.tyres_age_laps or 0) if p else 0
            if age <= 0 or current_wear <= 0:
                return None
            rate = current_wear / age
        return max(0.0, round((target_pct - current_wear) / rate, 1))

    def reset_for_new_stint(self) -> None:
        self._wear_history.clear()
        self._last_sampled_age = None
        self._steps_fired.clear()
        self._cold_active = self._hot_active = False
        self._last_fired.clear()
    
    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None or not p.tyres_wear:
            return []
        self._detect_new_stint(p)
        insights: List[Insight] = []
        max_wear = max(p.tyres_wear)
        worst = TYRE_ORDER[p.tyres_wear.index(max_wear)] if len(p.tyres_wear) == 4 else None
        age = p.tyres_age_laps or 0

        if age != self._last_sampled_age and age > 0:
            self._wear_history.append((age, max_wear))
            self._last_sampled_age = age
            del self._wear_history[:-20]

        common = {"max_wear_pct": round(max_wear, 1), "wear_all": p.tyres_wear, "worst_tyre": worst,
                  "compound": TYRE_COMPOUNDS_VISUAL.get(p.visual_tyre_compound, p.visual_tyre_compound),
                  "tyre_age_laps": age}

        crit_step = max((s for s in self.config.tyre_wear_critical_steps if max_wear >= s), default=None)
        warn_step = max((s for s in self.config.tyre_wear_warning_steps if max_wear >= s), default=None)
        if crit_step is not None and ("c", crit_step) not in self._steps_fired:
            self._steps_fired.add(("c", crit_step))
            laps = self.laps_to_wear(max_wear, 100.0)
            insights.append(self._make_insight(
                InsightType.TYRE_WEAR_CRITICAL, InsightPriority.CRITICAL, {**common, "laps_remaining": laps},
                f"Tyre wear critical at {max_wear:.0f}%." + (f" About {laps:.0f} laps left." if laps is not None else "")))
        elif warn_step is not None and crit_step is None and ("w", warn_step) not in self._steps_fired:
            self._steps_fired.add(("w", warn_step))
            laps = self.laps_to_wear(max_wear, self.config.tyre_wear_critical_steps[0])
            insights.append(self._make_insight(
                InsightType.TYRE_WEAR_WARNING, InsightPriority.WARNING, {**common, "laps_to_critical": laps},
                f"Tyre wear at {max_wear:.0f}%." + (f" About {laps:.0f} laps to the critical point." if laps is not None else "")))

        rate = self.wear_rate()
        if rate > 0 and not self._on_cooldown(InsightType.TYRE_DEGREDATION_RATE, self.config.cd(self.config.cooldown_tyre_rate_s)):
            to_crit = self.laps_to_wear(max_wear, self.config.tyre_wear_critical_steps[0])
            insights.append(self._make_insight(
                InsightType.TYRE_DEGREDATION_RATE, InsightPriority.INFO,
                {**common, "wear_per_lap_pct": round(rate, 2), "laps_to_critical": to_crit, "samples": len(self._wear_history)},
                f"Tyre wear is {rate:.1f}% per lap" + (f", about {to_crit:.0f} laps to the critical point." if laps is not None else "")))
            self._mark_fired(InsightType.TYRE_DEGREDATION_RATE)

        insights += self._check_temperatures(p, common)
        insights += self._check_blisters(p, common)
        return insights

    def _detect_new_stint(self, p: CarState) -> None:
        age, comp = p.tyres_age_laps, p.visual_tyre_compound
        if self._last_age is not None and age is not None and (age < self._last_age or comp != self._last_comp):
            self.reset_for_new_stint()
        self._last_age, self._last_comp = age, comp

    def _check_temperatures(self, p: CarState, common: dict) -> List[Insight]:
        temps = p.tyres_surface_temp
        if not temps or not p.is_on_track or (p.speed_kph or 0) < 100:
            return []
        avg = sum(temps) / len(temps)
        cfg, out = self.config, []
        if avg < cfg.tyre_temp_cold_surface:
            if not self._cold_active and not self._on_cooldown(InsightType.TYRE_TEMP_COLD, cfg.cd(cfg.cooldown_tyre_temp_s)):
                self._cold_active = True
                self._mark_fired(InsightType.TYRE_TEMP_COLD)
                out.append(self._make_insight(
                    InsightType.TYRE_TEMP_COLD, InsightPriority.ADVISORY,
                    {**common, "avg_temp_c": round(avg, 1), "temps_all": temps, "target_min_c": cfg.tyre_temp_cold_surface},
                    f"Tyres are cold at {avg:.0f} degrees. Build temperature before pushing."))
        elif avg >= cfg.tyre_temp_cold_surface + cfg.tyre_temp_hysteresis:
            self._cold_active = False
        if avg >= cfg.tyre_temp_hot_surface:
            if not self._hot_active and not self._on_cooldown(InsightType.TYRE_TEMP_OVERHEATING, cfg.cd(cfg.cooldown_tyre_temp_s)):
                self._hot_active = True
                self._mark_fired(InsightType.TYRE_TEMP_OVERHEATING)
                out.append(self._make_insight(
                    InsightType.TYRE_TEMP_OVERHEATING, InsightPriority.WARNING,
                    {**common, "avg_temp_c": round(avg, 1), "temps_all": temps, "target_max_c": cfg.tyre_temp_hot_surface},
                    f"Tyres overheating at {avg:.0f} degrees. Ease off to protect them"))
        elif avg < cfg.tyre_temp_hot_surface - cfg.tyre_temp_hysteresis:
            self._hot_active = False
        return out

    def _check_blisters(self, p: CarState, common: dict) -> List[Insight]:
        if not p.tyre_blisters:
            return []
        worst = max(p.tyre_blisters)
        if worst >= self.config.tyre_blister_warning and not self._on_cooldown(
            InsightType.TYRE_BLISTER_WARNING, self.config.cd(self.config.cooldown_blister_s)):
            self._mark_fired(InsightType.TYRE_BLISTER_WARNING)
            return [self._make_insight(InsightType.TYRE_BLISTER_WARNING, InsightPriority.WARNING,
                                       {**common, "max_blister_pct": worst, "blisters_all": p.tyre_blisters},
                                       f"Tyre blistering at {worst}%.")]
        return []

## SECTION 6: Fuel Analyser

class FuelAnalyser(BaseAnalyser):
    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._fuel_per_lap_history: List[float] = []
        self._fuel_at_lap_start: Optional[float] = None
        self._last_lap_num: Optional[int] = None
        self._last_save_delta: Optional[float] = None

    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None or not self.session.is_race or not p.fuel_remaining_laps is None:
            return []
        self._track_consumption(p)
        laps_left = self.state.laps_remaining()
        if laps_left is None:
            return []
        cfg = self.config
        delta = p.fuel_remaining_laps - laps_left
        data = {"fuel_remaining_laps": round(p.fuel_remaining_laps, 2), "laps_left": laps_left,
                "delta_laps": round(delta, 2), "fuel_in_tank_kg": round(p.fuel_in_tank or 0, 2),
                "kg_per_lap": round(self._avg_fuel_per_lap(), 2), "current_mix": p.fuel_mix}

        if p.fuel_remaining_laps < cfg.fuel_critical_laps:
            if not self._on_cooldown(InsightType.FUEL_CRITICAL, cfg.cd(cfg.cooldown_fuel_critical_s)):
                self._mark_fired(InsightType.FUEL_CRITICAL)
                return[self._make_insight(InsightType.FUEL_CRITICAL, InsightPriority.CRITICAL, data,
                                          f"Fuel critical: {p.fuel_remaining_laps:.1f} laps in the tank, {laps_left} to go.")]
        elif delta < cfg.fuel_save_delta_laps:
            worse = self._last_save_delta is not None and delta < self._last_save_delta - cfg.fuel_worsen_steps_laps
            if worse or not self._on_cooldown(InsightType.FUEL_SAVE_REQUIRED, cfg.cd(cfg.cooldown_fuel_s)):
                    self._last_save_delta = delta
                    self._mark_fired(InsightType.FUEL_SAVE_REQUIRED)
                    return [self._make_insight(InsightType.FUEL_SAVE_REQUIRED, InsightPriority.WARNING, data,
                            f"Fuel save required. Short by {abs(delta):.1f} laps. Switch to lean mix.")]
        elif delta > cfg.fuel_rich_delta_laps:
                    self._last_save_delta = None
                    if not self._on_cooldown(InsightType.FUEL_RICH_AVAILABLE, cfg.cd(cfg.cooldown_fuel_delta_s)):
                        self._mark_fired(InsightType.FUEL_RICH_AVAILABLE)
                        return [self._make_insight(InsightType.FUEL_RICH_AVAILABLE, InsightPriority.ADVISORY,
                            {**data, "surplus_kg": round(delta * self._avg_fuel_per_lap(), 2)},
                            f"Fuel surplus of {delta:.1f} laps. Rich mix is available")]
        else:
            self._last_save_delta = None
            if not self._on_cooldown(InsightType.FUEL_DELTA, cfg.cd(cfg.cooldown_fuel_delta_s)):
                self._mark_fired(InsightType.FUEL_DELTA)
                return [self._make_insight(InsightType.FUEL_DELTA, InsightPriority.INFO, data,
                                           f"Fuel is on target, {delta:+.1f} laps")]
        return []

    def _track_consumption(self, p:CarState) -> None:
        lap = p.current_lap_num
        fuel = p.fuel_in_tank
        if lap is None or fuel is None:
            return
        if self._last_lap_num is not None and lap > self._last_lap_num and self._fuel_at_lap_start is not None:
            used = self._fuel_at_lap_start - fuel
            if used > 0:
                self._fuel_per_lap_history.append(used)
                del self._fuel_per_lap_history[:-15]
        if lap != self._last_lap_num:
            self._fuel_at_lap_start = fuel
        self._last_lap_num = lap

    def _avg_fuel_per_lap(self) -> float:
        h = self._fuel_per_lap_history
        return sum(h) / len(h) if h else 0.0

## SECTION 7: ERS Analyser

class ERSAnalyser(BaseAnalyser):
    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._harvest_per_lap: List[float] = []
        self._deploy_per_lap: List[float] = []
        self._last_lap_num: Optional[int] = None
        self._seen = {"harvest": 0.0, "deploy": 0.0}
        self._low_active = False
        self._harvest_checked_lap: Optional[int] = None

    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None or p.ers_store_energy is None:
            return []
        cfg, out = self.config, []
        self._track_lap_ers(p)
        if p.ers_store_percent is None:
            return out
        pct = p.ers_store_percent

        if pct < cfg.ers_low_pct:
            if not self._low_active and not self._on_cooldown(InsightType.ERS_STORE_LOW, cfg.cd(cfg.cooldown_ers_s)):
                self._low_active = True
                self._mark_fired(InsightType.ERS_STORE_LOW)
                out.append(self._make_insight(
                    InsightType.ERS_STORE_LOW, InsightPriority.ADVISORY,
                    {"store_pct": round(pct, 1), "store_joules": round(p.ers_store_energy, 0), "deploy_mode": p.ers_mode_name},
                    f"ERS store low at {pct:.0f}%. Considering harvesting."))
        elif pct >= cfg.ers_rearm_pct:
            self._low_active = False

        lap = p.current_lap_num
        if len(self._harvest_per_lap) >= 4 and lap != self._harvest_checked_lap:
            self._harvest_checked_lap = lap
            avg = sum(self._harvest_per_lap[:-1]) / len(self._harvest_per_lap[:-1])
            last = self._harvest_per_lap[-1]
            drop = (avg - last) / avg * 100 if avg > 0 else 0
            if drop > cfg.ers_harvest_drop_pct and not self._on_cooldown(
                InsightType.ERS_HARVEST_LOW, cfg.cd(cfg.cooldown_ers_harvest_s)):
                self._mark_fired(InsightType.ERS_HARVEST_LOW)
                out.append(self._make_insight(
                    InsightType.ERS_HARVEST_LOW, InsightPriority.ADVISORY,
                    {"last_harvest_kj": round(last / 1000, 1), "avg_harvest_kj": round(avg / 1000, 1), "drop_pct": round(drop, 1)},
                    f"ERS harvest was down {drop:.0f}% on your average last lap."))
        return out

    def _track_lap_ers(self, p: CarState) -> None:
        lap = p.current_lap_num
        if lap is None:
            return
        if self._last_lap_num is not None and lap > self._last_lap_num:
            self._harvest_per_lap.append(self._seen["harvest"])
            self._deploy_per_lap[:-20], self._deploy_per_lap[:-20]
            del self._harvest_per_lap[:-20], self._deploy_per_lap[:-20]
        self._last_lap_num = lap
        self._seen["harvest"] = (p.ers_harvested_lap_mguk or 0) + (p.ers_harvested_lap_mguh or 0)
        self._seen["deploy"] = p.ers_deployed_lap or 0

## SECTION 8: Braking Analyser

CornerLookup = Callable[[float], Optional[Tuple[int, str]]]

class BrakingAnalyser(BaseAnalyser):
    EVAL_WAIT_S = 6.0

    def __init__(self, state: TelemetryState, config: AnalyticsConfig, corner_lookup: Optional[CornerLookup] = None):
        super().__init__(state, config)
        self.corner_lookup = corner_lookup
        self._cur: Optional[Dict[str, Any]] = None
        self._events: List[Dict[str, Any]] = []
        self._lap_events: Dict[int, List[Dict[str, Any]]] = {}
        self._last_lap_num: Optional[int] = None
        self._pending_eval: List[Tuple[int, float]] = []
        self._last_coached_lap: Dict[str, int] = {}

    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None or p.brake is None or p.lap_distance is None or not p.is_on_track:
            return []
        lap = p.current_lap_num or 0
        if self._last_lap_num is not None and lap != self._last_lap_num:
            self._close_event(p)
            if lap > self._last_lap_num:
                self._lap_events[self._last_lap_num] = self._events
                self._pending_eval.append((self._last_lap_num, _now()))
                best = self.state.get_best_lap_record()
                keep = best.lap_number if best else None
                for old in [k for k in self._lap_events if k < lap - 12 and k != keep]:
                    del self._lap_events[old]
            self._events = []
        self._last_lap_num = lap

        cfg = self.config
        speed = p.speed_kph or 0
        if self._cur is None:
            if p.brake > cfg.brake_threshold and speed > cfg.min_speed_for_braking and not p.is_pitting:
                self._cur = {"dist_m": p.lap_distance, "entry_speed": speed, "min_speed": speed, "lap": lap}
        else:
            self._cur["min_speed"] = min(self._cur["min_speed"], speed)
            if p.brake < cfg.brake_release_threshold:
                self._close_event(p)

        out: List[Insight] = []
        waiting = []
        for lap_num, ended in self._pending_eval:
            if self.state.get_player_lap_record(lap_num) is None and _now() - ended < self.EVAL_WAIT_S:
                waiting.append((lap_num, ended))
            else:
                out += self._evaluate_lap(lap_num)
        self._pending_eval = waiting
        return out

    def _close_event(self, p: CarState) -> None:
        if self._cur is not None:
            self._cur["end_dist_m"] = p.lap_distance
            self._events.append(self._cur)
            self._cur = None

    def reference_events(self) -> Tuple[Optional[int], List[Dict[str, Any]]]:
        best = self.state.get_best_lap_record()
        if best and best.lap_number in self._lap_events:
            return best.lap_number, self._lap_events[best.lap_number]
        return None, []

    def get_braking_profile(self) -> List[Dict[str, Any]]:
        return list(self.reference_events()[1])

    def _key_and_corner(self, dist_m: float) -> Tuple[str, Optional[int], Optional[str]]:
        hit = self.corner_lookup(dist_m) if self.corner_lookup else None
        if hit:
            return f"c{hit[0]}", hit[0], hit[1]
        return f"d{int(dist_m // 60)}", None, None

    def _evaluate_lap(self, lap_num: int) -> List[Insight]:
        cfg = self.config
        rec = self.state.get_player_lap_record(lap_num)
        ref_lap, ref_events = self.reference_events()
        if rec is None or not rec.lap_valid or rec.pit_stop_this_lap or rec.is_out_lap:
            return []
        if ref_lap is None or ref_lap == lap_num or not ref_events:
            return []
        candidates = []
        for e in self._lap_events.get(lap_num, []):
            ref = min(ref_events, key=lambda r: abs(r["dist_m"] - e["dist_m"]))
            if abs(ref["dist_m"] - e["dist_m"]) > cfg.braking_match_window_m:
                continue
            delta = e["dist_m"] - ref["dist_m"]
            key, cid, cname = self._key_and_corner(ref["dist_m"])
            candidates.append((delta, key, cid, cname, e, ref))

        early = sorted((c for c in candidates if c[0] < -cfg.braking_early_delta_m), key=lambda c: c[0])
        late = sorted((c for c in candidates if c[0] > cfg.braking_early_delta_m), key=lambda c: c[0], reverse=True)
        out: List[Insight] = []
        for delta, key, cid, cname, e, ref in (early + late):
            if len([i for i in out]) >= cfg.braking_max_per_lap:
                break
            last = self._last_coached_lap.get(key)
            if last is not None and lap_num - last < cfg.braking_corner_min_laps:
                continue
            self._last_coached_lap[key] = lap_num
            is_early = delta < 0
            where = cname or f"the braking zone at {ref['dist_m']:.0f} metres"
            data = {"delta_m": round(delta, 1), "dist_m": round(e["dist_m"], 1), "ref_dist_m": round(ref["dist_m"], 1),
                    "entry_speed_kph": e["entry_speed"], "ref_entry_speed_kph": ref["entry_speed"],
                    "min_speed_kph": e["min_speed"], "ref_min_speed_kph": ref["min_speed"], "vs_lap": ref_lap,
                    "position_m": round(ref["dist_m"], 1)}
            out.append(self._make_insight(
                InsightType.BRAKING_POINT_EARLY if is_early else InsightType.BRAKING_POINT_LATE,
                InsightPriority.ADVISORY if is_early else InsightPriority.INFO, data,
                f"You braked {abs(delta):.0f} metres {'earlier' if is_early else 'later'} than your best lap into {where}.",
                lap_number=lap_num, corner_id=cid, corner_name=cname))
            return out

## SECTION 9: Strategy Analyser

class StrategyAnalyser(BaseAnalyser):
    POSITION_CONFIRM_S = 2.0

    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._last_position: Optional[int] = None
        self._candidate: Optional[Tuple[int, float]] = None
        self._undercut_flagged: bool = False
        self._pit_open_lap: Optional[int] = None
        self._last_stops: int = 0

    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None or not self.session.is_race:
            return []
        return (self._check_pit_window(p) + self._check_undercut(p) + self._check_position_change(p) + self._check_gap_report(p))

    def rival_ahead(self) -> Optional[CarState]:
        p = self.player
        return self.state.get_car_by_position(p.car_position - 1) if p and p.car_position and p.car_position > 1 else None

    def rival_behind(self) -> Optional[CarState]:
        p = self.player
        return self.state.get_car_by_position(p.car_position + 1) if p and p.car_position else None

    def _check_pit_window(self, p: CarState) -> List[Insight]:
        ideal = self.session.pit_stop_window_ideal_lap
        latest = self.session.pit_stop_window_latest_lap
        lap = p.current_lap_num
        if not ideal or not latest or lap is None:
            return []
        stops = p.num_pit_stops or 0
        if stops != self._last_stops:
            self._last_stops = stops
            self._pit_open_lap = None
        if stops >= 1 and self.session.total_laps and self.session.total_laps < 30:
            return[]
        cfg, out = self.config, []
        rejoin = self.session.pit_stop_rejoin_position
        if ideal <= lap <= latest and self._pit_open_lap is None:
            self._pit_open_lap = lap
            out.append(self._make_insight(
                InsightType.PIT_WINDOW_OPEN, InsightPriority.ADVISORY,
                {"ideal_lap": ideal, "latest_lap": latest, "current_lap": lap, "rejoin_pos": rejoin},
                f"Pit window is open. Ideal lap {ideal}, latest lap {latest}. Rejoin P{rejoin}."))
        to_latest = latest - lap
        if 0 < to_latest <= cfg.pit_window_warning_laps and not self._on_cooldown(
            InsightType.PIT_WINDOW_CLOSING, cfg.cd(cfg.cooldown_strategy_s)):
            self._mark_fired(InsightType.PIT_WINDOW_CLOSING)
            out.append(self._make_insight(
                InsightType.PIT_WINDOW_CLOSING, InsightPriority.WARNING,
                {"latest_lap": latest, "current_lap": lap, "laps_to_latest": to_latest},
                f"Pit window closing. Must stop within {to_latest} laps, latest lap {latest}."))
        return out

    def _check_undercut(self, p: CarState) -> List[Insight]:
        cfg = self.config
        gap, rival = self.state.player_gap_to_car_ahead(), self.rival_ahead()
        if gap is None or rival is None or p.is_pitting:
            return []
        if gap > cfg.undercut_gap_threshold_s * 1.5:
            self._undercut_flagged = False
        if (not self._undercut_flagged and gap < cfg.undercut_gap_threshold_s
            and (rival.tyres_age_laps or 0) >= cfg.undercut_tyre_age_min
            and not self._on_cooldown(InsightType.UNDERCUT_WINDOW, cfg.cd(cfg.cooldown_strategy_s))):
            self._undercut_flagged = True
            self._mark_fired(InsightType.UNDERCUT_WINDOW)
            return [self._make_insight(
                InsightType.UNDERCUT_WINDOW, InsightPriority.ADVISORY,
                {"gap_ahead_s": round(gap, 2), "rival_name": rival.name, "rival_tyre_age": rival.tyres_age_laps,
                 "rival_compound": TYRE_COMPOUNDS_VISUAL.get(rival.visual_tyre_compound, rival.visual_tyre_compound),
                 "player_tyre_age": p.tyres_age_laps, "rejoin_pos": self.session.pit_stop_rejoin_position},
                 f"Undercut chance: {rival.name or 'the car ahead'} is {gap:.1f} ahead on {rival.tyres_age_laps}-lap-old tyres.",
                 vehicle_idx=rival.vehicle_index)]
        return []

    def _check_position_change(self, p: CarState) -> List[Insight]:
        pos = p.car_position
        if pos is None:
            return []
        if self._last_position is None:
            self._last_position = pos
            return []
        if p.is_pitting:
            self._last_position = pos
            self._candidate = None
            return []
        if pos == self._last_position:
            self._candidate = None
            return []
        if self._candidate is None or self._candidate[0] != pos:
            self._candidate = (pos, _now())
            return []
        if _now() - self._candidate[1] < self.POSITION_CONFIRM_S:
            return []    
        gained, old = pos < self._last_position, self._last_position
        self._last_position, self._candidate = pos, None
        return [self._make_insight(
            InsightType.POSITION_GAINED if gained else InsightType.POSITION_LOST, InsightPriority.INFO,
            {"new_position": pos, "old_position": old, "delta": old - pos},
            f"Up to P{pos}." if gained else f"Down to P{pos}.")]

    def _check_gap_report(self, p: CarState) -> List[Insight]:
        cfg = self.config
        if self.session.safety_car_deployed or self._on_cooldown(InsightType.GAP_TO_AHEAD, cfg.cd(cfg.cooldown_gap_s)):
            return []
        ahead, leader = self.state.player_gap_to_car_ahead(), self.state.player_gap_to_leader()
        if ahead is None:
            return []
        self._mark_fired(InsightType.GAP_TO_AHEAD)
        return [self._make_insight(
            InsightType.GAP_TO_AHEAD, InsightPriority.INFO,
            {"gap_ahead_s": round(ahead, 3), "gap_leader_s": round(leader, 3) if leader else None, "position": p.car_position},
            f"Gap to car ahead: {ahead:.1f}s." + (f" Leader: {leader:.1f}s." if leader is not None else ""))]

## SECTION 10: Damage Analyser

class DamageAnalyser(BaseAnalyser):

    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._last = {"wing": 0, "floor": 0, "engine": 0, "gearbox": 0}
        self._engine_blown_alerted: bool = False
        self._drs_fault_alerted: bool = False

    def analyse(self) -> List[Insight]:
        p = self.player
        if p is None:
            return []
        cfg, out = self.config, []
        if p.engine_blown and not self._engine_blown_alerted:
            self._engine_blown_alerted = True
            out.append(self._make_insight(InsightType.ENGINE_BLOWN, InsightPriority.CRITICAL,
            {"engine_blown": True}, "Engine failure."))
        if p.drs_fault and not self._drs_fault_alerted:
            self._drs_fault_alerted = True
            out.append(self._make_insight(InsightType.DRS_FAULT, InsightPriority.WARNING,
                {"drs_fault": True}, "DRS fault detected."))
        elif not p.drs_fault:
            self._drs_fault_alerted = False

        fl, fr, rear = (p.front_left_wing_damage or 0), (p.front_right_wing_damage or 0), (p.rear_wing_damage or 0)
        wing = max(fl, fr, rear)
        floor = max(p.floor_damage or 0, p.diffuser_damage or 0)
        out += self._step(InsightType.DAMAGE_WING, "wing", wing, 5, 30,
                          {"front_left_pct": fl, "front_right_pct": fr, "rear_pct": rear},
                          lambda v: f"Wing damage: front left {fl}%, front right {fr}%, rear {rear}%.")
        out += self._step(InsightType.DAMAGE_FLOOR, "floor", floor, 5, 25, {"floor_damage_pct": floor},
                          lambda v: f"Floor damage at {v}%.")
        out += self._step(InsightType.DAMAGE_ENGINE, "engine", p.engine_damage or 0, 10, 50,
                          {"engine_damage_pct": p.engine_damage or 0}, lambda v: f"Engine damage at {v}%.")
        out += self._step(InsightType.DAMAGE_GEARBOX, "gearbox", p.gear_box_damage or 0, 10, 50,
                          {"gearbox_damage_pct": p.gear_box_damage or 0}, lambda v: f"Gearbox damage at {v}%.")
        return out

    def _step(self, itype: InsightType, name: str, value: int, jump: int, warn_at: int,
    data: dict, msg: callable[[int], str]) -> List[Insight]:
        last = self._last[name]
        if value < last:
            self._last[name] = value
            return []
        if value > last + jump and not self._on_cooldown(itype, self.config.cd(self.config.cooldown_damage_s)):
            self._last[name] = value
            self._mark_fired(itype)
            return [self._make_insight(itype, InsightPriority.WARNING if value > warn_at else InsightPriority.INFO, data, msg(value))]
        return []

## SECTION 11: Event Analyser

PENALTY_TYPES = {0: "drive-through", 1: "stop-go", 2: "grid penalty", 4: "time penalty", 5: "warning", 6: "disqualification", 10: "lap deleted"}
INFRINGEMENTS = {0: "blocking", 3: "a big collision", 4: "a collision", 10: "corner cutting", 13: "crossing the pit exit line", 14: "ignoring blue flags", 15: "ignoring yellow flags", 20: "pit lane speeding", 28: "track limits"}

class EventAnalyser(BaseAnalyser):

    def __init__(self, state: TelemetryState, config: AnalyticsConfig):
        super().__init__(state, config)
        self._seen: Deque[Tuple[float, str, str]] = deque(maxlen=200)

    def analyse(self) -> List[Insight]:
        out = []
        pidx = self.state.player_index
        for ev in list(self.state.events):
            key = (ev.wall_time, ev.event_code, repr(ev.details))
            if key in self._seen:
                continue
            self._seen.append(key)
            handler = {"SCAR": self._safety_car, "RDFL": self._red_flag, "FTLP": self._fastest_lap,
                       "OVTK": self._overtake, "PENA": self._penalty, "RTMT": self._retirement}.get(ev.event_code)
            ins = handler(ev, pidx) if handler else None
            if ins:
                out.append(ins)
        return out

    def _name(self, idx: Optional[int]) -> str:
        c = self.state.cars[idx] if idx is not None and 0 <= idx < len(self.state.cars) else None
        return (c.name if c and c.name else "a rival")

    def _safety_car(self, ev, pidx):
        d = ev.details
        kind = {1: "Safety Car", 2: "Virtual Safety Car", 3: "Formation Lap"}.get(getattr(d, "safety_car_type", 0), "Safety car")
        etype = getattr(d, "event_type", 0)
        if etype == 0:
            return self._make_insight(InsightType.SAFETY_CAR_DEPLOYED, InsightPriority.WARNING,
                                      {"kind": kind, "event_type": "deployed"}, f"{kind} deployed.")
        if etype in (1, 3):
            return self._make_insight(InsightType.SAFETY_CAR_ENDING, InsightPriority.WARNING,
                                      {"kind": kind, "event_type": "returning" if etype == 1 else "resume"},
                                      f"{kind} in this lap. Prepare for the restart." if etype == 1 else "Race resumes")
        return None
    
    def _red_flag(self, ev, pidx):
        return self._make_insight(InsightType.RED_FLAG, InsightPriority.CRITICAL, {}, "Red flag. Session suspended.")

    def _fastest_lap(self, ev, pidx):
        d = ev.details
        if d is None or getattr(d, "vehicle_idx", -1) != pidx:
            return None
        secs = float(getattr(d, "lap_time_ms", 0))
        txt = _ms_to_time_str(int(round(secs * 1000)))
        return self._make_insight(InsightType.FASTEST_LAP, InsightPriority.INFO,
                                  {"lap_time_s": secs, "lap_time_str": txt}, f"Fastest lap of the race: {txt}.")

    def _overtake(self, ev, pidx): 
        d = ev.details
        if d is None:
            return None
        a, b = getattr(d, "overtaking_vehicle_idx", None), getattr(d, "being_overtaken_vehicle_idx", None)
        if pidx not in (a, b):
            return None
        passed_by_me = a == pidx
        other = b if passed_by_me else a
        return self._make_insight(
            InsightType.OVERTAKE_DETECTED, InsightPriority.INFO,
            {"player_passed": passed_by_me, "rival_name": self._name(other), "rival_idx": other},
            f"You passed {self._name(other)}." if passed_by_me else f"{self._name(other)} passed you.",
            vehicle_idx=other)

    def _penalty(self, ev, pidx):
        d = ev.details
        if d is None or getattr(d, "vehicle_idx", -1) != pidx:
            return None
        ptype = PENALTY_TYPES.get(d.penalty_type, f"penalty type {d.penalty_type}")
        why = INFRINGEMENTS.get(d.infringement_type, f"infringement {d.infringement_type}")
        secs = f" of {d.time} seconds" if d.penalty_type == 4 and d.time else ""
        return self._make_insight(InsightType.PENALTY_ISSUED, InsightPriority.WARNING,
                                  {"penalty_type": ptype, "infringement": why, "seconds": d.time, "lap": d.lap_num},
                                  f"You have a {ptype}{secs} for {why}.")

    def _retirement(self, ev, pidx):
        d = ev.details
        idx = getattr(d, "vehicle_idx", None)
        if d is None or idx == pidx:
            return None
        return self._make_insight(InsightType.RETIREMENT, InsightPriority.INFO,
                                  {"rival_name": self._name(idx), "rival_idx": idx},
                                  f"{self._name(idx)} has retired", vehicle_idx=idx)

## Section 12: Analytics Engine

class AnalyticsEngine:

    MAX_HISTORY = 300

    def __init__(self, state: TelemetryState, config: Optional[AnalyticsConfig] = None,
                 corner_lookup: Optional[CornerLookup] = None, require_live: bool = True):
        self.state = state
        self.config = config or AnalyticsConfig()
        self.require_live = require_live
        self.lap = LapAnalyser(state, self.config)
        self.tyre = TyreAnalyser(state, self.config)
        self.fuel = FuelAnalyser(state, self.config)
        self.ers = ERSAnalyser(state, self.config)
        self.braking = BrakingAnalyser(state, self.config, corner_lookup)
        self.strategy = StrategyAnalyser(state, self.config)
        self.damage = DamageAnalyser(state, self.config)
        self.events = EventAnalyser(state, self.config)
        self._analysers: List[BaseAnalyser] = [self.lap, self.tyre, self.fuel, self.ers, self.braking,
                                               self.strategy, self.damage, self.events]
        self.insight_history: Deque[Insight] = deque(maxlen=self.MAX_HISTORY)
        self._tick_count = 0

    def tick(self) -> List[Insight]:
        if self.require_live and not self.state.is_live:
            return []
        self._tick_count += 1
        new: List[Insight] = []
        lock = getattr(self.state, "_lock", None)
        for a in self._analysers:
            try:
                if lock:
                    with lock:
                        new += a.analyse()
                else:
                    new += a.analyse()
            except Exception:
                logger.exception(f"{type(a).__name__}.analyse() failed")
        new.sort(key=lambda i: i.priority.value)
        self.insight_history.extend(new)
        return new

    def set_feedback_level(self, level: str) -> None:
        if level not in FEEDBACK_MULTIPLIER:
            raise ValueError(f"feedback level must be one of {list(FEEDBACK_MULTIPLIER)}")
        self.config.feedback_level = level

    def notify_new_stint(self) -> None:
        self.tyre.reset_for_new_stint()

    def get_recent_insights(self, n: int = 10, insight_type: Optional[InsightType] = None, max_age_s: Optional[float] = None) -> List[Insight]:
        out = []
        for ins in reversed(self.insight_history):
            if insight_type is not None and ins.insight_type != insight_type:
                continue
            if max_age_s is not None and _now() - ins.timestamp > max_age_s:
                continue
            out.append(ins)
            if len(out) >= n:
                break
        return out

    def get_latest(self, insight_type: InsightType) -> Optional[Insight]:
        r = self.get_recent_insights(1, insight_type)
        return r[0] if r else None

    @property
    def tick_count(self) -> int:
        return self._tick_count

    def __repr__(self) -> str:
        return (
            f"AnalysticsEngine(ticks={self._tick_count}, analysers={len(self._analysers)}, history={len(self.insight_history)})"
        )

## UTILITY HELPERS

def _format_delta_ms(delta_ms: int) -> str:
    if delta_ms == 0:
        return "=0.000"
    sign = "+" if delta_ms > 0 else "-"
    a = abs(delta_ms)
    secs, millis = a // 1000, a % 1000
    return f"{sign}{secs}.{millis:03d}" if secs else f"{sign}0.{millis:03d}"