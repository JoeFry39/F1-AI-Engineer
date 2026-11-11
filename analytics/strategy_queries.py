from __future__ import annotations
import logging
from dataclasses import dataclass
from statistics import median
from typing import Any, Dict, List, Optional, Tuple

from analytics.analytics_engine import(
    AnalyticsEngine,
    Insight,
    InsightPriority,
    InsightType,
    _now,
    _format_delta_ms,
)
from telemetry.packet_parser import _ms_to_time_str, TYRE_COMPOUNDS_VISUAL
from telemetry.telemetry_state import CarState, LapRecord, TelemetryState

logger = logging.getLogger(__name__)

@dataclass
class StrategyModel:
    outlap_penalty_s: float = 1.5
    rival_response_laps: int = 2
    margin_s: float = 0.3
    horizon_laps: int = 8
    pit_loss_s: Optional[float] = None
    fuel_effect_s_per_lap: float = 0.0
    min_samples: int = 4

def _clean_laps(records: List[LapRecord]) -> List[LapRecord]:
    return [r for r in records if r.lap_valid and r.lap_time_ms > 0 and not r.pit_stop_this_lap and not r.is_out_lap]

def _slope(xs: List[float], ys: List[float]) -> Optional[float]:
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    return None if den == 0 else sum ((x - mx) * (y - my) for x, y in zip(xs, ys)) / den

def _compound_name(code: Optional[int]) -> str:
    return TYRE_COMPOUNDS_VISUAL.get(code, str(code)) if code is not None else "unknown"

