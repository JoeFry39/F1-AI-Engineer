import threading
import time
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

from datetime import date
MADRID_REFERENCE_DATE = date(2026, 9, 13)

## SECTION 1 - Track ID -> Fast F1 Mapping

NO_REFERENCE_TRACKS = {42}

TRACK_ID_TO_FASTF1 = {
    0:  "Melbourne",
    2:  "Shanghai",
    3:  "Bahrain",
    4:  "Barcelona",
    5:  "Monaco",
    6:  "Montreal",
    7:  "Silverstone",
    9:  "Budapest",
    10: "Spa",
    11: "Monza",
    12: "Singapore",
    13: "Suzuka",
    14: "Abu Dhabi",
    15: "Austin",
    16: "São Paulo",
    17: "Spielberg",
    19: "Mexico City",
    20: "Baku",
    26: "Zandvoort",
    27: "Imola",
    29: "Jeddah",
    30: "Miami",
    31: "Las Vegas",
    32: "Lusail",
    # Reverse layouts — FastF1 doesn't distinguish, use same location
    39: "Silverstone",
    40: "Spielberg",
    41: "Zandvoort",
    # F1 26 DLC
    42: "Madrid" if date.today() >= MADRID_REFERENCE_DATE else None,  # Madrid - no ref until 13th sept '26
}

GAME_SESSION_TO_FASTF1 = {
    1:  "FP1",
    2:  "FP2",
    3:  "FP3",
    4:  "FP1",   # Short Practice → use FP1 as benchmark
    5:  "Q",     # Q1
    6:  "Q",     # Q2
    7:  "Q",     # Q3 → all map to Qualifying session
    8:  "Q",     # Short Qualifying
    9:  "Q",     # One-Shot Qualifying
    10: "SQ",    # Sprint Shootout 1
    11: "SQ",
    12: "SQ",
    13: "SQ",
    14: "SQ",
    15: "R",     # Race
    16: "R",
    17: "R",
    18: "Q",     # Time Trial → use Qualifying as reference
}

PRACTICE_SESSIONS = {1, 2, 3, 4}

## SECTION 2 - LoadState

class LoadState(Enum):
    IDLE = auto()
    LOADING = auto()
    READY = auto()
    FAILED = auto()
    BYPASSED = auto()

## SECTION 3 - CornerProfile

@dataclass
class CornerProfile:
    corner_number: int
    brake_point_m: float
    apex_distance_m: float
    apex_speed_kph: float
    exit_distance_m: float
    entry_speed_kph: float
    braking_zone_m: float

    @property
    def braking_commitment(self) -> float:
        return self.apex_distance_m - self.brake_point_m

## SECTION 4 - ReferenceProfile

