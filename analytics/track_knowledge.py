"""
analytics/track_knowledge.py

provides static, circuit specific knowledge for the engineer pipeline

this module owns all circuit data at runtime with no dependency on
FastF1, the internet, or any live data source
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class CornerSpeed(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def from_apex_speed(cls, speed_kph: float) -> "CornerSpeed":
        if speed_kph >= 200:
            return cls.HIGH
        elif speed_kph >= 120:
            return cls.MEDIUM
        return cls.LOW

class CornerType(Enum):
    HAIRPIN = "hairpin"
    SLOW_CHICANE = "slow_chicane"
    FAST_CHICANE = "fast_chicane"
    MEDIUM_RADIUS = "medium_radius"
    HIGH_SPEED_SWEEP = "high_speed_sweep"
    DOUBLE_APEX = "double_apex"
    LONG_RADIUS = "long_radius"

class CornerDirection(Enum):
    LEFT = "left"
    RIGHT = "right"

class SectorNumber(Enum):
    S1 = 1
    S2 = 2
    S3 = 3

class ZoneType(Enum):
    DRS = "drs"
    PIT_ENTRY = "pit_entry"
    PIT_EXIT = "pit_exit"
    SAFETY_CAR = "safety_car_delta"

@dataclass(frozen=True)
class CornerInfo:
    corner_number: int
    name: Optional[str]
    sector: SectorNumber
    direction: CornerDirection
    speed_class: CornerSpeed
    corner_type: CornerType

    distance_brake_m: float
    distance_apex_m: float
    distance_exit_m: float

    reference_apex_speed_kph: float
    reference_braking_zone_m: float

    lift_only: bool = False
    flat_out: bool = False
    shared_braking_with_previous: bool = False

    heading_change_deg: Optional[float] = None
    radius_m: Optional[float] = None
    estimated_lateral_g: Optional[float] = None

    tyre_sensitive: bool = False

    overtaking_opportunity: bool = False

    drs_activation_after: bool = False

    notes: str = ""

    @property
    def display_name(self) -> str:
        if self.name:
            return self.name
        return f"Turn {self.corner_number}"

    @property
    def braking_zone_length_m(self) -> Optional[float]:
        if self.distance_apex_m is None or self.distance_brake_m is None:
            return None
        return self.distance_apex_m - self.distance_brake_m

    def contains_distance(self, distance_m: float, margin_m: float = 50.0) -> bool:
        return((self.distance_brake_m - margin_m) <= distance_m <= (self.distance_exit_m + margin_m))

@dataclass(frozen=True)
class DRSZone:
    zone_number: int
    detection_m: float
    activation_m: float
    end_m: float
    straight_name: Optional[str] = None
    available_in: List[int] = field(default_factory=lambda: [2025, 2026])
    notes: str = ""

@dataclass(frozen=True)
class PitZone:
    pit_entry_m: float
    pit_exit_m: float
    speed_limit_kph: int

@dataclass
class TrackKnowledge:
    ## Identity
    track_id: int
    name: str
    location: str
    country: str
    fastf1_name: str

    ## Layout
    track_length_m: float
    num_corners: int
    lap_record_s: Optional[float] = None
    reference_season: Optional[int] = None

    ## Sectors
    sector2_distance_m: float = 0.0
    sector3_distance_m: float = 0.0

    ## Corners
    corners: List[CornerInfo] = field(default_factory=list)

    ## DRS Zones
    drs_zones: List[DRSZone] = field(default_factory=list)

    ## Pit Lane
    pit_zone: Optional[PitZone] = None

    ## Circuit Characteristics
    high_speed_circuit: bool = False
    street_circuit: bool = False
    tyre_degradation_high: bool = False
    overtaking_difficulty: str = "medium"

    ## Elevation
    elevation_change_m: float = 0.0

    ## Notes
    notes: str = ""

    ## Corner Lookup
    def get_corner_at(self, distance_m: float, margin_m: float = 50.0) -> Optional[CornerInfo]:
        candidates = [c for c in self.corners if c.contains_distance(distance_m, margin_m)]
        if not candidates:
            return None
        return min(candidates, key=lambda c: abs(c.distance_apex_m - distance_m))

    def get_corner_by_number(self, corner_number: int) -> Optional[CornerInfo]:
        for corner in self.corners:
            if corner.corner_number == corner_number:
                return corner
        return None

    def get_corners_by_speed(self, speed_class: CornerSpeed) -> List[CornerInfo]:
        return [c for c in self.corners if c.speed_class == speed_class]

    def get_corners_by_type(self, corner_type: CornerType) -> List[CornerInfo]:
        return [c for c in self.corners if c.corner_type == corner_type]

    def get_corners_in_sector(self, sector: SectorNumber) -> List[CornerInfo]:
        return [c for c in self.corners if c.sector == sector]

    def get_tyre_sensitive_corners(self) -> List[CornerInfo]:
        return [c for c in self.corners if c.tyre_sensitive]

    def get_overtaking_corners(self) -> List[CornerInfo]:
        return [c for c in self.corners if c.overtaking_opportunity]

    def get_active_drs_zones(self, season: int) -> List[DRSZone]:
        return[zone for zone in self.drs_zones if season in zone.available_in]

    def sector_for_distance(self, distance_m: float) -> SectorNumber:
        if distance_m >= self.sector3_distance_m:
            return SectorNumber.S3
        elif distance_m >= self.sector2_distance_m:
            return SectorNumber.S2
        return SectorNumber.S1

    def __repr__(self) -> str:
        return(
            f"TrackKnowledge({self.name}, "
            f"{self.num_corners} corners, "
            f"{self.track_length_m:.0f}m)"
        )

def _corner_from_dict(d: dict) -> CornerInfo:
    return CornerInfo(
        corner_number = d["corner_number"],
        name = d.get("name"),
        sector = SectorNumber(d["sector"]),
        direction = CornerDirection(d["direction"]),
        speed_class = CornerSpeed(d["speed_class"]),
        corner_type = CornerType(d["corner_type"]),
        distance_brake_m = d["distance_brake_m"],
        distance_apex_m = d["distance_apex_m"],
        distance_exit_m = d["distance_exit_m"],
        reference_apex_speed_kph = d["reference_apex_speed_kph"],
        reference_braking_zone_m = d["reference_braking_zone_m"],
        tyre_sensitive = d.get("tyre_sensitive", False),
        overtaking_opportunity = d.get("overtaking_opportunity", False),
        drs_activation_after = d.get("drs_activation_after", False),
        notes = d.get("notes", ""),
    )

def _drs_zone_from_dict(d: dict) -> DRSZone:
    return DRSZone(
        zone_number = d["zone_number"],
        detection_m = d["detection_m"],
        activation_m = d["activation_m"],
        end_m = d["end_m"],
        straight_name = d.get("straight_name"),
        available_in = d.get("available_in", [2025, 2026]),
        notes = d.get("notes", "")
    )
    

def _pit_zone_from_dict(d: dict) -> PitZone:
    return PitZone(
        pit_entry_m = d["pit_entry_m"],
        pit_exit_m = d["pit_exit_m"],
        speed_limit_kph = d.get("speed_limit_kph", 80),
    )

def _track_from_dict(d: dict) -> TrackKnowledge:
    return TrackKnowledge(
        track_id = d["track_id"],
        name = d["name"],
        location = d["location"],
        country = d["country"],
        fastf1_name = d["fastf1_name"],
        reference_season=d.get("reference_season"),
        track_length_m = d["track_length_m"],
        num_corners = d["num_corners"],
        lap_record_s = d.get("lap_record_s"),
        sector2_distance_m = d.get("sector2_distance_m", 0.0),
        sector3_distance_m = d.get("sector3_distance_m", 0.0),
        corners = [_corner_from_dict(c) for c in d.get("corners", [])],
        drs_zones = [_drs_zone_from_dict(z) for z in d.get("drs_zones", [])],
        pit_zone = _pit_zone_from_dict(d["pit_zone"]) if d.get("pit_zone") else None,
        high_speed_circuit = d.get("high_speed_circuit", False),
        street_circuit = d.get("street_circuit", False),
        tyre_degradation_high = d.get("tyre_degradation_high", False),
        overtaking_difficulty = d.get("overtaking_difficulty", "medium"),
        elevation_change_m = d.get("elevation_change_m", 0.0),
        notes = d.get("notes", ""),
    )

def track_to_dict(tk: TrackKnowledge) -> Dict:
    def corner_to_dict(c: CornerInfo) -> Dict:
        return {
            "corner_number": c.corner_number,
            "name": c.name,
            "sector": c.sector.value,
            "direction": c.direction.value,
            "speed_class": c.speed_class.value,
            "corner_type": c.corner_type.value,
            "distance_brake_m": None if c.distance_brake_m is None else round(c.distance_brake_m, 1),
            "distance_apex_m": None if c.distance_apex_m is None else round(c.distance_apex_m, 1),
            "distance_exit_m": None if c.distance_exit_m is None else round(c.distance_exit_m, 1),
            "reference_apex_speed_kph": None if c.reference_apex_speed_kph is None else round(c.reference_apex_speed_kph, 1),
            "reference_braking_zone_m": None if c.reference_braking_zone_m is None else round(c.reference_braking_zone_m, 1),
            "tyre_sensitive": c.tyre_sensitive,
            "overtaking_opportunity": c.overtaking_opportunity,
            "drs_activation_after": c.drs_activation_after,
            "lift_only": c.lift_only,
            "flat_out": c.flat_out,
            "shared_braking_with_previous": c.shared_braking_with_previous,
            "heading_change_deg": None if c.heading_change_deg is None else round(c.heading_change_deg, 1),
            "radius_m": None if c.radius_m is None else round(c.radius_m, 1),
            "estimated_lateral_g": None if c.estimated_lateral_g is None else round(c.estimated_lateral_g, 2),
            "notes": c.notes,
        }

    def drs_to_dict(z: DRSZone) -> Dict:
        return {
            "zone_number": z.zone_number,
            "detection_m": round(z.detection_m, 1),
            "activation_m": round(z.activation_m, 1),
            "end_m": round(z.end_m, 1),
            "straight_name": z.straight_name,
            "available_in": z.available_in,
        }

    result = {
        "track_id": tk.track_id,
        "name": tk.name,
        "location": tk.location,
        "country": tk.country,
        "fastf1_name": tk.fastf1_name,
        "reference_season": tk.reference_season,
        "track_length_m": round(tk.track_length_m, 1),
        "num_corners": tk.num_corners,
        "lap_record_s": tk.lap_record_s,
        "sector2_distance_m": round(tk.sector2_distance_m, 1),
        "sector3_distance_m": round(tk.sector3_distance_m, 1),
        "high_speed_circuit": tk.high_speed_circuit,
        "street_circuit": tk.street_circuit,
        "tyre_degradation_high": tk.tyre_degradation_high,
        "overtaking_difficulty": tk.overtaking_difficulty,
        "elevation_change_m": round(tk.elevation_change_m, 1),
        "notes": tk.notes,
        "corners": [corner_to_dict(c) for c in tk.corners],
        "drs_zones": [drs_to_dict(z) for z in tk.drs_zones],
        "pit_zone":{
            "pit_entry_m": round(tk.pit_zone.pit_entry_m, 1),
            "pit_exit_m": round(tk.pit_zone.pit_exit_m, 1),
            "speed_limit_kph": tk.pit_zone.speed_limit_kph,
        } if tk.pit_zone else None,
    }
    return result

class TrackKnowledgeBase:
    DEFAULT_TRACKS_DIR = Path(__file__).parent / "tracks"

    def __init__(self, tracks_dir: Optional[Path] = None):
        self._dir: Path = tracks_dir or self.DEFAULT_TRACKS_DIR
        self._cache: Dict[int, TrackKnowledge] = {}
        self._index: Dict[int, Path] = self._build_index()

        logger.info(
            f"TrackKnowledgeBase initialised: "
            f"{len(self._index)} circuits available at {self._dir}"
        )

    def _build_index(self) -> Dict[int, Path]:
        index: Dict[int, Path] = {}
        if not self._dir.exists():
            logger.warning(
                f"Tracks directory not found: {self._dir}. "
                f"Run tools/generate_track_knowledge.py to generate circuit files"
            )
            return index
        for path in sorted(self._dir.glob("*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    tid = data.get("track_id")
                    if tid is not None:
                        index[int(tid)] = path
            except Exception as e:
                logger.warning(f"Could not index {path.name}: {e}")
        return index

    def get(self, track_id: int) -> Optional[TrackKnowledge]:
        if track_id in self._cache:
            return self._cache[track_id]
        path = self._index.get(track_id)
        if path is None:
            logger.debug(f"No track knowledge file for track_id={track_id}")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tk = _track_from_dict(data)
            self._cache[track_id] = tk
            logger.info(f"Loaded track knowledge: {tk}")
            return tk
        except Exception as e:
            logger.error(f"Failed to load track knowledge for track_id{track_id}: {e}")
            return None

    def get_corner(self, track_id: int, distance_m: float, margin_m: float = 50.0) -> Optional[CornerInfo]:
        tk = self.get(track_id)
        if tk is None:
            return None
        return tk.get_corner_at(distance_m, margin_m)

    def is_loaded(self, track_id: int) -> bool:
        return track_id in self._cache

    def is_available(self, track_id: int) -> bool:
        return track_id in self._index

    def preload(self, track_id: int) -> None:
        self.get(track_id)

    @property
    def available_track_ids(self) -> List[int]:
        return sorted(self._index.keys())

    def __repr__(self) -> str:
        return(
            f"TrackKnowledgeBase("
            f"available={len(self._index)}, "
            f"cached={len(self._cache)})"
        )