class StrategyQueries:
    def __init__(self, state: TelemetryState, engine: AnalyticsEngine, model: Optional[StrategyModel] = None):
        self.state, self.engine = state, engine
        self.model = model or StrategyModel()

    def facts_for(self, topic: Any, question: str = "") -> List[Insight]:
        t = getattr(topic, "value", topic)
        builders = {
            "strategy": [self.undercut_report, self.pit_window_report],
            "tyres": [self.tyre_report],
            "lap": [self.theoretical_best_report],
            "racecraft": [lambda: self.rival_report(True), lambda: self.rival_report(False)],
            "fuel": [self.fuel_report],
        }.get(t, [])
        out = []
        for b in builders:
            try:
                r = b()
                if r is not None:
                    out.append(r)
            except Exception:
                logger.exception(f"strategy query {getattr(b, '__name__', b)} failed")
        return out

    def _ins(self, itype: InsightType, data: Dict[str, Any], message: str, **kw) -> Insight:
        p = self.state.player
        return Insight(itype, InsightPriority.INFO, _now(), (p.lap_data_ts or 0.0) if p else 0.0, data, message,
                       lap_number=p.current_lap_num if p else None, **kw)

    def _stint_laps(self) -> List[LapRecord]:
        p = self.state.player
        recs = _clean_laps(self.state.lap_history)
        if not recs or p is None:
            return []
        last = recs[-1]
        if(p.tyres_age_laps is not None and last.tyre_age_at_end is not None and p.tyres_age_laps < last.tyre_age_at_end):
            return
        comp = last.tyre_compound_visual
        out = []
        for r in reversed(recs):
            if r.tyre_compound_visual != comp or (out and r.tyre_age_at_end is not None
                                                  and out[-1].tyre_age_at_end is not None
                                                  and r.tyre_age_at_end >= out[-1].tyre_age_at_end):
                break
            out.append(r)
        return list(reversed(out))

    def pace_loss_per_lap(self) -> Optional[Dict[str, Any]]:
        laps = [r for r in self._stint_laps() if r.tyre_age_at_end is not None]
        if laps:
            med = median(r.lap_time_ms for r in laps)
            laps = [r for r in laps if r.lap_time_ms <= med * 1.07]
        if len(laps) < self.model.min_samples:
            return None
        first = laps[0].lap_number
        xs = [float(r.tyre_age_at_end) for r in laps]
        ys = [r.lap_time_ms / 1000 + self.model.fuel_effect_s_per_lap * (r.lap_number - first) for r in laps]
        m = _slope(xs, ys)
        if m is None:
            return None
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        ss_tot = sum((y - my) ** 2 for y in ys) or 1e-9
        ss_res = sum((y - (my + m * (x - mx))) ** 2 for x, y in zip(xs, ys))
        return {"slope_s_per_lap": m, "r_squared": 1 - ss_res / ss_tot, "n": len(laps)}

    def _my_pace_s(self, n: int = 3) -> Optional[float]:
        return self._recent_pace_s([r.lap_time_ms for r in self._stint_laps()], n)
    
    def _recent_pace_s(self, lap_times_ms: List[int], n: int = 3) -> Optional[float]:
        times = [t for t in lap_times_ms if t and t > 0]
        if len(times) < 2:
            return None
        med = median(times)
        clean = [t for t in times if t <= med * 1.07][-n:]
        return sum(clean) / len(clean) / 1000 if clean else None

    def _rival_lap_times(self, car_idx: int) -> List[int]:
        return [lh.lap_time_ms for lh in (self.state.session_history_raw.get(car_idx) or []) if lh.lap_time_ms]

    def tyre_report(self) -> Optional[Insight]:
        p = self.state.player
        if p is None or not p.tyres_wear:
            return None
        ty = self.engine.tyre
        wear = max(p.tyres_wear)
        rate = ty.wear_rate()
        pace = self.pace_loss_per_lap()
        data: Dict[str, Any] = {
            "compound": _compound_name(p.visual_tyre_compound), "tyre_age_laps": p.tyres_age_laps,
            "max_wear_pct": round(wear, 1), "wear_all": p.tyres_wear,
            "avg_surface_temp_c": round(sum(p.tyres_surface_temp) / len(p.tyres_surface_temp), 1) if p.tyres_surface_temp else None,
            "wear_per_lap_pct": round(rate, 2) if rate else None,
            "laps_to_70_pct": ty.laps_to_wear(wear, 70.0) if wear < 70 else 0,
            "laps_to_critical": ty.laps_to_wear(wear, float(self.engine.config.tyre_wear_critical_steps[0])),
            "pace_loss_s_per_lap": round(pace["slope_s_per_lap"], 3) if pace else None,
            "pace_fit_r2": round(pace["r_squared"], 2) if pace else None,
            "pace_fit_laps": pace["n"] if pace else 0}
        parts = [f"{data['compound']} tyres, {p.tyres_age_laps} laps old, {wear:.0f}% worn."]
        if rate:
            parts.append(f"Wearing {rate:.1f}% per lap.")
        if data["laps_to_critical"] is not None and wear < self.engine.config.tyre_wear_critical_steps[0]:
            parts.append(f"About {data['laps_to_critical']:.0f} laps to the critical point.")
        if pace:
            s = pace["slope_s_per_lap"]
            parts.append(f"Losing {s:.2f} seconds per lap to tyre wear." if s > 0.005 else "Lap times are holding steady on this set")
        else:
            data["note"] = "Lap-time degradation needs more clean laps on this set."
        return self._ins(InsightType.TYRE_DEGREDATION_RATE, data, " ".join(parts))

    def undercut_report(self) -> Optional[Insight]:
        p, m = self.state.player, self.model
        rival = self.engine.strategy.rival_ahead()
        gap = self.state.player_gap_to_car_ahead()
        if p is None or rival is None or gap is None:
            return self._ins(InsightType.UNDERCUT_WINDOW, {"viable": None, "reason": "no car ahead or gap unknown"},
                             "There's no car ahead to undercut right now.")
        pace = self.pace_loss_per_lap()
        mine, theirs = self._my_pace_s(), self._recent_pace_s(self._rival_lap_times(rival.vehicle_index))
        trend = 0.0
        if mine and theirs:
            trend = max(-2.0, min(2.0, mine - theirs))
        data: Dict[str, Any] = {
            "gap_ahead_s": round(gap, 2), "rival_name": rival.name, "rival_position": rival.car_position,
            "rival_tyre_age": rival.tyres_age_laps, "rival_compound": _compound_name(rival.visual_tyre_compound),
            "rival_stops": rival.num_pit_stops, "player_tyre_age": p.tyres_age_laps,
            "player_compound": _compound_name(p.visual_tyre_compound),
            "rejoin_pos": self.state.session.pit_stop_rejoin_position,
            "gap_trend_s_per_lap": round(trend, 2) if (mine and theirs) else None,
            "assumptions": {"outlap_penalty_s": m.outlap_penalty_s, "rival_response_laps": m.rival_response_laps,
                            "margin_s": m.margin_s, "pit_loss_s": m.pit_loss_s}}
        who = rival.name or "the car ahead"
        if not pace:
            data.update(viable=None, reason="not enough clean laps on this set to measure tyre pace loss")
            return self._ins(InsightType.UNDERCUT_WINDOW, data,
                                f"I can't call the undercut yet. {who} is {gap:.1f} seconds up, "
                                f"but I need more clean laps on these tyres to measure your degradation.",
                                vehicle_idx=rival.vehicle_index)
        if pace["slope_s_per_lap"] <= 0:
            data.update(viable=False, reason="no measurable tyre pace loss",
                        tyre_pace_loss_s_per_lap=round(pace["slope_s_per_lap"], 3))
            return self._ins(InsightType.UNDERCUT_WINDOW, data,
                             f"No undercvucut for now. Your pace isn't dropping on these tyres, so an early stop won't gain on {who}.",
                             vehicle_idx=rival.vehicle_index)
        slope, age = pace["slope_s_per_lap"], p.tyres_age_laps or 0

        def net_gain(k: int) -> float:
            return max(0.0, slope * (age + k)) * m.rival_response_laps - m.outlap_penalty_s

        def gap_at(k: int) -> float:
            return max(0.0, gap + trend * k)

        window = next ((k for k in range(m.horizon_laps + 1) if net_gain(k) >= gap_at(k) + m.margin_s), None)
        data.update(viable=window == 0, pit_in_laps=window, net_gain_now_s=round(net_gain(0), 2),
                    tyre_pace_loss_s_per_lap=round(slope, 3), pace_fit_r2=round(pace["r_squared"], 2))
        if window == 0:
            msg = f"Yes, the undercut is on. Pitting now nets about {net_gain(0):.1f} seconds against a {gap:.1f} seconds gap to {who}."
        elif window is not None:
            msg = f"Not yet. The undercut works in about {window} laps; pitting now nets {net_gain(0):.1f} seconds against {gap:.1f}."
        else:
            msg = f"The undercut isn't there in the next {m.horizon_laps} laps. Pitting now nets {net_gain(0):.1f} seconds against a {gap:.1f} second gap."
        if data["rejoin_pos"]:
            msg += f" Rejoin would be P{data['rejoin_pos']}."
        if pace["r_squared"] < 0.3:
            msg += " The degradation fit is rough."
        return self._ins(InsightType.UNDERCUT_WINDOW, data, msg, vehicle_idx=rival.vehicle_index)

    def rival_report(self, ahead: bool = True) -> Optional[Insight]:
        p = self.state.player
        rival = self.engine.strategy.rival_ahead() if ahead else self.engine.strategy.rival_behind()
        if p is None or rival is None:
            return None
        gap = self.state.player_gap_to_car_ahead() if ahead else (rival.delta_to_car_in_front_ms or 0) / 1000 or None
        mine, theirs = self._my_pace_s(), self._recent_pace_s(self._rival_lap_times(rival.vehicle_index))
        pace_delta = round(theirs - mine, 2) if (mine and theirs) else None
        data = {"rival_name": rival.name, "rival_position": rival.car_position, "ahead": ahead,
                "gap_s": round(gap, 2) if gap else None, "compound": _compound_name(rival.visual_tyre_compound),
                "tyre_age": rival.tyres_age_laps, "stops": rival.num_pit_stops,
                "rival_pace_s": round(theirs, 3) if theirs else None, "my_pace_s": round(mine, 3) if mine else None,
                "rival_slower_by_s": pace_delta}
        side = "ahead" if ahead else "behind"
        msg = f"{rival.name or 'The car'} {side}" + (f" is {gap:.1f} seconds away" if gap else "") + f", on {rival.tyres_age_laps}-lap-old {data['compound'].lower()}s."
        if pace_delta is not None:
            msg += (f" They are {abs(pace_delta):.1f} seconds a lap {'slower' if pace_delta > 0 else 'faster'} than you.")
        return self._ins(InsightType.RIVAL_STATUS, data, msg, vehicle_idx=rival.vehicle_index)

    def _sector_bests(self) -> Optional[Tuple[List[int], List[int]]]:
        clean = _clean_laps(self.state.lap_history)
        if len(clean) < 2:
            return None
        bests: List[int] = []
        src: List[int] = []
        for n in (1, 2, 3):
            t, v = f"sector{n}_time_ms", f"sector{n}_valid"
            cands = [r for r in clean if getattr(r, t) > 0 and getattr(r, v)]
            if not cands:
                return None
            r = min(cands, key=lambda r: getattr(r, t))
            bests.append(getattr(r, t))
            src.append(r.lap_number)
        return bests, src
    
    def theoretical_best_report(self) -> Optional[Insight]:
        best = self.state.get_best_lap_record()
        sb = self._sector_bests()
        if best is None or sb is None:
            return self._ins(InsightType.THEORETICAL_BEST, {"available": False},
                             "I need a couple more clean laps before I can build a theoretical best.")
        bests, src = sb
        theory = sum(bests)
        gain = best.lap_time_ms - theory
        data = {"available": True, "theoretical_ms": theory, "theoretical_str": _ms_to_time_str(theory),
                "best_lap_ms": best.lap_time_ms, "best_lap_str": _ms_to_time_str(best.lap_time_ms),
                "best_lap_number": best.lap_number, "gain_ms": gain, "sector_best_ms": bests, "sector_best_laps": src}
        return self._ins(InsightType.THEORETICAL_BEST, data,
                         f"Theoretical best is {_ms_to_time_str(theory)}, {gain / 1000:.3f} seconds quicker than your best lap "
                         f"of {_ms_to_time_str(best.lap_time_ms)}. Best sectors came from laps {src[0]}, {src[1]} and {src[2]}.")

    def fuel_report(self) -> Optional[Insight]:
        p, f = self.state.player, self.engine.fuel
        left = self.state.laps_remaining()
        if p is None or p.fuel_remaining_laps is None or left is None:
            return None
        delta = p.fuel_remaining_laps - left
        data = {"fuel_remaining_laps": round(p.fuel_remaining_laps, 2), "laps_left": left, "delta_laps": round(delta, 2),
                "kg_per_lap": round(f._avg_fuel_per_lap(), 2), "fuel_in_tank_kg": round(p.fuel_in_tank or 0, 2)}
        cfg = self.engine.config
        state = ("short" if delta < cfg.fuel_save_delta_laps
                  else "in surplus" if delta > cfg.fuel_rich_delta_laps
                  else "on target")
        return self._ins(InsightType.FUEL_DELTA, data,
                         f"Fuel is {state}: {p.fuel_remaining_laps:.1f} laps in the tank for {left} to go ({delta:+.1f}).")

    def pit_window_report(self) -> Optional[Insight]:
        s, p = self.state.session, self.state.player
        if p is None or not s.pit_stop_window_ideal_lap or not s.pit_stop_window_latest_lap:
            return None
        lap = p.current_lap_num or 0
        wear = max(p.tyres_wear) if p.tyres_wear else 0
        to_crit = self.engine.tyre.laps_to_wear(wear, float(self.engine.config.tyre_wear_critical_steps[0]))
        data = {"ideal_lap": s.pit_stop_window_ideal_lap, "latest_lap": s.pit_stop_window_latest_lap, "current_lap": lap,
                "window_open": s.pit_stop_window_ideal_lap <= lap <= s.pit_stop_window_latest_lap,
                "rejoin_pos": s.pit_stop_rejoin_position, "laps_to_critical_wear": to_crit}
        msg = f"Pit window is lap {s.pit_stop_window_ideal_lap} to {s.pit_stop_window_latest_lap}; you're on lap {lap}."
        if s.pit_stop_rejoin_position:
            msg += f" Rejoin would be P{s.pit_stop_rejoin_position}."
        if to_crit is not None:
            msg += f" Tyres reach the critical point in about {to_crit:.0f} laps"
        return self._ins(InsightType.PIT_WINDOW_OPEN, data, msg)