@dataclass
class ReferenceProfile:
    driver_code: str
    driver_name: str
    team_name: str
    lap_time_ms: int
    track_name: str
    session_type: str
    year: int
    track_length_m: float
    loaded_at: float = field(default_factory=time.perf_counter)

    distance: Optional[np.ndarray] = None
    speed: Optional[np.ndarray] = None
    throttle: Optional[np.ndarray] = None
    brake: Optional[np.ndarray] = None
    gear: Optional[np.ndarray] = None
    rpm: Optional[np.ndarray] = None
    drs: Optional[np.ndarray] = None

    corners: List[CornerProfile] = field(default_factory=list)

    def speed_at(self, distance_m: float) -> Optional[float]:
        return self._lookup(self.speed, distance_m)

    def throttle_at(self, distance_m: float) -> Optional[float]:
        return self._lookup(self.throttle, distance_m)

    def brake_at(self, distance_m: float) -> Optional[float]:
        return self._lookup(self.brake, distance_m)

    def gear_at(self, distance_m: float) -> Optional[int]:
        val = self._lookup(self.gear, distance_m)
        return int(val) if val is not None else None

    def braking_delta_at(self, corner_distance_m: float, player_brake_point_m: float, search_window_m: float = 50.0,) -> Optional[float]:
        corner = self._nearest_corner(corner_distance_m, search_window_m)
        if corner is None:
            return None
        return player_brake_point_m - corner_distance_m

    def min_corner_speed_at(self, corner_distance_m: float, search_window_m: float = 50.0) -> Optional[float]:
        corner = self._nearest_corner(corner_distance_m, search_window_m)
        return corner.apex_speed_kph if corner else None

    def throttle_application_at(self, corner_distance_m: float, search_window_m: float = 50.0) -> Optional[float]:
        corner = self._nearest_corner(corner_distance_m, search_window_m)
        return corner.exit_distance_m if corner else None

    def speed_trace_window(self, start_m: float, end_m: float) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        if self.distance is None or self.speed is None:
            return None, None
        mask = (self.distance >= start_m) & (self.distance <= end_m)
        return self.distance[mask], self.speed[mask]

    def throttle_trace_window(self, start_m: float, end_m: float) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        if self.distance is None or self.throttle is None:
            return None, None
        mask = (self.distance >= start_m) & (self.distance <= end_m)
        return self.distance[mask], self.throttle[mask]

    def brake_trace_window(self, start_m: float, end_m: float) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        if self.distance is None or self.brake is None:
            return None, None
        mask = (self.distance >= start_m) & (self.distance <= end_m)
        return self.distance[mask], self.brake[mask]

    def full_trace(self) -> Dict[str, Optional[np.ndarray]]:
        return{
            "distance": self.distance,
            "speed": self.speed,
            "throttle": self.throttle,
            "brake": self.brake,
            "gear": self.gear,
            "rpm": self.rpm,
            "drs": self.drs,
        }

    def _lookup(self, array: Optional[np.ndarray], distance_m: float) -> Optional[float]:
        if array is None or self.distance is None:
            return None
        idx = int(round(distance_m))
        idx = max(0, min(idx, len(array) - 1))
        return float(array[idx])

    def _nearest_corner(self, distance_m: float, window_m: float) -> Optional[CornerProfile]:
        if not self.corners:
            return None
        candidates = [c for c in self.corners if abs(c.apex_distance_m - distance_m) <= window_m]
        if not candidates:
            return None
        return min(candidates, key=lambda c: abs(c.apex_distance_m - distance_m))

    @property
    def lap_time_str(self) -> str:
        if self.lap_time_ms <= 0:
            return "--:--.---"
        minutes = self.lap_time_ms // 60000
        seconds = (self.lap_time_ms % 60000) // 1000
        millis = self.lap_time_ms % 1000
        return f"{minutes}:{seconds:02d}.{millis:03d}"

    def __repr__(self) -> str:
        return(
            f"ReferenceProfile({self.driver_code}, "
            f"{self.track_name} {self.year} {self.session_type}, "
            f"{self.lap_time_str}, "
            f"corners={len(self.corners)}"
        )

## SECTION 5 - FastF1 Loader

class FastF1Loader:
    DRS_ON_THRESHOLD = 10
    CORNER_APEX_SPEED_THRESHOLD_KPH = 250
    MIN_BRAKING_ZONE_M = 15.0
    BRAKE_HEAVY_THRESHOLD = 0.5

    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_enabled = False

    def _ensure_cache(self) -> None:
        if not self._cache_enabled:
            try:
                import fastf1
                fastf1.Cache.enable_cache(str(self.cache_dir))
                self._cache_enabled = True
                logger.info(f"FastF1 cache enabled at {self.cache_dir}")
            except Exception as e:
                logger.warning(f"FastF1 cache setup failed: {e}")

    def load_session_profiles(
            self,
            year: int,
            location: str,
            session_type: str,
            max_drivers: int = 3,
    ) -> List[ReferenceProfile]:
        self._ensure_cache()
        try:
            import fastf1
        except ImportError:
            logger.error("FastF1 not installed. Run pip install fastf1")
            return[]
        try:
            logger.info(f"Loading FastF1: {year} {location} {session_type}")
            session = fastf1.get_session(year, location, session_type)
            session.load(
                telemetry=True,
                laps=True,
                weather=False,
                messages=False,
            )
        except Exception as e:
            logger.error(f"FastF1 session load failed: {e}")
            return[]
        try:
            driver_codes = self._rank_drivers(session, session_type)
        except Exception as e:
            logger.error(f"Driver ranking failed: {e}")
            return[]
        profiles = []
        for driver_code in driver_codes[:max_drivers]:
            try:
                profile = self._build_profile(session, driver_code, session_type, year, location)
                if profile is not None:
                    profiles.append(profile)
                    logger.info(f"Loaded profile: {profile}")
            except Exception as e:
                logger.warning(f"Profile build failed for {driver_code}: {e}")
                continue
        return profiles

    def _rank_drivers(self, session, session_type: str) -> List[str]:
        try:
            laps = session.laps.copy()
            laps = laps[laps["Deleted"] == False] if "Deleted" in laps.columns else laps
            laps = laps.dropna(subset=["LapTime"])
            fastest_per_driver = (
                laps.loc[laps.groupby("Driver")["LapTime"].idxmin()]
                .sort_values("LapTime")
            )
            return list(fastest_per_driver["Driver"])
        except Exception as e:
            logger.warning(f"Could not rank drivers, using results order: {e}")
            try:
                return list(session.results["Abbreviation"].head(10))
            except Exception:
                return[]

    def _build_profile(
            self,
            session,
            driver_code: str,
            session_type: str,
            year: int,
            location: str,
    ) -> Optional[ReferenceProfile]:
        driver_laps = session.laps.pick_driver(driver_code)
        if driver_laps.empty:
            logger.warning(f"No laps found for {driver_code}")
            return None
        fastest_lap = driver_laps.pick_fastest()
        if fastest_lap is None or fastest_lap.empty:
            return None
        lap_time_td = fastest_lap["LapTime"]
        if hasattr(lap_time_td, "total_seconds"):
            lap_time_ms = int(lap_time_td.total_seconds() * 1000)
        else:
            lap_time_ms = 0
        try:
            tel = fastest_lap.get_car_data().add_distance()
        except Exception as e:
            logger.warning(f"Telemetry load failed for {driver_code}: {e}")
            return None
        if tel.empty or "Distance" not in tel.columns:
            return None
        driver_name, team_name = self._get_driver_info(session, driver_code)
        track_length_m = float(tel["Distance"].max())
        if track_length_m < 100:
            logger.warning(f"Suspiciously short track for {driver_code}: {track_length_m}m")
            return None
        dist_arr, speed_arr, throttle_arr, brake_arr, gear_arr, rpm_arr, drs_arr = (self._interpolate_to_distance_axis(tel, track_length_m))
        corners = self._detect_corners(dist_arr, speed_arr, brake_arr)
        return ReferenceProfile(
            driver_code = driver_code,
            driver_name = driver_name,
            team_name = team_name,
            lap_time_ms = lap_time_ms,
            track_name = location,
            session_type = session_type,
            year = year,
            track_length_m = track_length_m,
            distance = dist_arr,
            speed = speed_arr,
            throttle = throttle_arr,
            brake = brake_arr,
            gear = gear_arr,
            rpm = rpm_arr,
            drs = drs_arr,
            corners = corners,
        )

    def _interpolate_to_distance_axis(self, tel, track_length_m: float) -> Tuple:
        raw_dist = tel["Distance"].to_numpy(dtype=np.float64)
        target_dist = np.arange(0, int(track_length_m) + 1, dtype=np.float32)

        def interp_continuous(col_name: str) -> np.ndarray:
            if col_name not in tel.columns:
                return np.zeros(len(target_dist), dtype = np.float32)
            raw = tel[col_name].to_numpy(dtype = np.float64)
            valid = ~np.isnan(raw)
            if valid.sum() < 2:
                return np.zeros(len(target_dist), dtype = np.float32)
            return np.interp(target_dist, raw_dist[valid], raw[valid]).astype(np.float32)

        def interp_discrete(col_name: str, dtype = np.float32) -> np.ndarray:
            if col_name not in tel.columns:
                return np.zeros(len(target_dist), dtype = dtype)
            raw = tel[col_name].to_numpy()
            result = np.empty(len(target_dist), dtype = dtype)
            for i, d in enumerate(target_dist):
                idx = np.searchsorted(raw_dist, d)
                idx = min(idx, len(raw) - 1)
                result[i] = dtype(raw[idx])
            return result
        speed_arr = interp_continuous("Speed")
        throttle_arr = interp_continuous("Throttle") / 100.0
        rpm_arr = interp_continuous("RPM")
        if "Brake" in tel.columns:
            raw_brake = tel["Brake"].to_numpy().astype(np.float64)
            if np.nanmax(raw_brake) > 1.0:
                raw_brake = raw_brake / 100.0
            brake_arr = np.interp(target_dist, raw_dist, raw_brake).astype(np.float32)
        else:
            brake_arr = np.zeros(len(target_dist), dtype = np.float32)
        gear_arr = interp_discrete("nGear", dtype = np.float32)
        if "DRS" in tel.columns:
            raw_drs = (tel["DRS"].to_numpy() >= self.DRS_ON_THRESHOLD).astype(np.float64)
            drs_arr = np.interp(target_dist, raw_dist, raw_drs).astype(np.float32)
        else:
            drs_arr = np.zeros(len(target_dist), dtype = np.float32)
        return target_dist, speed_arr, throttle_arr, brake_arr, gear_arr, rpm_arr, drs_arr

    def _detect_corners(
            self,
            dist_arr: np.ndarray,
            speed_arr: np.ndarray,
            brake_arr: np.ndarray,
    ) -> List[CornerProfile]:
        corners = []
        n = len(speed_arr)
        if n < 10:
            return corners
        window = 30
        apex_indices = []
        for i in range(window, n - window):
            if speed_arr[i] >= self.CORNER_APEX_SPEED_THRESHOLD_KPH:
                continue
            left = speed_arr[max(0, i-window):i]
            right = speed_arr[i+1:min(n, i+window+1)]
            if len(left) == 0 or len(right) == 0:
                continue
            if(speed_arr[i] <= np.min(left) and speed_arr[i] <= np.min(right)):
                apex_indices.append(i)
                # local_min = np.min(speed_arr[max(0, i-window):min(n, i+window)])
                # if abs(speed_arr[i] - local_min) < 2.0:
                #     if speed_arr[i] < speed_arr[i - window] and speed_arr[i] < speed_arr[i+window]:
                #         apex_indices.append(i)

        merged = []
        skip_until = -1
        for i, idx in enumerate(apex_indices):
            if idx <= skip_until:
                continue
            group = [idx]
            for j in range(i + 1, len(apex_indices)):
                if apex_indices[j] - idx <= 50:
                    group.append(apex_indices[j])
                    skip_until = apex_indices[j]
                else:
                    break
            best = min(group, key=lambda x: speed_arr[x])
            merged.append(best)
        corner_number = 1
        for apex_idx in merged:
            apex_dist = float(dist_arr[apex_idx])
            apex_speed = float(speed_arr[apex_idx])
            entry_speed, brake_point_m = self._find_brake_point(dist_arr, speed_arr, brake_arr, apex_idx)
            exit_dist = self._find_exit_point(dist_arr, brake_arr, apex_idx, n)
            braking_zone = apex_dist - brake_point_m
            if braking_zone < self.MIN_BRAKING_ZONE_M:
                continue
            corners.append(CornerProfile(
                corner_number = corner_number,
                brake_point_m = brake_point_m,
                apex_distance_m = apex_dist,
                apex_speed_kph = apex_speed,
                exit_distance_m = exit_dist,
                entry_speed_kph = entry_speed,
                braking_zone_m = braking_zone,
            ))
            corner_number += 1
        logger.info(f"Detected {len(corners)} corners")
        return corners

    def _find_brake_point(
            self,
            dist_arr: np.ndarray,
            speed_arr: np.ndarray,
            brake_arr: np.ndarray,
            apex_idx: int,
    ) -> Tuple[float, float]:
        search_back = min(apex_idx, 300)
        for i in range(apex_idx, apex_idx - search_back, -1):
            if i < 0:
                break
            if brake_arr[i] >= self.BRAKE_HEAVY_THRESHOLD:
                return float(speed_arr[i]), float(dist_arr[i])
        fallback_idx = max(0, apex_idx - 50)
        return float(speed_arr[fallback_idx]), float(dist_arr[fallback_idx])

    def _find_exit_point(
            self,
            dist_arr: np.ndarray,
            brake_arr: np.ndarray,
            apex_idx: int,
            n: int,
    ) -> float:
        search_fwd = min(n - apex_idx - 1, 200)
        for i in range(apex_idx, apex_idx + search_fwd):
            if i >= n:
                break
            if brake_arr[i] < 0.1:
                return float(dist_arr[i])
        return float(dist_arr[min(apex_idx + 50, n - 1)])

    def _get_driver_info(self, session, driver_code: str) -> Tuple[str, str]:
        try:
            results = session.results
            row = results[results["Abbreviation"] == driver_code]
            if row.empty:
                return driver_code, "Unknown"
            driver_name = str(row.iloc[0].get("FullName", driver_code))
            team_name = str(row.iloc[0].get("TeamName", "Unknown"))
            return driver_name, team_name
        except Exception:
            return driver_code, "Unknown"

## SECTION 6 - ReferenceDataManager

class ReferenceDataManager:
    def __init__(self, cache_dir: str = "sessions/fastf1_cache"):
        self._loader = FastF1Loader(cache_dir)
        self._profiles: Dict[str, ReferenceProfile] = {}
        self._load_state: LoadState = LoadState.IDLE
        self._load_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._last_track_id: Optional[int] = None
        self._last_session_type: Optional[int] = None
        self._last_year: Optional[int] = None
        self._bypass_reason: str = ""
        self._regulation_warning: bool = False

    def trigger_load(
            self,
            track_id: int,
            game_session_type: int,
            packet_format: int = 2025,
            regulations_2026: bool = False,
    ) -> None:
        with self._lock:
            if (self._load_state == LoadState.LOADING or
                (self._load_state == LoadState.READY and
                 track_id == self._last_track_id and
                 game_session_type == self._last_session_type)):
                return
            bypass, reason = self._should_bypass(track_id, packet_format, regulations_2026)
            if bypass:
                self._load_state = LoadState.BYPASSED
                self._bypass_reason = reason
                logger.info(f"Reference data bypassed: {reason}")
                return
            year = self._select_year(track_id, packet_format, regulations_2026)
            fastf1_session = self._map_session_type(game_session_type)
            location = TRACK_ID_TO_FASTF1.get(track_id)
            if location is None:
                self._load_state = LoadState.BYPASSED
                self._bypass_reason = f"No FastF1 mapping for track_id={track_id}"
                return
            self._last_track_id = track_id
            self._last_session_type = game_session_type
            self._last_year = year
            self._load_state = LoadState.LOADING
            self._profiles.clear()
            self._load_thread = threading.Thread(
                target = self._background_load,
                args = (year, location, fastf1_session),
                daemon = True,
                name = "ReferenceDataLoader",
            )
            self._load_thread.start()
            logger.info(
                f"Reference data load triggered: "
                f"{year} {location} {fastf1_session}"
            )

    def _background_load(
            self,
            year: int,
            location: str,
            session_type: str,
    ) -> None:
        try:
            profiles = self._loader.load_session_profiles(
                year = year,
                location = location,
                session_type = session_type,
                max_drivers = 3,
            )
            with self._lock:
                if profiles:
                    self._profiles = {p.driver_code: p for p in profiles}
                    self._load_state = LoadState.READY
                    logger.info(
                        f"Reference data ready: "
                        f"{[p.driver_code for p in profiles]}"
                    )
                else:
                    self._load_state = LoadState.FAILED
                    logger.warning("Reference data load returned no profiles")

        except Exception as e:
            with self._lock:
                self._load_state = LoadState.FAILED
            logger.error(f"Reference data background load failed: {e}")

    def _should_bypass(
            self,
            track_id: int,
            packet_format: int,
            regulations_2026: bool,
    ) -> Tuple[bool, str]:
        if track_id in NO_REFERENCE_TRACKS:
            return True, "No reference data available"
        return False, ""

    def _has_2026_race_occurred(self, location: str) -> bool:
        try:
            import fastf1
            from datetime import datetime, timezone
            schedule = fastf1.get_event_schedule(2026, include_testing=False)
            event = schedule[schedule["Location"].str.contains(location, case=False, na=False)]
            if event.empty:
                return False
            race_date = event.iloc[0].get("Session5DateUtc") or event.iloc[0].get("EventDate")
            if race_date is None:
                return False
            if hasattr(race_date, "tzinfo") and race_date.tzinfo is None:
                race_date = race_date.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return now > race_date.to_pydatetime() if hasattr(race_date, "to_pydatetime") else now.timestamp() > race_date.timestamp()
        except Exception as e:
            logger.warning(f"Could not check 2026 race schedule: {e}")
            return False

    def _select_year(
            self,
            track_id: int,
            packet_format: int,
            regulations_2026: bool,
    ) -> int:
        self._regulation_warning = False
        if packet_format >= 2026 and regulations_2026:
            location = TRACK_ID_TO_FASTF1.get(track_id)
            if location:
                if self._has_2026_race_occurred(location):
                    return 2026
                else:
                    self._regulation_warning = True
                    logger.info(
                        f"2026-spec car at {location}: no 2026 race yet, "
                        f"using 2025 data with regulation warning"
                    )
                    return 2025
        return 2025

    def _map_session_type(self, game_session_type: int) -> str:
        if game_session_type in PRACTICE_SESSIONS:
            return "Q"
        return GAME_SESSION_TO_FASTF1.get(game_session_type, "Q")

    @property
    def load_state(self) -> LoadState:
        return self._load_state

    @property
    def is_ready(self) -> bool:
        return self._load_state == LoadState.READY

    @property
    def is_loading(self) -> bool:
        return self._load_state == LoadState.LOADING

    @property
    def is_bypassed(self) -> bool:
        return self._load_state == LoadState.BYPASSED

    @property
    def bypass_reason(self) -> str:
        return self._bypass_reason

    @property
    def regulation_warning(self) -> bool:
        return self._regulation_warning

    @property
    def all_profiles(self) -> List[ReferenceProfile]:
        with self._lock:
            return sorted(self._profiles.values(), key=lambda p: p.lap_time_ms)

    @property
    def fastest_profile(self) -> Optional[ReferenceProfile]:
        profiles = self.all_profiles
        return profiles[0] if profiles else None

    def get_profile(self, driver_code: str) -> Optional[ReferenceProfile]:
        with self._lock:
            return self._profiles.get(driver_code.upper())

    def get_corner_profiles(self, driver_code: Optional[str] = None) -> List[CornerProfile]:
        if driver_code:
            profile = self.get_profile(driver_code)
        else:
            profile = self.fastest_profile
        return profile.corners if profile else []

    def braking_delta(
            self,
            corner_distance_m: float,
            player_brake_point_m: float,
            driver_code: Optional[str] = None,
    ) -> Optional[float]:
        profile = (
            self.get_profile(driver_code) if driver_code
            else self.fastest_profile
        )
        if profile is None:
            return None
        return profile.braking_delta_at(corner_distance_m, player_brake_point_m)

    def speed_delta_at(
            self,
            distance_m: float,
            player_speed: float,
            driver_code: Optional[str] = None,
    ) -> Optional[float]:
        profile = (self.get_profile(driver_code) if driver_code else self.fastest_profile)
        if profile is None:
            return None
        ref_speed = profile.speed_at(distance_m)
        if ref_speed is None:
            return None
        return player_speed - ref_speed

    def status_message(self) -> str:
        state = self._load_state
        if state == LoadState.IDLE:
            return "Reference data: not requested"
        elif state == LoadState.LOADING:
            loc = TRACK_ID_TO_FASTF1.get(self._last_track_id or -1, "?")
            return f"Loading {self._last_year} {loc} reference data..."
        elif state == LoadState.READY:
            drivers = ", ".join(p.driver_code for p in self.all_profiles)
            base = f"Reference data ready: {drivers}"
        if self._regulation_warning:
            base += (
                f"-- WARNING: 2026-spec car vs 2025 data "
                f"(2026 race not yet run at this circuit). "
                f"Comparison accuracy will improve as the 2026 season progresses"
            )
            return base
        elif state == LoadState.FAILED:
            return "Reference data unavailable -- self-comparison only"
        elif state == LoadState.BYPASSED:
            return f"Reference bypassed: {self._bypass_reason}"
        return "Unknown"

    def __repr__(self) -> str:
        return (
            f"ReferenceDataManager("
            f"state={self._load_state.name}, "
            f"profiles={list(self._profiles.keys())})"
        )