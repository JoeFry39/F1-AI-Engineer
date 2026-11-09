## One time script to generate static circuit JSON files

## run:: pip install fastf1 numpy

from __future__ import annotations
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

from datetime import date
MADRID_REFERENCE_DATE = date(2026, 9, 13)

sys.path.insert(0, str(Path(__file__).parent.parent))

from analytics.track_knowledge import(
    TrackKnowledge,
    CornerInfo,
    DRSZone,
    PitZone,
    CornerSpeed,
    CornerType,
    CornerDirection,
    SectorNumber,
    track_to_dict,
)

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "analytics" / "tracks"

CIRCUIT_LIST: Dict[int, Tuple[str, str]] = {
    0: ("Australian Grand Prix", "melbourne"),
    2: ("Chinese Grand Prix", "shanghai"),
    3: ("Bahrain Grand Prix", "bahrain"),
    4: ("Spanish Grand Prix", "barcelona"),
    5: ("Monaco Grand Prix", "monaco"),
    6: ("Canadian Grand Prix", "montreal"),
    7: ("British Grand Prix", "silverstone"),
    9: ("Hungarian Grand Prix", "budapest"),
    10: ("Belgian Grand Prix", "spa"),
    11: ("Italian Grand Prix", "monza"),
    12: ("Singapore Grand Prix", "singapore"),
    13: ("Japanese Grand Prix", "suzuka"),
    14: ("Abu Dhabi Grand Prix", "abu_dhabi"),
    15: ("United States Grand Prix", "austin"),
    16: ("São Paulo Grand Prix", "sao_paulo"),
    17: ("Austrian Grand Prix", "spielberg"),
    19: ("Mexico City Grand Prix", "mexico_city"),
    20: ("Azerbaijan Grand Prix", "baku"),
    26: ("Dutch Grand Prix", "zandvoort"),
    27: ("Emilia Romagna Grand Prix", "imola"),
    29: ("Saudi Arabian Grand Prix", "jeddah"),
    30: ("Miami Grand Prix", "miami"),
    31: ("Las Vegas Grand Prix", "las_vegas"),
    32: ("Qatar Grand Prix", "lusail"),
}

if date.today() >= MADRID_REFERENCE_DATE:
    CIRCUIT_LIST[42] = ("Madrid", "madrid")

REVERSE_LAYOUT_MAP: Dict[int, int] = {
    39: 7,
    40: 17,
    41: 26,
}

"""
Template

"name": "",
"location": "",
"country": "",
"high_speed_circuit": ,
"street_circuit": ,
"tyre_degradation_high": ,
"overtaking_difficulty": "",
"elevation_change_m": ,
"notes": "",
"corners": [
    {
    "corner_number": ,
    "name": "",
    "type": "",
    "direction": "",
    "tyre_sensitive": ,
    "overtaking": ,
    "drs_after": ,
    "notes": "",
    },
],
"drs_zones": [
    {
    "zone_number": ,
    "straight": "",
    "after_corner": ,
    "before_corner": ,
    "available_in": [],
    "notes": "",
    },
],
"pit": {"speed_limit_kph": , "notes": ""}
"""

MANUAL_METADATA: Dict[str, dict] = {
    "melbourne": {
        "name": "Albert Park Circuit",
        "location": "Melbourne",
        "country": "Australia",
        "high_speed_circuit": True,
        "street_circuit": True,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "medium",
        "elevation_change_m": 8.0,
        "notes": "Fast semi-street circuit with smooth asphalt, significant track evolution across weekend, and multiple heavy braking zones. Exit speed onto the long straights is critical for overtaking.",
        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the pit straight. Primary overtaking opportunity",
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Good traction on exit is important for the short straight into Turn 3",
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking zone at the end of the short straight.",
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Flows immediately into the high-speed sequence.",
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "High speed commitment corner with sustained lateral load.",
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast direction change leading into the sweeping middle sector.",
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Precision on entry sets up the following fast section.",
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "High-speed corner where confidence and aerodynamic grip are key.",
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "fast_chicane",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast transition into the braking zone for Turn 11",
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "fast_chicane",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed is crucial into Lakeside Drive.",
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking zone and another realistic overtaking opportunity.",
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Short transition towards the final sector.",
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Technical corner leading into the final turn.",
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed determines speed along the pit straight.",
            },
        ],
        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 14,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 14. Detection before the final corner.",
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 2 and 3",
                "after_corner": 2,
                "before_corner": 3,
                "available_in": [2025, 2026],
                "notes": "Short assisted zone into Turn 3",
            },
            {
                "zone_number": 3,
                "straight": "Between Turns 5 and 6",
                "after_corner": 5,
                "before_corner": 6,
                "available_in": [2026],
                "notes": "Straight Mode only",
            },
            {
                "zone_number": 4,
                "straight": "Lakeside Drive",
                "after_corner": 8,
                "before_corner": 9,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 10. Detection before Turn 9.",
            },
            {
                "zone_number": 5,
                "straight": "Between Turns 10 and 11",
                "after_corner": 10,
                "before_corner": 11,
                "available_in": [2026],
                "notes": "Straight Mode only",
            },
        ],
        "pit": {"speed_limit_kph": 80, "notes": "Pit entry immediately before Turn 14. Pit exit rejoins after Turn 2."}
    },

    "shanghai": {
        "name": "Shanghai International Circuit",
        "location": "Shanghai",
        "country": "China",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": True,
        "overtaking_difficulty": "easy",
        "elevation_change_m": 12.0,
        "notes": "Permanent Tilke-designed circuit featuring one of the longest straights in Formula 1, a unique tightening opening complex, and several long-radius corners that heavily load the left-front tyre.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": True,
                "drs_after": False,
                "notes": "Unique tightening right-hander entered at high speed. Drivers trail brake for a long duration."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Continuation of the opening spiral. Left-front tyre experiences heavy sustained load."
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Exit traction is important for the run to Turn 6."
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Acceleration onto the short straight."
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Technical left leading into Turn 6."
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking hairpin and overtaking opportunity."
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast flowing left requiring aerodynamic confidence."
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "High lateral G-load. One of the quickest corners on the circuit."
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Braking while changing direction."
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "long_radius",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Long accelerating right-hander leading towards Turn 11."
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Technical transition before the final complex."
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Builds speed towards the long Turn 13."
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Very long right-hander. Exit speed determines velocity along the 1.2 km back straight."
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the longest straight. Primary overtaking opportunity."
            },
            {
                "corner_number": 15,
                "name": "Turn 15",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Quick change of direction after Turn 14."
            },
            {
                "corner_number": 16,
                "name": "Turn 16",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is critical onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 16,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 16."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 4 and 6",
                "after_corner": 4,
                "before_corner": 6,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced for the 2026 regulations."
            },
            {
                "zone_number": 3,
                "straight": "Between Turns 10 and 11",
                "after_corner": 10,
                "before_corner": 11,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced for the 2026 regulations."
            },
            {
                "zone_number": 4,
                "straight": "Back Straight",
                "after_corner": 13,
                "before_corner": 14,
                "available_in": [2025, 2026],
                "notes": "Longest straight on the circuit. Activation after Turn 13."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Turn 16. Pit exit rejoins before Turn 1."
        },
    },

    "bahrain": {
        "name": "Bahrain International Circuit",
        "location": "Sakhir",
        "country": "Bahrain",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": True,
        "overtaking_difficulty": "easy",
        "elevation_change_m": 18.0,
        "notes": "Permanent desert circuit with abrasive asphalt, significant rear tyre degradation, multiple heavy braking zones, and excellent overtaking opportunities aided by long straights.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the pit straight. Primary overtaking opportunity."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Quick transition after Turn 1."
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed is critical onto the second DRS straight."
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after the second DRS zone."
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Downhill entry into the technical middle sector."
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Flows into Turn 7."
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Technical change of direction."
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Slow left hairpin leading into the downhill braking zone."
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Off-camber entry with difficult braking."
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "long_radius",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "One of the most difficult braking corners on the calendar. Easy to lock the unloaded front tyre."
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": True,
                "drs_after": False,
                "notes": "Fast right-hander after the third DRS zone."
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Flat-out change of direction."
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Late apex required for maximum exit speed."
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Beginning of the final complex."
            },
            {
                "corner_number": 15,
                "name": "Turn 15",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is crucial onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 15,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 15."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 3 and 4",
                "after_corner": 3,
                "before_corner": 4,
                "available_in": [2025, 2026],
                "notes": "Short straight into Turn 4."
            },
            {
                "zone_number": 3,
                "straight": "Between Turns 10 and 11",
                "after_corner": 10,
                "before_corner": 11,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 10."
            },
            {
                "zone_number": 4,
                "straight": "Between Turns 13 and 14",
                "after_corner": 13,
                "before_corner": 14,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced for the 2026 regulations."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Turn 15. Pit exit rejoins before Turn 1."
        },
    },

    "barcelona": {
        "name": "Circuit de Barcelona-Catalunya",
        "location": "Montmeló",
        "country": "Spain",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": True,
        "overtaking_difficulty": "medium",
        "elevation_change_m": 30.0,
        "notes": "Technical circuit with a representative mix of corner speeds. Long loaded corners place high stress on the front-left tyre. The final chicane was removed in 2023, restoring the fast final sector.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1 - Elf",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the pit straight. Primary overtaking opportunity."
            },
            {
                "corner_number": 2,
                "name": "Turn 2 - Renault",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Completes the opening complex."
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Long, loaded right-hander that heavily wears the front-left tyre."
            },
            {
                "corner_number": 4,
                "name": "Turn 4 - Repsol",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after the back straight."
            },
            {
                "corner_number": 5,
                "name": "Turn 5 - Seat",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 9,
                "name": "Turn 9 - Campsa",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Fast uphill right-hander. Exit speed is critical onto the back straight."
            },
            {
                "corner_number": 10,
                "name": "Turn 10 - La Caixa",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after the back straight. Major overtaking opportunity."
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 12,
                "name": "Turn 12 - Banc Sabadell",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Long left-hander generating sustained tyre load."
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 14,
                "name": "Turn 14 - New Holland",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": ""
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 14,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 15."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 3 and 4",
                "after_corner": 3,
                "before_corner": 4,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced for the 2026 regulations."
            },
            {
                "zone_number": 3,
                "straight": "Between Turns 5 and 6",
                "after_corner": 5,
                "before_corner": 7,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced for the 2026 regulations."
            },
            {
                "zone_number": 4,
                "straight": "Between Turns 9 and 10",
                "after_corner": 9,
                "before_corner": 10,
                "available_in": [2025, 2026],
                "notes": "Long back straight into Turn 10."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry before the final corner. Pit exit rejoins before Turn 1."
        },
    },

    "monaco": {
        "name": "Circuit de Monaco",
        "location": "Monte Carlo",
        "country": "Monaco",
        "high_speed_circuit": False,
        "street_circuit": True,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "very_hard",
        "elevation_change_m": 42.0,
        "notes": "Iconic street circuit with extremely narrow barriers, constant elevation changes, and the lowest average speed of the Formula One calendar. Qualifying is usually more important than race pace due to the lack of overtaking opportunities.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1 - Sainte Dévote",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after the pit straight. The circuit's main overtaking opportunity."
            },
            {
                "corner_number": 2,
                "name": "Turn 2 - Beau Rivage",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast uphill kink leading towards Massenet."
            },
            {
                "corner_number": 3,
                "name": "Turn 3 - Massenet",
                "type": "long_radius",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "High-speed uphill left requiring precision."
            },
            {
                "corner_number": 4,
                "name": "Turn 4 - Casino",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Entry to Casino Square."
            },
            {
                "corner_number": 5,
                "name": "Turn 5 - Mirabeau Haute",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Steep downhill braking zone."
            },
            {
                "corner_number": 6,
                "name": "Turn 6 - Fairmont Hairpin",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Slowest corner in Formula One."
            },
            {
                "corner_number": 7,
                "name": "Turn 7 - Mirabeau Bas",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Short downhill run towards the Grand Hotel section."
            },
            {
                "corner_number": 8,
                "name": "Turn 8 - Portier",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Critical traction point leading into the tunnel."
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Inside the tunnel"
            },
            {
                "corner_number": 10,
                "name": "Turn 10 - Nouvelle Chicane",
                "type": "slow_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after the tunnel. Rare overtaking opportunity."
            },
            {
                "corner_number": 11,
                "name": "Turn 11 - Nouvelle Chicane Exit",
                "type": "slow_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Exit kerb can unsettle the car."
            },
            {
                "corner_number": 12,
                "name": "Turn 12 - Tabac",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Very fast left with minimal runoff."
            },
            {
                "corner_number": 13,
                "name": "Turn 13 - Swimming Pool Entry",
                "type": "fast_chicane",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Aggressive left entry into the Swimming Pool complex."
            },
            {
                "corner_number": 14,
                "name": "Turn 14 - Swimming Pool",
                "type": "fast_chicane",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "High-speed direction change requiring commitment."
            },
            {
                "corner_number": 15,
                "name": "Turn 15 - Swimming Pool Exit",
                "type": "slow_chicane",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Exit chicane of swimming pool"
            },
            {
                "corner_number": 16,
                "name": "Turn 16",
                "type": "slow_chicane",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": ""
            },
            {
                "corner_number": 17,
                "name": "Turn 17",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Sweep before La Rascasse"
            },
            {
                "corner_number": 18,
                "name": "Turn 18 - La Rascasse",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Very tight right-hander before the final corner."
            },
            {
                "corner_number": 19,
                "name": "Turn 19 - Antony Noghès",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is important onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 19,
                "before_corner": 1,
                "available_in": [2025],
                "notes": "Only DRS/Straight Mode zone. Activation after Antony Noghès."
            },
        ],

        "pit": {
            "speed_limit_kph": 60,
            "notes": "Pit entry after Antony Noghès. Pit exit rejoins before Sainte Dévote."
        },
    },

    "montreal": {
        "name": "Circuit Gilles Villeneuve",
        "location": "Montreal",
        "country": "Canada",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "easy",
        "elevation_change_m": 6.0,
        "notes": "Semi-permanent circuit on Île Notre-Dame featuring long straights separated by heavy braking chicanes. Low tyre degradation, frequent safety cars, and excellent overtaking opportunities.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1 - Senna",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the pit straight."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Completes the opening complex."
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "slow_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "First part of the Turns 3-4 chicane."
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "slow_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed is important onto the back straight."
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "L'Épingle hairpin. Major overtaking opportunity."
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "fast_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "High-speed left entry into the casino section."
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "fast_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Quick direction change."
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Short acceleration before the final sector."
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "Heavy braking into hairpin"
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Long straight before final chicanes"
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Leads towards the Wall of Champions."
            },
            {
                "corner_number": 13,
                "name": "Turn 13 - Wall of Champions",
                "type": "fast_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Final corner before Wall of Champions."
            },
            {
                "corner_number": 14,
                "name": "Turn 14 - Wall of Champions",
                "type": "fast_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is crucial onto the pit straight while avoiding the Wall of Champions."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 14,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 11."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 7 and 8",
                "after_corner": 7,
                "before_corner": 8,
                "available_in": [2025, 2026],
                "notes": "Short straight."
            },
            {
                "zone_number": 3,
                "straight": "Between Turns 11 and 13",
                "after_corner": 11,
                "before_corner": 13,
                "available_in": [2025, 2026],
                "notes": "Straight after hairpin to final chicane."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry before the final chicane. Pit exit rejoins after Turn 2."
        },
    },

    "silverstone": {
        "name": "Silverstone Circuit",
        "location": "Silverstone",
        "country": "United Kingdom",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": True,
        "overtaking_difficulty": "medium",
        "elevation_change_m": 11.0,
        "notes": "One of the fastest circuits on the calendar with flowing high-speed corners, several iconic sequences, and multiple overtaking opportunities. Aerodynamic efficiency and confidence through fast corners are critical.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1 - Abbey",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Flat-out in qualifying. Precision on entry is vital."
            },
            {
                "corner_number": 2,
                "name": "Turn 2 - Farm",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Flat-out kink leading into Village."
            },
            {
                "corner_number": 3,
                "name": "Turn 3 - Village",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after the pit straight. Good overtaking opportunity."
            },
            {
                "corner_number": 4,
                "name": "Turn 4 - The Loop",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Slowest corner on the circuit."
            },
            {
                "corner_number": 5,
                "name": "Turn 5 - Aintree",
                "type": "long_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed determines performance down Wellington Straight."
            },
            {
                "corner_number": 6,
                "name": "Turn 6 - Brooklands",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of Wellington Straight."
            },
            {
                "corner_number": 7,
                "name": "Turn 7 - Luffield",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Long traction zone that rewards patience."
            },
            {
                "corner_number": 8,
                "name": "Turn 8 - Woodcote",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Fast exit onto the National Pit Straight."
            },
            {
                "corner_number": 9,
                "name": "Turn 9 - Copse",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Iconic high-speed corner requiring maximum commitment."
            },
            {
                "corner_number": 10,
                "name": "Turn 10 - Maggotts",
                "type": "fast_chicane",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Beginning of the famous Maggotts-Becketts sequence."
            },
            {
                "corner_number": 11,
                "name": "Turn 11 - Maggotts",
                "type": "fast_chicane",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Rapid direction change with high aerodynamic load."
            },
            {
                "corner_number": 12,
                "name": "Turn 12 - Becketts",
                "type": "fast_chicane",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Maintaining momentum is essential."
            },
            {
                "corner_number": 13,
                "name": "Turn 13 - Becketts",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed is critical onto Hangar Straight."
            },
            {
                "corner_number": 14,
                "name": "Turn 14 - Chapel",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after Hangar Straight. Prime overtaking opportunity."
            },
            {
                "corner_number": 15,
                "name": "Turn 15 - Stowe",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after Hangar Straight. Prime overtaking opportunity."
            },
            {
                "corner_number": 16,
                "name": "Turn 16 - Vale",
                "type": "slow_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Hard braking into the Vale chicane."
            },
            {
                "corner_number": 17,
                "name": "Turn 17 - Vale",
                "type": "slow_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Second part of the Vale chicane."
            },
            {
                "corner_number": 18,
                "name": "Turn 18 - Club",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Long final corner. Exit speed is crucial onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 18,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Club."
            },
            {
                "zone_number": 2,
                "straight": "Wellington Straight",
                "available_in": [2025, 2026],
                "after_corner": 5,
                "before_corner": 6,
                "notes": "Activation after Aintree."
            },
            {
                "zone_number": 3,
                "straight": "Between Vale and Club",
                "after_corner": 7,
                "before_corner": 9,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced for the 2026 regulations."
            },
            {
                "zone_number": 4,
                "straight": "Hangar Straight",
                "after_corner": 14,
                "before_corner": 15,
                "available_in": [2025, 2026],
                "notes": "Activation after Chapel."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry before Vale. Pit exit rejoins after Abbey."
        },
    },

    "budapest": {
        "name": "Hungaroring",
        "location": "Budapest",
        "country": "Hungary",
        "high_speed_circuit": False,
        "street_circuit": False,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "hard",
        "elevation_change_m": 34.0,
        "notes": "Tight and technical circuit often compared to Monaco without barriers. Overtaking is difficult, making qualifying especially important. The layout rewards downforce, traction, and rhythm through consecutive corners.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "Heavy braking at the end of the pit straight. Primary overtaking opportunity."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Long left-hander requiring patience on throttle."
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed is critical onto the back straight."
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast uphill left taken with high commitment."
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Medium-speed right leading into the technical middle sector."
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "slow_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "First part of the chicane."
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "slow_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Second part of the chicane."
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Beginning of the flowing final sector."
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Maintaining momentum is important."
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Leads into the fast right-hander."
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast corner requiring confidence and aerodynamic grip."
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Sets up the final braking zone."
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "Hairpin leading onto the pit straight. Secondary overtaking opportunity."
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Long final corner. Exit speed is crucial onto the main straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 14,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 14."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 1 and 2",
                "after_corner": 1,
                "before_corner": 2,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 1."
            },
            {
                "zone_number": 3,
                "straight": "Between Turns 3 and 4",
                "after_corner": 3,
                "before_corner": 4,
                "available_in": [2026],
                "notes": "Back straight following Turn 3."
            },
            {
                "zone_number": 4,
                "straight": "Between Turns 11 and 12",
                "after_corner": 11,
                "before_corner": 12,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced for the 2026 regulations."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Turn 14. Pit exit rejoins before Turn 1."
        },
    },

    "spa": {
        "name": "Circuit de Spa-Francorchamps",
        "location": "Stavelot",
        "country": "Belgium",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "easy",
        "elevation_change_m": 102.0,
        "notes": "The longest circuit on the calendar featuring dramatic elevation changes, very high average speeds, unpredictable weather, and several of Formula One's most iconic corners. Slipstreaming and overtaking are major characteristics.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1 - La Source",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "Tight opening hairpin and the best overtaking opportunity on the circuit."
            },
            {
                "corner_number": 2,
                "name": "Turn 2 - Eau Rouge",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Legendary uphill left beginning the Eau Rouge-Raidillon sequence."
            },
            {
                "corner_number": 3,
                "name": "Turn 3 - Raidillon",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Blind uphill crest. Exit speed is critical onto the Kemmel Straight."
            },
            {
                "corner_number": 4,
                "name": "Turn 4 - Raidillon",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Blind uphill crest. Exit speed is critical onto the Kemmel Straight."
            },
            {
                "corner_number": 5,
                "name": "Turn 5 - Les Combes",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after Kemmel Straight."
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Second part of Les Combes"
            },
            {
                "corner_number": 7,
                "name": "Turn 7 - Malmedy",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Completes the Les Combes complex."
            },
            {
                "corner_number": 8,
                "name": "Turn 8 - Bruxelles",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Downhill hairpin with another overtaking opportunity."
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Speed corner"
            },
            {
                "corner_number": 10,
                "name": "Turn 11 - Pouhon",
                "type": "double_apex",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast left requiring precision."
            },
            {
                "corner_number": 11,
                "name": "Turn 11 - Pouhon",
                "type": "double_apex",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Very fast left-hander demanding commitment."
            },
            {
                "corner_number": 12,
                "name": "Turn 12 - Les Fagnes",
                "type": "fast_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "First part of the Fagnes chicane."
            },
            {
                "corner_number": 13,
                "name": "Turn 13 - Les Fagnes",
                "type": "fast_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Second part of the Fagnes chicane."
            },
            {
                "corner_number": 14,
                "name": "Turn 14 - Stavelot",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Technical right-hander"
            },
            {
                "corner_number": 15,
                "name": "Turn 15 - Courbe Paul Frère",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Long accelerating corner."
            },
            {
                "corner_number": 16,
                "name": "Turn 16 - Blanchimont",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast section towards bus stop chicane."
            },
            {
                "corner_number": 17,
                "name": "Turn 17 - Blanchimont",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "One of the fastest corners on the calendar."
            },
            {
                "corner_number": 18,
                "name": "Turn 18 - Bus Stop",
                "type": "slow_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "First part of the final chicane."
            },
            {
                "corner_number": 19,
                "name": "Turn 19 - Bus Stop",
                "type": "slow_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is critical onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 18,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after the Bus Stop chicane."
            },
            {
                "zone_number": 2,
                "straight": "Between Turn 1 and 2",
                "available_in": [2026],
                "after_corner": 1,
                "before_corner": 2,
                "notes": "Additional Straight Mode zone introduced for the 2026 regulations."
            },
            {
                "zone_number": 3,
                "straight": "Kemmel Straight",
                "after_corner": 4,
                "before_corner": 5,
                "available_in": [2025, 2026],
                "notes": "Activation after Raidillon."
            },
            {
                "zone_number": 4,
                "straight": "Between Stavelot and Blanchimont",
                "after_corner": 15,
                "before_corner": 16,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced for the 2026 regulations."
            },
            {
                "zone_number": 5,
                "straight": "Between Blanchimont and Bus Stop",
                "after_corner": 17,
                "before_corner": 18,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced for the 2026 regulations."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry before the Bus Stop chicane. Pit exit rejoins before La Source."
        },
    },

    "monza": {
        "name": "Autodromo Nazionale Monza",
        "location": "Monza",
        "country": "Italy",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "easy",
        "elevation_change_m": 12.0,
        "notes": "The Temple of Speed. The fastest circuit on the Formula One calendar, featuring long straights separated by heavy braking zones and low-downforce setup requirements. Slipstreaming and overtaking are defining characteristics.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1 - Prima Variante",
                "type": "slow_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the pit straight. Primary overtaking opportunity."
            },
            {
                "corner_number": 2,
                "name": "Turn 2 - Prima Variante",
                "type": "slow_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Second part of the opening chicane."
            },
            {
                "corner_number": 3,
                "name": "Turn 3 - Curva Biassono",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Flat-out right-hander formerly known as Curva Grande."
            },
            {
                "corner_number": 4,
                "name": "Turn 4 - Variante della Roggia",
                "type": "slow_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after Curva Biassono."
            },
            {
                "corner_number": 5,
                "name": "Turn 5 - Variante della Roggia",
                "type": "slow_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Second part of the Roggia chicane."
            },
            {
                "corner_number": 6,
                "name": "Turn 6 - Lesmo 1",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast right-hander requiring strong front-end grip."
            },
            {
                "corner_number": 7,
                "name": "Turn 7 - Lesmo 2",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed is critical onto the Serraglio straight."
            },
            {
                "corner_number": 8,
                "name": "Turn 8 - Variante Ascari",
                "type": "fast_chicane",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "First part of the famous Ascari complex."
            },
            {
                "corner_number": 9,
                "name": "Turn 9 - Variante Ascari",
                "type": "fast_chicane",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Middle of the Ascari sequence."
            },
            {
                "corner_number": 10,
                "name": "Turn 10 - Variante Ascari",
                "type": "fast_chicane",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed determines top speed along the back straight."
            },
            {
                "corner_number": 11,
                "name": "Turn 11 - Curva Alboreto",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Formerly Parabolica. Long final corner where exit speed is crucial onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 11,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Curva Alboreto."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 3 and 4",
                "after_corner": 3,
                "before_corner": 4,
                "available_in": [2025, 2026],
                "notes": "Curva Biassono into Variante della Roggia."
            },
            {
                "zone_number": 3,
                "straight": "Between Turns 7 and 8",
                "after_corner": 7,
                "before_corner": 8,
                "available_in": [2026],
                "notes": "Straight Mode along the Serraglio straight after Lesmo 2."
            },
            {
                "zone_number": 4,
                "straight": "Between Turns 10 and 11",
                "after_corner": 10,
                "before_corner": 11,
                "available_in": [2026],
                "notes": "Straight Mode after Variante Ascari."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry before Curva Alboreto. Pit exit rejoins before Prima Variante."
        },
    },

    "singapore": {
        "name": "Marina Bay Street Circuit",
        "location": "Singapore",
        "country": "Singapore",
        "high_speed_circuit": False,
        "street_circuit": True,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "hard",
        "elevation_change_m": 9.0,
        "notes": "Demanding night street circuit with high humidity, close walls, frequent traction zones and heavy braking. One of the most physically demanding races on the Formula One calendar.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1 - Sheares",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the pit straight. Primary overtaking opportunity."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Part of the opening complex."
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Exit determines speed towards Turn 5."
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast kink taken flat."
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed is critical onto the Nicoll Highway straight."
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Flat-out left kink."
            },
            {
                "corner_number": 7,
                "name": "Turn 7 - Memorial",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after the longest straight."
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Technical traction zone."
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Narrow approach with walls close."
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Flows into the technical middle sector."
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast left leading towards the hairpin."
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "Very slow hairpin. Excellent overtaking opportunity."
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "Heavy braking beneath the grandstand."
            },
            {
                "corner_number": 15,
                "name": "Turn 15",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": ""
            },
            {
                "corner_number": 16,
                "name": "Turn 16",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Beginning of the final sector."
            },
            {
                "corner_number": 17,
                "name": "Turn 17",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 18,
                "name": "Turn 18",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 19,
                "name": "Turn 19",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is critical onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 19,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 19."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 5 and 7",
                "after_corner": 5,
                "before_corner": 7,
                "available_in": [2025, 2026],
                "notes": "Nicoll Highway straight."
            },
            {
                "zone_number": 3,
                "straight": "Between Turns 9 and 10",
                "after_corner": 9,
                "before_corner": 10,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced for the 2026 regulations."
            },
            {
                "zone_number": 4,
                "straight": "Between Turns 13 and 14",
                "after_corner": 13,
                "before_corner": 14,
                "available_in": [2025, 2026],
                "notes": "Esplanade Bridge straight."
            },
            {
                "zone_number": 5,
                "straight": "Between Turns 15 and 16",
                "after_corner": 15,
                "before_corner": 16,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced for the 2026 regulations."
            },
        ],

        "pit": {
            "speed_limit_kph": 60,
            "notes": "Pit entry after Turn 19. Pit exit rejoins before Turn 1."
        },
    },

    "suzuka": {
        "name": "Suzuka Circuit",
        "location": "Suzuka",
        "country": "Japan",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": True,
        "overtaking_difficulty": "hard",
        "elevation_change_m": 40.0,
        "notes": "Unique figure-of-eight circuit renowned for its flowing high-speed corners, technical esses and commitment through 130R. Driver precision and aerodynamic efficiency are critical.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1 - First Curve",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": True,
                "drs_after": False,
                "notes": "Fast downhill entry from the main straight. Primary overtaking opportunity."
            },
            {
                "corner_number": 2,
                "name": "Turn 2 - First Curve",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Exit sets up the Esses."
            },
            {
                "corner_number": 3,
                "name": "Turn 3 - S Curves",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Beginning of the iconic Esses."
            },
            {
                "corner_number": 4,
                "name": "Turn 4 - S Curves",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Rhythm and precision are vital."
            },
            {
                "corner_number": 5,
                "name": "Turn 5 - S Curves",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 6,
                "name": "Turn 6 - S Curves",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 7,
                "name": "Turn 7 - Dunlop Curve",
                "type": "long_radius",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Long uphill left-hander."
            },
            {
                "corner_number": 8,
                "name": "Turn 8 - Degner 1",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast commitment corner."
            },
            {
                "corner_number": 9,
                "name": "Turn 9 - Degner 2",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Easy to run wide into the gravel."
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Under the bridge."
            },
            {
                "corner_number": 11,
                "name": "Turn 11 - Hairpin",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Best overtaking opportunity outside Turn 1."
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Builds speed towards Spoon."
            },
            {
                "corner_number": 13,
                "name": "Turn 13 - Spoon Curve",
                "type": "double_apex",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "First apex of Spoon."
            },
            {
                "corner_number": 14,
                "name": "Turn 14 - Spoon Curve",
                "type": "double_apex",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed is critical onto the back straight."
            },
            {
                "corner_number": 15,
                "name": "Turn 15 - 130R",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Legendary flat-out left-hander."
            },
            {
                "corner_number": 16,
                "name": "Turn 16 - Casio Triangle",
                "type": "slow_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after 130R."
            },
            {
                "corner_number": 17,
                "name": "Turn 17 - Casio Triangle",
                "type": "slow_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Second part of the chicane."
            },
            {
                "corner_number": 18,
                "name": "Turn 18 - Final Curve",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed determines top speed along the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 18,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 18."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 14 and 15",
                "after_corner": 14,
                "before_corner": 15,
                "available_in": [2025, 2026],
                "notes": "Straight Mode after Spoon Curve towards 130R."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry before the Casio Triangle. Pit exit rejoins before Turn 1."
        },
    },

    "abu_dhabi": {
        "name": "Yas Marina Circuit",
        "location": "Abu Dhabi",
        "country": "United Arab Emirates",
        "high_speed_circuit": False,
        "street_circuit": False,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "medium",
        "elevation_change_m": 12.0,
        "notes": "Modern permanent circuit featuring two long straights, heavy braking zones and a technical final sector. Redesigned in 2021 to improve racing and overtaking.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "Hairpin leading onto the longest straight. Exit speed is critical."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast left-hand kink."
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Flat-out right-hand bend."
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "Heavy braking after the first long straight."
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Flat-out kink."
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Beginning of the technical middle sector."
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": ""
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Flows through the hotel section."
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 15,
                "name": "Turn 15",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 16,
                "name": "Turn 16",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is critical onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 16,
                "before_corner": 1,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced for the 2026 regulations."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 5 and 6",
                "after_corner": 5,
                "before_corner": 6,
                "available_in": [2025, 2026],
                "notes": "Longest straight on the circuit."
            },
            {
                "zone_number": 3,
                "straight": "Between Turns 8 and 9",
                "after_corner": 8,
                "before_corner": 9,
                "available_in": [2025, 2026],
                "notes": "Second DRS/Straight Mode zone."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Turn 16. Pit exit rejoins before Turn 1."
        },
    },

    "austin": {
        "name": "Circuit of the Americas",
        "location": "Austin",
        "country": "United States",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": True,
        "overtaking_difficulty": "easy",
        "elevation_change_m": 41.0,
        "notes": "Purpose-built circuit featuring a dramatic uphill first corner, high-speed esses inspired by Silverstone, heavy braking zones and one of the widest track layouts on the calendar.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1 - Big Red",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Steep uphill braking zone and the primary overtaking opportunity."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Beginning of the high-speed esses."
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Exit onto the back straight."
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit onto the long back straight."
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after the back straight."
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 15,
                "name": "Turn 15",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Another heavy braking opportunity."
            },
            {
                "corner_number": 16,
                "name": "Turn 16",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Beginning of the long carousel."
            },
            {
                "corner_number": 17,
                "name": "Turn 17",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Continuation of the carousel."
            },
            {
                "corner_number": 18,
                "name": "Turn 18",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Long loaded right-hander."
            },
            {
                "corner_number": 19,
                "name": "Turn 19",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 20,
                "name": "Turn 20",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is critical onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 20,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 20."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 11 and 12",
                "after_corner": 11,
                "before_corner": 12,
                "available_in": [2025, 2026],
                "notes": "Longest straight on the circuit."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Turn 20. Pit exit rejoins before Turn 1."
        },
    },

    "sao_paulo": {
        "name": "Autódromo José Carlos Pace",
        "location": "São Paulo",
        "country": "Brazil",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "medium",
        "elevation_change_m": 43.0,
        "notes": "Short anti-clockwise circuit combining long full-throttle sections with a technical infield. Significant elevation changes and variable weather often influence strategy.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1 - Senna S",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy downhill braking and the best overtaking opportunity on the circuit."
            },
            {
                "corner_number": 2,
                "name": "Turn 2 - Senna S",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Second part of the Senna S."
            },
            {
                "corner_number": 3,
                "name": "Turn 3 - Curva do Sol",
                "type": "long_radius",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed is critical onto the Reta Oposta."
            },
            {
                "corner_number": 4,
                "name": "Turn 4 - Descida do Lago",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after the back straight."
            },
            {
                "corner_number": 5,
                "name": "Turn 5 - Descida do Lago",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Left onto straight."
            },
            {
                "corner_number": 6,
                "name": "Turn 6 - Ferradura",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast downhill right-hander."
            },
            {
                "corner_number": 7,
                "name": "Turn 7 - Ferradura",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast downhill right-hander."
            },
            {
                "corner_number": 8,
                "name": "Turn 8 - Laranjinha",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Right before double hairpin."
            },
            {
                "corner_number": 9,
                "name": "Turn 9 - Pinheirinho",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Hairpin."
            },
            {
                "corner_number": 10,
                "name": "Turn 10 - Bico de Pato",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Tightest corner on the circuit."
            },
            {
                "corner_number": 11,
                "name": "Turn 11 - Mergulho",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Left towards T12."
            },
            {
                "corner_number": 12,
                "name": "Turn 12 - Juncão",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Critical traction zone leading onto the pit straight."
            },
            {
                "corner_number": 13,
                "name": "Turn 13 - Subida dos Boxes",
                "type": "long_radius",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Flat-out uphill left."
            },
            {
                "corner_number": 14,
                "name": "Turn 14 - Subida dos Boxes",
                "type": "long_radius",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Flat-out uphill left."
            },
            {
                "corner_number": 15,
                "name": "Turn 15 - Arquibancadas",
                "type": "long_radius",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Continuation onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 14,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Juncão."
            },
            {
                "zone_number": 2,
                "straight": "Reta Oposta",
                "after_corner": 3,
                "before_corner": 4,
                "available_in": [2025, 2026],
                "notes": "Activation after Curva do Sol."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Juncão. Pit exit rejoins before the Senna S."
        },
    },

    "spielberg": {
        "name": "Red Bull Ring",
        "location": "Spielberg",
        "country": "Austria",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "easy",
        "elevation_change_m": 65.0,
        "notes": "One of the shortest circuits on the calendar. Features three long straights separated by heavy braking zones, followed by a flowing downhill final sector. Significant elevation change creates unique braking challenges.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1 - Castrol Edge",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "Fast uphill right-hander. Exit speed is important onto the second straight."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Flat-out left kink."
            },
            {
                "corner_number": 3,
                "name": "Turn 3 - Remus",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "Highest point on the circuit. Major overtaking opportunity after the uphill straight."
            },
            {
                "corner_number": 4,
                "name": "Turn 4 - Schlossgold",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast downhill left kink."
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Quick direction change before the final sector."
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast downhill left requiring commitment."
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Technical right-hander beginning the final complex."
            },
            {
                "corner_number": 8,
                "name": "Turn 8 - Rindt",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Very fast blind right-hander."
            },
            {
                "corner_number": 9,
                "name": "Turn 9 - Red Bull Mobile",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast downhill left."
            },
            {
                "corner_number": 10,
                "name": "Turn 10 - Jochen Rindt",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is critical onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 10,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 10."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 1 and 3",
                "after_corner": 1,
                "before_corner": 3,
                "available_in": [2025, 2026],
                "notes": "Longest uphill straight on the circuit."
            },
            {
                "zone_number": 3,
                "straight": "Between Turns 3 and 4",
                "after_corner": 3,
                "before_corner": 4,
                "available_in": [2025, 2026],
                "notes": "Second uphill straight after Remus."
            },
            {
                "zone_number": 4,
                "straight": "Between Turns 8 and 9",
                "after_corner": 8,
                "before_corner": 9,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced in the F1 25 2026 Season Pack."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Turn 10. Pit exit rejoins before Turn 1."
        },
    },

    "mexico_city": {
        "name": "Autódromo Hermanos Rodríguez",
        "location": "Mexico City",
        "country": "Mexico",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "easy",
        "elevation_change_m": 12.0,
        "notes": "High-altitude circuit at over 2,200 metres above sea level. Thin air reduces drag and downforce, creating very high straight-line speeds while reducing aerodynamic grip through the corners.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the pit straight. Primary overtaking opportunity."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Part of the opening complex."
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed determines performance along the long back straight."
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after the back straight."
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Beginning of the fast Esses."
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": ""
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Entry into the stadium section."
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Stadium section."
            },
            {
                "corner_number": 15,
                "name": "Turn 15",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 16,
                "name": "Turn 16",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 17,
                "name": "Turn 17 - Peraltada",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is critical onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 17,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 17."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 3 and 4",
                "after_corner": 3,
                "before_corner": 4,
                "available_in": [2025, 2026],
                "notes": "Longest straight on the circuit."
            },
            {
                "zone_number": 3,
                "straight": "Between Turns 11 and 12",
                "after_corner": 11,
                "before_corner": 12,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced in the F1 25 2026 Season Pack."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Turn 17. Pit exit rejoins before Turn 1."
        },
    },

    "baku": {
        "name": "Baku City Circuit",
        "location": "Baku",
        "country": "Azerbaijan",
        "high_speed_circuit": True,
        "street_circuit": True,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "medium",
        "elevation_change_m": 29.0,
        "notes": "Unique street circuit combining the narrow medieval Old City section with one of the longest full-throttle straights in Formula One. Low tyre degradation but high risk of incidents and Safety Cars.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the pit straight. Primary overtaking opportunity."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed is important onto the uphill straight."
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after the first DRS zone."
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "slow_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "slow_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Entry to the technical Old City section."
            },
            {
                "corner_number": 8,
                "name": "Turn 8 - Castle",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Extremely narrow uphill left-hander beside the medieval castle walls."
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 15,
                "name": "Turn 15",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 16,
                "name": "Turn 16",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 17,
                "name": "Turn 17",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 18,
                "name": "Turn 18",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 19,
                "name": "Turn 19",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed is critical onto the 2.2 km main straight."
            },
            {
                "corner_number": 20,
                "name": "Turn 20",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "2.2 km main straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 19,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 16."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 2 and 3",
                "after_corner": 2,
                "before_corner": 3,
                "available_in": [2025, 2026],
                "notes": "Short uphill straight after Turn 2."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Turn 16. Pit exit rejoins before Turn 1."
        },
    },

    "zandvoort": {
        "name": "Circuit Zandvoort",
        "location": "Zandvoort",
        "country": "Netherlands",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "hard",
        "elevation_change_m": 8.0,
        "notes": "Fast, flowing seaside circuit featuring dramatic banking, narrow racing lines, and limited overtaking opportunities. Precision and confidence through the high-speed corners are essential.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1 - Tarzanbocht",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the pit straight. Best overtaking opportunity on the circuit."
            },
            {
                "corner_number": 2,
                "name": "Turn 2 - Gerlachbocht",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast uphill left."
            },
            {
                "corner_number": 3,
                "name": "Turn 3 - Hugenholtzbocht",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Steeply banked hairpin."
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast commitment corner."
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 7,
                "name": "Turn 7 - Scheivlak",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "One of the fastest and most demanding corners on the calendar."
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast sweeping left."
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 14,
                "name": "Turn 14 - Arie Luyendykbocht",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Highly banked final corner. Exit speed is critical onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 14,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Arie Luyendykbocht."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 10 and 11",
                "after_corner": 10,
                "before_corner": 11,
                "available_in": [2026],
                "notes": "Additional Straight Mode zone introduced in the F1 25 2026 Season Pack."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry before Turn 14. Pit exit rejoins before Turn 1."
        },
    },
## FIX IMOLA SO IT ONLY RUNS 2025
    "imola": {
        "name": "Autodromo Internazionale Enzo e Dino Ferrari",
        "location": "Imola",
        "country": "Italy",
        "high_speed_circuit": False,
        "street_circuit": False,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "hard",
        "elevation_change_m": 30.0,
        "notes": "Historic anti-clockwise circuit featuring numerous chicanes, elevation changes and narrow racing lines. Overtaking is difficult outside the main braking zones, making qualifying especially important.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 2,
                "name": "Turn 2 - Tamburello",
                "type": "fast_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking into the opening chicane. Primary overtaking opportunity."
            },
            {
                "corner_number": 3,
                "name": "Turn 3 - Tamburello",
                "type": "fast_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Second part of the Tamburello chicane."
            },
            {
                "corner_number": 4,
                "name": "Turn 4 - Tamburello",
                "type": "fast_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit speed is crucial onto the Villeneuve straight."
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "fast_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast change of direction."
            },
            {
                "corner_number": 6,
                "name": "Turn 6 - Villeneuve",
                "type": "fast_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Exit towards Tosa."
            },
            {
                "corner_number": 7,
                "name": "Turn 7 - Tosa",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Tight uphill hairpin and one of the best overtaking opportunities."
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Fast downhill left requiring commitment."
            },
            {
                "corner_number": 9,
                "name": "Turn 9 - Piratella",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Downhill braking into the first part of Acque Minerali."
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Uphill exit."
            },
            {
                "corner_number": 11,
                "name": "Turn 11 - Acque Minerali",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Uphill exit."
            },
            {
                "corner_number": 12,
                "name": "Turn 12 - Acque Minerali",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Uphill exit."
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 14,
                "name": "Turn 14 - Gresini",
                "type": "slow_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Aggressive kerb usage required."
            },
            {
                "corner_number": 15,
                "name": "Turn 15 - Gresini",
                "type": "slow_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": "Completes the chicane."
            },
            {
                "corner_number": 16,
                "name": "Turn 16",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 17,
                "name": "Turn 17",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 18,
                "name": "Turn 18 - Rivazza",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Late braking opportunity."
            },
            {
                "corner_number": 19,
                "name": "Turn 19 - Rivazza",
                "type": "long_radius",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is critical onto the pit straight."
            },
            {
                "corner_number": 20,
                "name": "Turn 20",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 21,
                "name": "Turn 21",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 19,
                "before_corner": 2,
                "available_in": [2025, 2026],
                "notes": "Activation after Rivazza."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Rivazza. Pit exit rejoins before Tamburello."
        },
    },

    "jeddah": {
        "name": "Jeddah Corniche Circuit",
        "location": "Jeddah",
        "country": "Saudi Arabia",
        "high_speed_circuit": True,
        "street_circuit": True,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "medium",
        "elevation_change_m": 12.0,
        "notes": "Ultra-fast street circuit with long full-throttle sections, sweeping high-speed corners and close concrete walls. One of the quickest street circuits ever built, demanding precision and confidence.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking into the opening corner."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit onto the first DRS straight."
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Beginning of the high-speed esses."
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "long_radius",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Banked left-hander leading onto the back straight."
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 15,
                "name": "Turn 15",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 16,
                "name": "Turn 16",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after":False,
                "notes": ""
            },
            {
                "corner_number": 17,
                "name": "Turn 17",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 18,
                "name": "Turn 18",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 19,
                "name": "Turn 19",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 20,
                "name": "Turn 20",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 21,
                "name": "Turn 21",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 22,
                "name": "Turn 22",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 23,
                "name": "Turn 23",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 24,
                "name": "Turn 24",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 25,
                "name": "Turn 25",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 26,
                "name": "Turn 26",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final hairpin. Exit speed is critical onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 27,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 26."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 19 and 22",
                "after_corner": 19,
                "before_corner": 22,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 19."
            },
            {
                "zone_number": 3,
                "straight": "Between Turns 24 and 27",
                "after_corner": 24,
                "before_corner": 27,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 24."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Turn 26. Pit exit rejoins before Turn 1."
        },
    },

    "miami": {
        "name": "Miami International Autodrome",
        "location": "Miami",
        "country": "United States",
        "high_speed_circuit": True,
        "street_circuit": True,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "medium",
        "elevation_change_m": 4.5,
        "notes": "Temporary circuit around Hard Rock Stadium featuring long straights, a very technical middle sector and several heavy braking zones. Overtaking is concentrated into Turns 1, 11 and 17.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the pit straight. Primary overtaking opportunity."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit onto the back straight."
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after the back straight."
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "slow_chicane",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 15,
                "name": "Turn 15",
                "type": "slow_chicane",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 16,
                "name": "Turn 16",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit onto the long pit straight."
            },
            {
                "corner_number": 17,
                "name": "Turn 17",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking into the final sector."
            },
            {
                "corner_number": 18,
                "name": "Turn 18",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 19,
                "name": "Turn 19",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is crucial onto the pit straight."
            },
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 19,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 19."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 8 and 11",
                "after_corner": 9,
                "before_corner": 11,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 8."
            },
            {
                "zone_number": 3,
                "straight": "Between Turns 16 and 17",
                "after_corner": 16,
                "before_corner": 17,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 16."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Turn 19. Pit exit rejoins before Turn 1."
        },
    },

    "las_vegas": {
        "name": "Las Vegas Strip Circuit",
        "location": "Las Vegas",
        "country": "United States",
        "high_speed_circuit": True,
        "street_circuit": True,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "easy",
        "elevation_change_m": 12.0,
        "notes": "Ultra-high-speed street circuit featuring the iconic Las Vegas Strip. Long full-throttle sections, heavy braking zones and low tyre degradation make overtaking relatively straightforward.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the pit straight."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit onto the long Strip straight."
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the Las Vegas Strip."
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "Heavy braking hairpin leading onto the straight."
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 15,
                "name": "Turn 15",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 16,
                "name": "Turn 14",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },  
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Las Vegas Strip",
                "after_corner": 4,
                "before_corner": 5,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 4."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 13 and 14",
                "after_corner": 13,
                "before_corner": 14,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 12."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Turn 14. Pit exit rejoins before Turn 1."
        },
    },

    "lusail": {
        "name": "Lusail International Circuit",
        "location": "Lusail",
        "country": "Qatar",
        "high_speed_circuit": True,
        "street_circuit": False,
        "tyre_degradation_high": True,
        "overtaking_difficulty": "medium",
        "elevation_change_m": 6.0,
        "notes": "Fast permanent circuit with flowing medium and high-speed corners. Tyre degradation is among the highest on the calendar due to sustained lateral loads, with overtaking focused into Turns 1, 6 and 10.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the pit straight. Primary overtaking opportunity."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit onto the first DRS straight."
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Carries speed onto the second DRS straight."
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking after the second DRS zone."
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit onto the back straight."
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Best overtaking opportunity in Sector 3."
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 15,
                "name": "Turn 15",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 16,
                "name": "Turn 16",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is crucial onto the pit straight."
            }
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 16,
                "before_corner": 1,
                "available_in": [2025, 2026],
                "notes": "Activation after Turn 16."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Turn 16. Pit exit rejoins before Turn 1."
        },
    },
}

if date.today() >= MADRID_REFERENCE_DATE:
    MANUAL_METADATA["madrid"] = {
        "name": "Madring",
        "location": "Madrid",
        "country": "Spain",
        "high_speed_circuit": True,
        "street_circuit": True,
        "tyre_degradation_high": False,
        "overtaking_difficulty": "medium",
        "elevation_change_m": 45.0,
        "notes": "Hybrid street circuit around IFEMA Madrid combining fast public roads with a technical permanent section. Significant elevation changes, several heavy braking zones and a long banked corner create a varied challenge.",

        "corners": [
            {
                "corner_number": 1,
                "name": "Turn 1",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the pit straight."
            },
            {
                "corner_number": 2,
                "name": "Turn 2",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 3,
                "name": "Turn 3",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 4,
                "name": "Turn 4",
                "type": "hairpin",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "Hairpin leading onto the first long straight."
            },
            {
                "corner_number": 5,
                "name": "Turn 5",
                "type": "high_speed_sweep",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 6,
                "name": "Turn 6",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 7,
                "name": "Turn 7",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 8,
                "name": "Turn 8",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 9,
                "name": "Turn 9",
                "type": "hairpin",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": True,
                "notes": "Slowest corner on the circuit."
            },
            {
                "corner_number": 10,
                "name": "Turn 10",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 11,
                "name": "Turn 11",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 12,
                "name": "Turn 12",
                "type": "high_speed_sweep",
                "direction": "left",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Beginning of the fast banked section."
            },
            {
                "corner_number": 13,
                "name": "Turn 13",
                "type": "long_radius",
                "direction": "right",
                "tyre_sensitive": True,
                "overtaking": False,
                "drs_after": False,
                "notes": "Long banked right-hander inspired by Zandvoort. Sustained lateral load."
            },
            {
                "corner_number": 14,
                "name": "Turn 14",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 15,
                "name": "Turn 15",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 16,
                "name": "Turn 16",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Exit onto the final straight."
            },
            {
                "corner_number": 17,
                "name": "Turn 17",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": True,
                "drs_after": False,
                "notes": "Heavy braking at the end of the final straight."
            },
            {
                "corner_number": 18,
                "name": "Turn 18",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 19,
                "name": "Turn 19",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 20,
                "name": "Turn 20",
                "type": "medium_radius",
                "direction": "left",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": False,
                "notes": ""
            },
            {
                "corner_number": 21,
                "name": "Turn 21",
                "type": "medium_radius",
                "direction": "right",
                "tyre_sensitive": False,
                "overtaking": False,
                "drs_after": True,
                "notes": "Final corner. Exit speed is critical onto the pit straight."
            }
        ],

        "drs_zones": [
            {
                "zone_number": 1,
                "straight": "Pit Straight",
                "after_corner": 22,
                "before_corner": 1,
                "available_in": [2026],
                "notes": "Activation after Turn 21."
            },
            {
                "zone_number": 2,
                "straight": "Between Turns 3 and 4",
                "after_corner": 3,
                "before_corner": 4,
                "available_in": [2026],
                "notes": "Longest straight on the circuit."
            },
        ],

        "pit": {
            "speed_limit_kph": 80,
            "notes": "Pit entry after Turn 21. Pit exit rejoins before Turn 1."
        },
    }

import dataclasses
from collections import Counter
from typing import Sequence

PREFERRED_YEARS = [2026, 2025, 2024, 2023]
EVENT_MUST_CONTAIN = {"imola": ("imola", "emilia"),
                      "jeddah": ("jeddah", "saudi arabia")}
YEARS_OVERRIDE = {"imola": [2025, 2024, 2022, 2021],
                  "jeddah": [2025, 2024, 2023, 2022]}

GRID_SPACING_M = 2.0

## Braking/Lift
MIN_BRAKING_ZONE_M = 10
MAX_BRAKE_SEARCH_M = 250.0
BRAKE_ON_THRESH = 0.5
BRAKE_GAP_TOLERANCE_M = 6.0
BRAKE_ASSOC_MAX_M = 80.0
LIFT_SEARCH_M = 150.0
LIFT_ASSOC_MAX_M = 40.0
THROTTLE_LIFT_THRESH = 0.85
THROTTLE_LIFT_MIN_M = 10.0
THROTTLE_RETURN_THRESH = 0.80
MAX_EXIT_SEARCH_M = 150.0

## Curvature
POSITION_SMOOTH_M = 40.0
HEADING_SMOOTH_M = 24.0
CURVATURE_SMOOTH_M = 30.0
CURVATURE_MIN = 0.0012
SEGMENT_MERGE_GAP_M = 20.0
MIN_HEADING_CHANGE_DEG = 18.0
MIN_CORNER_LENGTH_M = 20.0
APEX_SPEED_WINDOW_PAD_M = 10.0

## Cross-Lap Merge
CROSS_LAP_MATCH_M = 30.0
STRONG_CORNER_DEG = 20.0
MAX_APEX_GAP_M = 800.0
HEADING_SANITY_TOL_DEG = 40.0

## Direction calibration
FORCE_CURVATURE_SIGN: Optional[int] = None
CAL_MARGIN = 3.0
ANCHOR_TOL_M = 60.0
LATERAL_G_WARN = 6.0

OVERRIDE_DIR = Path(__file__).resolve().parent / "corner_overrides"

## Pit lane and DRS
PIT_MAX_OFFSET_M = 80.0
PIT_MATCH_WINDOW_S = 2.0
PIT_SPREAD_WARN_M  = 100.0
DRS_MIN_LENGTH_M = 20.0
DRS_MAX_LENGTH_M = 1800.0
DRS_OPEN_MIN = 10
DRS_ELIGIBLE_VALUES = (8,)
DRS_NUM_LAPS = 8
DRS_FLICKER_GAP_M = 40.0
DRS_CLUSTER_GAP_M = 250.0
DRS_MIN_LAP_FRACTION = 0.5
DRS_ASSIGN_MAX_M = 600.0
DRS_DETECT_LOOKBACK_M = 1500.0
PIT_PATH_MAX_S = 900.0
PIT_PATH_MIN_POINTS = 15
PIT_PATH_MIN_STEP_M = 1.0
DRS_NO_DETECTION_SEASONS = (2026,)
PIT_WALK_MAX_S = 60

@dataclasses.dataclass
class LapProfile:
    dist: np.ndarray
    speed: np.ndarray
    brake: np.ndarray
    throttle: np.ndarray
    x: np.ndarray
    y: np.ndarray
    heading: np.ndarray
    curvature: np.ndarray

def load_fastf1_session(location: str, slug: Optional[str] = None):
    import fastf1
    fastf1.Cache.enable_cache("sessions/fastf1_cache")
    years = YEARS_OVERRIDE.get(slug, PREFERRED_YEARS)
    needles = EVENT_MUST_CONTAIN.get(slug)
    last_error = None
    for year in years:
        try:
            logger.info(f"Trying FastF1: {year} {location} Q")
            session = fastf1.get_session(year, location, "Q")
            if needles:
                event = session.event
                haystack = " ".join(str(event.get(k, "")) for k in ("Location", "EventName", "OfficialEventName", "Country")).lower()
                if not any(n in haystack for n in needles):
                    raise RuntimeError(f"FastF1 returned '{event.get('EventName')}' ({event.get('Location')}) for {slug}")
            session.load(
                telemetry=True,
                laps=True,
                weather=False,
                messages=False,
            )
            if len(session.laps) == 0:
                raise RuntimeError("No lap data")
            logger.info(f"Using {year} data for {location}")
            return session, year
        except Exception as e:
            last_error = e
            logger.info(f"{year} unavailable for {location}")
    raise RuntimeError(f"No FastF1 data available for {location}: {last_error}")

def _get_lap_telemetry(lap):
    try:
        car = lap.get_car_data(pad=1, pad_side="both")
        pos = lap.get_pos_data(pad=1, pad_side="both")
        tel = car.merge_channels(pos)
        tel = tel.slice_by_lap(lap, interpolate_edges=True).add_distance()
        return tel
    except Exception as e:
        logger.debug(f"Direct car+pos merge failed ({e}), using get_telemetry()")
        tel = lap.get_telemetry()
        if "Distance" not in tel.columns:
            tel = tel.add_distance()
        return tel

def _moving_average(arr: np.ndarray, window_m: float) -> np.ndarray:
    w = max(1, int(round(window_m/GRID_SPACING_M)))
    if w <= 1:
        return arr.copy()
    left = w//2
    right = w - 1 - left
    padded = np.pad(arr, (left, right), mode = "edge")
    return np.convolve(padded, np.ones(w) / w, mode = "valid")

def _build_profile(tel) -> Optional[LapProfile]:
    if len(tel) == 0:
        return None
    for needed in ("Distance", "Speed", "X", "Y"):
        if needed not in tel.columns:
            logger.warning(f"Telemetry has no '{needed}' channel (position data missing?)")
            return None

    def column(name: str, default: float) -> np.ndarray:
        if name in tel.columns:
            return tel[name].to_numpy(dtype=float)
        return np.full(len(tel), default, dtype=float)

    dist_raw = column("Distance", np.nan)
    speed_raw = column("Speed", np.nan)
    x_raw = column("X", np.nan) / 10.0
    y_raw = column("Y", np.nan) / 10.0
    brake_raw = np.nan_to_num(column("Brake", 0.0), nan=0.0)
    throttle_raw = np.nan_to_num(column("Throttle", 100.0), nan=100.0)

    if brake_raw.max() > 1.0:
        brake_raw = brake_raw / 100.0
    if throttle_raw.max() > 1.0:
        throttle_raw = throttle_raw / 100.0

    valid = (
        np.isfinite(dist_raw) & np.isfinite(speed_raw) & np.isfinite(x_raw) & np.isfinite(y_raw) & ~((x_raw==0)&(y_raw==0))
    )
    dist_raw, speed_raw, x_raw, y_raw, brake_raw, throttle_raw = [
        a[valid] for a in (dist_raw, speed_raw, x_raw, y_raw, brake_raw, throttle_raw)
    ]
    if len(dist_raw) < 50:
        return None

    keep = np.concatenate(([True], np.diff(dist_raw) > 0))
    dist_raw, speed_raw, x_raw, y_raw, brake_raw, throttle_raw = [
        a[keep] for a in (dist_raw, speed_raw, x_raw, y_raw, brake_raw, throttle_raw)
    ]

    dist = np.arange(dist_raw[0], dist_raw[-1], GRID_SPACING_M)
    speed = np.interp(dist, dist_raw, speed_raw)
    brake = np.interp(dist, dist_raw, brake_raw)
    throttle = np.interp(dist, dist_raw, throttle_raw)

    x = _moving_average(np.interp(dist, dist_raw, x_raw), POSITION_SMOOTH_M)
    y = _moving_average(np.interp(dist, dist_raw, y_raw), POSITION_SMOOTH_M)

    dx = np.gradient(x, GRID_SPACING_M)
    dy = np.gradient(y, GRID_SPACING_M)
    heading = np.unwrap(np.arctan2(dy, dx))
    heading_smooth = _moving_average(heading, HEADING_SMOOTH_M)
    curvature = _moving_average(np.gradient(heading_smooth, GRID_SPACING_M), CURVATURE_SMOOTH_M)

    return LapProfile(dist, speed, brake, throttle, x, y, heading, curvature)

def _total_heading_deg(profile: LapProfile) -> float:
    return float(np.degrees(profile.heading[-1] - profile.heading[0]))

def _find_curvature_segments(profile: LapProfile) -> List[Tuple[int, int, int, float]]:
    k = profile.curvature
    n = len(k)
    raw_sign = np.where(np.abs(k) >= CURVATURE_MIN, np.sign(k), 0.0).astype(int)

    runs: List[List[int]] = []
    i = 0
    while i < n:
        s = int(raw_sign[i])
        if s == 0:
            i += 1
            continue
        j = i
        while j + 1 < n and raw_sign[j + 1] == s:
            j += 1
        runs.append([i, j, s])
        i = j + 1

    gap = max(1, int(round(SEGMENT_MERGE_GAP_M / GRID_SPACING_M)))
    merged: List[List[int]] = []
    for run in runs: 
        if merged and merged[-1][2] == run[2] and run[0] - merged[-1][1] <= gap:
            merged[-1][1] = run[1]
        else:
            merged.append(run)

    segments = []
    for start, end, s, in merged:
        heading_deg = float(np.degrees(abs(np.sum(k[start:end + 1]) * GRID_SPACING_M)))
        length_m = (end - start + 1) * GRID_SPACING_M
        if heading_deg >= MIN_HEADING_CHANGE_DEG and length_m >= MIN_CORNER_LENGTH_M:
            segments.append((start, end, s, heading_deg))
    return segments

def _analyse_braking(profile: LapProfile, min_idx: int, prev_min_idx: Optional[int]) -> dict:
    dist, brake, throttle = profile.dist, profile.brake, profile.throttle
    n = len(dist)
    upper = min(n - 1, min_idx + 2)
    lower = max(0, min_idx - int(MAX_BRAKE_SEARCH_M / GRID_SPACING_M))
    end_idx = None
    for i in range(upper, lower -1, -1):
        if brake[i] >= BRAKE_ON_THRESH:
            end_idx = i
            break

    if end_idx is not None:
        gap_m = (min_idx - end_idx) * GRID_SPACING_M
        linked = prev_min_idx is None or end_idx > prev_min_idx
        if gap_m <= BRAKE_ASSOC_MAX_M and linked:
            tol = int(round(BRAKE_GAP_TOLERANCE_M / GRID_SPACING_M))
            start_idx = end_idx
            misses = 0
            i = end_idx
            while i > lower:
                i -= 1
                if brake[i] >= BRAKE_ON_THRESH:
                    start_idx = i
                    misses = 0
                else:
                    misses += 1
                    if misses > tol:
                        break
            zone = float(dist[min_idx] - dist[start_idx])
            if zone >= MIN_BRAKING_ZONE_M:
                shared = prev_min_idx is not None and start_idx < prev_min_idx
                return{
                    "brake_type": "brake",
                    "distance_brake_m": float(dist[start_idx]),
                    "reference_braking_zone_m": zone,
                    "shared_braking": shared,
                }

    lift_lower = max(0, min_idx - int(LIFT_SEARCH_M / GRID_SPACING_M))
    lift_end = None
    for i in range(upper, lift_lower -1, -1):
        if throttle[i] < THROTTLE_LIFT_THRESH:
            lift_end = i
            break

    if lift_end is not None:
        gap_m = (min_idx - lift_end) * GRID_SPACING_M
        linked = prev_min_idx is None or lift_end > prev_min_idx
        if gap_m <= LIFT_ASSOC_MAX_M and linked:
            lift_start = lift_end
            while lift_start > lift_lower and throttle[lift_start - 1] < THROTTLE_LIFT_THRESH:
                lift_start -= 1
            lift_len = (lift_end - lift_start + 1) * GRID_SPACING_M
            if lift_len >= THROTTLE_LIFT_MIN_M:
                return{
                    "brake_type": "lift",
                    "distance_brake_m": float(dist[lift_start]),
                    "reference_braking_zone_m": None,
                    "shared_braking": prev_min_idx is not None and lift_start < prev_min_idx,
                }
    return{
        "brake_type": "flat",
        "distance_brake_m": None,
        "reference_braking_zone_m": None,
        "shared_braking": False,
    }

def _find_exit_point(profile: LapProfile, min_idx: int, seg_end_idx: int, brake_type: str) -> float:
    dist, throttle = profile.dist, profile.throttle
    n = len(dist)
    if brake_type == "flat":
        return float(dist[seg_end_idx])
    max_search = min(n, min_idx + int(MAX_EXIT_SEARCH_M / GRID_SPACING_M))
    sustained = 0
    for i in range(min_idx, max_search):
        if throttle[i] >= THROTTLE_RETURN_THRESH:
            sustained += 1
            if sustained >= 3:
                return float(dist[max(min_idx, i - 2)])
        else:
            sustained = 0
    return float(dist[min(max(seg_end_idx, min_idx), n - 1)])

def _build_corner(
        profile: LapProfile,
        seg: Tuple[int, int, int, float],
        lo: int,
        hi: int,
        prev_min_idx: Optional[int],
) -> Tuple[dict, int]:
    start, end, sign, heading_deg = seg
    pad = max(1, int(round(APEX_SPEED_WINDOW_PAD_M / GRID_SPACING_M)))
    w0 = max(lo, start - pad)
    w1 = min(hi, end + pad)
    min_idx = w0 + int(np.argmin(profile.speed[w0:w1 + 1]))

    k_abs = np.abs(profile.curvature[start:end + 1])
    apex_idx = start + int(np.argmax(k_abs))
    peak_k = float(k_abs.max())

    braking = _analyse_braking(profile, min_idx, prev_min_idx)
    exit_dist = max(
        _find_exit_point(profile, min_idx, end, braking["brake_type"]),
        float(profile.dist[apex_idx]),
    )
    apex_speed_geom_kph = float(profile.speed[apex_idx])
    lateral_g = (apex_speed_geom_kph / 3.6) ** 2 * peak_k / 9.81

    corner = {
        "curv_sign": int(sign),
        "distance_start_m": round(float(profile.dist[start]), 1),
        "distance_apex_m": round(float(profile.dist[apex_idx]), 1),
        "distance_end_m": round(float(profile.dist[end]), 1),
        "distance_exit_m": round(exit_dist, 1),
        "reference_apex_speed_kph": round(float(profile.speed[min_idx]), 1),
        "brake_type": braking["brake_type"],
        "distance_brake_m": None if braking["distance_brake_m"] is None else round(braking["distance_brake_m"], 1),
        "reference_braking_zone_m": None if braking["reference_braking_zone_m"] is None else round(braking["reference_braking_zone_m"], 1),
        "shared_braking": bool(braking["shared_braking"]),
        "heading_change_deg": round(heading_deg, 1),
        "radius_m": round(1.0 / peak_k, 1),
        "estimated_lateral_g": round(lateral_g, 2),
    }
    return corner, min_idx

def _extract_corners_from_lap(profile: LapProfile) -> List[dict]:
    segments = _find_curvature_segments(profile)
    logger.info(f"Curvature segments (corners) found: {len(segments)}")
    n = len(profile.dist)

    corners: List[dict] = []
    prev_min_idx: Optional[int] = None
    for i, seg in enumerate(segments):
        lo = segments[i - 1][1] + 1 if i > 0 else 0
        hi = segments[i + 1][0] - 1 if i < len(segments) - 1 else n - 1
        corner, min_idx = _build_corner(profile, seg, lo, hi, prev_min_idx)
        corners.append(corner)
        prev_min_idx = min_idx
        logger.debug(
            f"Corner {i + 1}: apex {corner['distance_apex_m']}m, "
            f"{corner['heading_change_deg']}deg, {corner['reference_apex_speed_kph']}kph, "
            f"{corner['brake_type']}"
        )
    return corners

def _merge_group(group: List[dict]) -> dict:
    def med(key: str, items: List[dict], nd: int = 1) -> Optional[float]:
        vals = [c[key] for c in items if c.get(key) is not None]
        return round(float(np.median(vals)), nd) if vals else None

    brake_type = Counter(c["brake_type"] for c in group).most_common(1)[0][0]
    same = [c for c in group if c["brake_type"] == brake_type]

    merged = {
        "curv_sign": group[0]["curv_sign"],
        "brake_type": brake_type,
        "shared_braking": sum(1 for c in same if c["shared_braking"]) * 2 > len(same),
    }
    for key in ("distance_start_m", "distance_apex_m", "distance_end_m", "distance_exit_m", "reference_apex_speed_kph", "heading_change_deg", "radius_m"):
        merged[key] = med(key, group)
    merged["estimated_lateral_g"] = med("estimated_lateral_g", group, nd=2)
    for key in ("distance_brake_m", "reference_braking_zone_m"):
        merged[key] = med(key, same)
    return merged

def _merge_corner_sets(corner_sets: List[List[dict]]) -> List[dict]:
    reference = corner_sets[0]
    if len(corner_sets) == 1:
        return reference

    result = []
    for ref in reference:
        group = [ref]
        for other in corner_sets[1:]:
            candidates = [c for c in other if c["curv_sign"] == ref["curv_sign"]]
            if not candidates:
                continue
            best = min(candidates, key=lambda c: abs(c["distance_apex_m"] - ref["distance_apex_m"]))
            if abs(best["distance_apex_m"] - ref["distance_apex_m"]) <= CROSS_LAP_MATCH_M:
                group.append(best)
        result.append(_merge_group(group))
    return result

def extract_corners_from_telemetry(session, num_laps: int = 3) -> Tuple[List[dict], Optional[dict]]:
    corner_sets: List[List[dict]] = []
    geometry: Optional[dict] = None

    laps = session.laps.copy()
    if "Deleted" in laps.columns:
        laps = laps[laps["Deleted"] != True]
    laps = laps.dropna(subset=["LapTime"])
    top_laps = (
        laps.loc[laps.groupby("Driver")["LapTime"].idxmin()]
        .sort_values("LapTime")
        .head(num_laps)
    )
    logger.info(f"Laps considered: {len(laps)}, using {len(top_laps)} fastest per_driver laps")

    for _, lap_row in top_laps.iterrows():
        driver = lap_row["Driver"]
        try:
            tel = _get_lap_telemetry(lap_row)
            profile = _build_profile(tel)
            if profile is None:
                logger.warning(f"{driver}: no usable telemetry/position data, skipping lap")
                continue
            total = _total_heading_deg(profile)
            logger.info(f"{driver}: {len(profile.dist)} grid points, total heading change {total:.0f} deg")
            if abs(abs(total) - 360.0) > HEADING_SANITY_TOL_DEG:
                logger.warning(f"{driver}: total heading change {total:.0f} deg is not close to +/-360 (bad position data?)")

            corners = _extract_corners_from_lap(profile)
            if corners:
                corner_sets.append(corners)
                if geometry is None:
                    geometry = {
                        "dist": profile.dist,
                        "x": profile.x,
                        "y": profile.y,
                        "heading_total_deg": total,
                    }
        except Exception as e:
            logger.warning(f"{driver}: could not extract corners from lap: {e}", exc_info=True)

    if not corner_sets:
        return [], None
    return _merge_corner_sets(corner_sets), geometry

def _direction_of(corner: dict, cal: int) -> str:
    return "left" if corner["curv_sign"] * cal > 0 else "right"

def _align(detected: List[dict], manual: List[dict], cal: int) -> Tuple[float, List[Tuple[int, int]]]:
    n, m = len(detected), len(manual)
    def strength(c: dict) -> float:
        return min(c["heading_change_deg"] / 30.0, 1.0)

    def skip_det(i: int) -> float:
        return -0.1 - 0.6 * strength(detected[i])

    def skip_meta(j: int) -> float:
        return -0.2 if manual[j].get("flat_out") else -1.5

    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    bt: List[List[Optional[str]]] = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + skip_det(i - 1)
        bt[i][0] = "det"
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + skip_meta(j - 1)
        bt[0][j] = "meta"

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            best = dp[i - 1][j] + skip_det(i - 1)
            move = "det"
            s = dp[i][j - 1] + skip_meta(j - 1)
            if s > best:
                best, move = s, "meta"
            meta_dir = manual[j - 1].get("direction")
            if meta_dir is None or meta_dir == _direction_of(detected[i - 1], cal):
                s = dp[i - 1][j - 1] + 2.0 + 2.0 * strength(detected[i - 1])
                if s > best:
                    best, move = s, "match"
            dp[i][j] = best
            bt[i][j] = move

    pairs: List[Tuple[int, int]] = []
    i, j = n, m
    while i > 0 or j > 0:
        move = bt[i][j]
        if move == "match":
            pairs.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif move == "det":
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    return dp[n][m], pairs

def _combine_detections(group: List[dict]) -> dict:
    if len(group) == 1:
        return group[0]
    lead = max(group, key=lambda c: c["heading_change_deg"])
    first, last = group[0], group[-1]
    merged = dict(lead)
    merged["distance_start_m"] = first["distance_start_m"]
    merged["distance_end_m"] = last["distance_end_m"]
    merged["distance_exit_m"] = last["distance_exit_m"]
    merged["reference_apex_speed_kph"] = min(c["reference_apex_speed_kph"] for c in group)
    merged["heading_change_deg"] = round(sum(c["heading_change_deg"] for c in group if c["curv_sign"] == lead["curv_sign"]), 1)
    merged["radius_m"] = min(c["radius_m"] for c in group)
    merged["estimated_lateral_g"] = max(c["estimated_lateral_g"] for c in group)
    for key in ("brake_type", "distance_brake_m", "reference_braking_zone_m", "shared_braking"):
        merged[key] = first[key]
    merged["merged_from"] = len(group)
    merged["member_apex_m"] = [c["distance_apex_m"] for c in group]
    return merged

def _apply_hints(detected: List[dict], manual: List[dict]) -> Tuple[List[dict], Dict[int, int], List[str]]:
    notes: List[str] = []
    used: set = set()
    groups: Dict[int, List[int]] = {}
    for j, m in enumerate(manual):
        hint = m.get("apex_m")
        if hint is None:
            continue
        label = f"T{m.get('corner_number', j + 1)}"
        hints = list(hint) if isinstance(hint, (list, tuple)) else [hint]
        picked: List[int] = []
        for h in hints:
            candidates = [(abs(c["distance_apex_m"] - h), idx) for idx, c in enumerate(detected) if idx not in used]
            if candidates and min(candidates)[0] <= ANCHOR_TOL_M:
                idx = min(candidates)[1]
                picked.append(idx)
                used.add(idx)
            else:
                notes.append(f"{label}: no detection within {ANCHOR_TOL_M:.0f} m of apex_m={h}")
        if picked:
            groups[j] = sorted(picked)

    items = [(c["distance_apex_m"], c, None) for idx, c in enumerate(detected) if idx not in used]
    for j, idxs in groups.items():
        combined = _combine_detections([detected[i] for i in idxs])
        items.append((combined["distance_apex_m"], combined, j))
    items.sort(key=lambda t: t[0])

    new_detected = [t[1] for t in items]
    pins: Dict[int, int] = {}
    last_det = -1
    for j in sorted(j for _, _, j in items if j is not None):
        det_idx = next(i for i, t in enumerate(items) if t[2] == j)
        if det_idx <= last_det:
            notes.append(f"T{manual[j].get('corner_number', j + 1)}: apex_m is out of order with the other hints - hint ignored")
            continue
        pins[j] = det_idx
        last_det = det_idx
    return new_detected, pins, notes

def _align_with_pins(detected: List[dict], manual: List[dict], cal: int, pins: Dict[int, int]) -> List[Tuple[int, int]]:
    pairs: List[Tuple[int, int]] = []
    prev_m, prev_d = 0, 0
    for m_idx in sorted(pins):
        d_idx = pins[m_idx]
        _, sub = _align(detected[prev_d:d_idx], manual[prev_m:m_idx], cal)
        pairs += [(prev_d + d, prev_m + m) for d, m in sub]
        pairs.append((d_idx, m_idx))
        prev_m, prev_d = m_idx + 1, d_idx + 1
    _, sub = _align(detected[prev_d:], manual[prev_m:], cal)
    pairs += [(prev_d + d, prev_m + m) for d, m in sub]
    return pairs

def _match_to_metadata(detected: List[dict], manual: List[dict], ignore_m: Sequence[float] = (), complete: bool = False,) -> Tuple[List[dict], List[dict], int, List[Tuple[int, Optional[int]]], List[str]]:
    def is_ignored(c: dict) -> bool:
        return any(abs(c["distance_apex_m"] - g) <= ANCHOR_TOL_M for g in ignore_m)

    kept = [c for c in detected if not is_ignored(c)]
    ignored = [c for c in detected if is_ignored(c)]
    notes: List[str] = []

    if not manual:
        return kept, ignored, 1, [(i, None) for i in range(len(kept))], notes

    if FORCE_CURVATURE_SIGN in (1, -1):
        cal = int(FORCE_CURVATURE_SIGN)
        logger.info(f"Curvature sign forced to {cal}")
    else:
        score_pos, _ = _align(kept, manual, +1)
        score_neg, _ = _align(kept, manual, -1)
        logger.info(f"Direction alignment score: sign +1 = {score_pos:.1f}, sign -1 = {score_neg:.1f}")
        if score_neg > score_pos + CAL_MARGIN:
            cal = -1
            logger.info("X/Y data appears mirrored for this track; using flipped curvature sign")
        else:
            cal = 1
            if abs(score_neg - score_pos) <= CAL_MARGIN:
                notes.append("Direction calibration is ambiguous (alternating corners score the same both ways); "
                             "assuming unmirrored X/Y - check the PNG orientation against the official map "
                             "(set FORCE_CURVATURE_SIGN if it is mirrored)")

    detected2, pins, hint_notes = _apply_hints(kept, manual)
    notes += hint_notes
    if complete:
        pairs = [(d, m) for m, d in sorted(pins.items())]
    else:
        pairs = _align_with_pins(detected2, manual, cal, pins)
    return detected2, ignored, cal, pairs, notes

def _log_detection_table(detected: List[dict], pairs: List[Tuple[int, Optional[int]]], manual: List[dict], cal: int) -> None:
    label = {d: manual[m].get("corner_number", m + 1) for d, m in pairs if m is not None}
    logger.info("Detected corners (use the apex distances for apex_m / ignore_apex_m hints):")
    for i, c in enumerate(detected):
        tag = f"T{label[i]}" if i in label else "?"
        extra = f" (merged from {c['merged_from']})" if c.get("merged_from") else ""
        logger.info(
            f" {tag:>4} apex {c['distance_apex_m']:7.0f} m {_direction_of(c, cal):>5} "
            f"{c['heading_change_deg']:5.0f} deg {c['reference_apex_speed_kph']:4.0f} kph {c['brake_type']}{extra}"
        )

def extract_sector_boundaries(session) -> Tuple[float, float]:
    try:
        fastest = session.laps.pick_fastest()
        tel = fastest.get_car_data().add_distance()
        track_length = float(tel["Distance"].max())

        s1_time = fastest["Sector1Time"].total_seconds()
        s2_time = fastest["Sector2Time"].total_seconds()
        s3_time = fastest["Sector3Time"].total_seconds()
        total_time = s1_time + s2_time + s3_time

        if total_time > 0:
            s2_start = track_length * (s1_time / total_time)
            s3_start = track_length * ((s1_time + s2_time) / total_time)
            return round(s2_start, 1), round(s3_start, 1)

    except Exception as e:
        logger.warning(f"Could not extract sector boundaries: {e}")

    try:
        track_length = float(session.laps.pick_fastest().get_car_data().add_distance()["Distance"].max())
        return round(track_length / 3, 1), round(track_length * 2 / 3, 1)
    except Exception:
        return 0.0, 0.0

_warned_dropped_fields: set = set()

def _make_corner_info(**kwargs) -> CornerInfo:
    if dataclasses.is_dataclass(CornerInfo):
        allowed = {f.name for f in dataclasses.fields(CornerInfo)}
        dropped = [k for k in kwargs if k not in allowed]
        for k in dropped:
            if k not in _warned_dropped_fields:
                _warned_dropped_fields.add(k)
                logger.warning(f"CornerInfo has no field '{k}' - not written to JSON. Add it to CornerInfo and track_to_dict().")
        kwargs = {k: v for k, v in kwargs.items() if k in allowed}
    return CornerInfo(**kwargs)

def _override_path(slug: str) -> Path:
    return OVERRIDE_DIR / f"{slug}.json"

def _load_overrides(slug: str) -> Optional[dict]:
    path = _override_path(slug)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "assignments" not in data:
            raise ValueError("missing 'assignments'")
        logger.info(f"Using saved corner review: {path}")
        return data
    except Exception as e:
        logger.warning(f"Could not read {path}: {e} - ignoring it")
        return None

def _json_default(o):
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"{type(o).__name__} is not JSON serialisable")

def _save_overrides(slug: str, data: dict) -> None:
    path = _override_path(slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=_json_default)
    logger.info(f"Saved corner review to {path}")

def _apply_overrides(manual: List[dict], ignore_m: Sequence[float], overrides: Optional[dict]) -> Tuple[List[dict], List[float], bool]:
    if not overrides:
        return manual, list(ignore_m), False

    corners = [{k: v for k, v in m.items() if k != "apex_m"} for m in manual]
    by_number = {m.get("corner_number", i + 1): m for i, m in enumerate(corners)}
    for key, apexes in overrides.get("assignments", {}).items():
        number = int(key)
        if number not in by_number:
            stub = {"corner_number": number}
            corners.append(stub)
            by_number[number] = stub
        by_number[number]["apex_m"] = list(apexes) if len(apexes) > 1 else apexes[0]
    corners.sort(key=lambda m: m.get("corner_number", 0))
    return corners, list(overrides.get("ignore_apex_m", [])), True

def _initial_review_labels(raw: List[dict], detected: List[dict], ignored: List[dict], pairs: List[Tuple[int, Optional[int]]], manual: List[dict]) -> Dict[int, object]:
    by_apex = {c["distance_apex_m"]: i for i, c in enumerate(raw)}
    labels: Dict[int, object] = {i: None for i in range(len(raw))}
    for c in ignored:
        labels[by_apex[c["distance_apex_m"]]] = "x"
    for d, m in pairs:
        if m is None:
            continue
        number = manual[m].get("corner_number", m + 1)
        for apex in detected[d].get("member_apex_m", [detected[d]["distance_apex_m"]]):
            labels[by_apex[apex]] = number
    return labels

class _ReviewSession:
    HELP = ("click a marker | type a number + Enter = assign (same number twice = merge) | x = remove | "
            "\n u = unassign | a = Add missed corner | f = flip added marker direction | <- -> = next marker | r = reset | s = save | q = cancel")
    COLOURS = {"brake": "tab:red", "lift": "tab:orange", "flat": "tab:green"}
    MIN_ADD_SEPARATION_M = 2.0

    def __init__(self, title: str, geometry: dict, detected: List[dict], labels: Dict[int, object],
                 cal: int, expected_numbers: Sequence[int], expected_dirs: Optional[Dict[int, str]] = None):
        self.title = title
        self.detected = [dict(c) for c in detected]
        self.inital_detected = [dict(c) for c in detected]
        self.initial_labels = dict(labels)
        self.labels = dict(labels)
        self.expected = sorted(set(expected_numbers))
        self.cal = cal
        self.expected_dirs = expected_dirs or {}
        self.dist = geometry["dist"]
        self.x = geometry["x"]
        self.y = -geometry["y"] if cal < 0 else geometry["y"]
        self.span = float(max(np.ptp(self.x), np.ptp(self.y)))
        self.add_mode = False
        self.buffer = ""
        self.status = "Click a marker, type its official corner number, press Enter."
        self._rebuild()
        self.sel: Optional[int] = self.order[0] if self.order else None

    def _point_at(self, apex_m: float) -> Tuple[float, float]:
        return float(np.interp(apex_m, self.dist, self.x)), float(np.interp(apex_m, self.dist, self.y))

    def _rebuild(self) -> None:
        self.points = [self._point_at(c["distance_apex_m"]) for c in self.detected]
        self.order = sorted(range(len(self.detected)), key=lambda i: self.detected[i]["distance_apex_m"])

    def _move(self, step: int) -> None:
        if self.sel is None:
            return
        pos = self.order.index(self.sel)
        self.sel = self.order[(pos + step) % len(self.order)]

    def _add_marker(self, apex_m: float) -> None:
        template = self.detected[self.sel]
        if any(abs(c["distance_apex_m"] - apex_m) < self.MIN_ADD_SEPARATION_M for c in self.detected):
            self.status = "a marker already exists there - click a different spot"
            return
        new = {k: v for k, v in template.items() if k not in ("merged_from", "member_apex_m")}
        new["distance_apex_m"] = round(float(apex_m), 1)
        new["distance_start_m"] = new["distance_apex_m"]
        new["distance_end_m"] = new["distance_apex_m"]
        new["distance_exit_m"] = max(float(template["distance_exit_m"]), new["distance_apex_m"])
        new["manual"] = True
        self.detected.append(new)
        idx = len(self.detected) - 1
        self.labels[idx] = None
        self._rebuild()
        self.sel = idx
        self.add_mode = False
        self.status = f"added marker at {new['distance_apex_m']:.0f} m - type its corner number, Enter"

    def _draw_turn_arrow(self, ax, apex_m: float, px: float, py: float, direction:str, colour: str) -> None:
        ahead, behind = self._point_at(apex_m + 10.0), self._point_at(apex_m - 10.0)
        tx, ty = ahead[0] - behind[0], ahead[1] - behind[1]
        norm = float(np.hypot(tx, ty))
        if norm == 0:
            return
        tx, ty = tx / norm, ty / norm
        nx, ny = (-ty, tx) if direction == "left" else (ty, -tx)
        a0, a1 = 0.022 * self.span, 0.08 * self.span
        ax.annotate("", xy=(px + nx * a1, py + ny * a1), xytext=(px + nx * a0, py + ny * a0),
                    arrowprops=dict(arrowstyle="-|>", color=colour, lw=2, shrinkA=0, shrinkB=0), zorder=4)

    def _mismatches(self) -> List[str]:
        out = []
        for i, label in self.labels.items():
            if not isinstance(label, int):
                continue
            want = self.expected_dirs.get(label)
            have = _direction_of(self.detected[i], self.cal)
            if want and want != have:
                note = "" if self.detected[i].get("manual") else " - detected marker, f cannot flip it"
                out.append((label, f"T{label} (metadata {want}, marker {have}{note})"))
        return [text for _, text in sorted(out)]

    def on_key(self, key: Optional[str]) -> Optional[str]:
        if self.add_mode and key in ("a", "escape"):
            self.add_mode = False
            self.status = "add cancelled"
            return None
        if not key or self.sel is None:
            return "cancel" if key in ("q", "escape") else None
        if len(key) == 1 and key.isdigit():
            self.buffer += key
            self.status = f"number: {self.buffer} (Enter to assign)"
        elif key == "backspace":
            self.buffer = self.buffer[:-1]
            self.status = f"number: {self.buffer}"
        elif key in ("enter", "return"):
            if not self.buffer:
                self.status = "type a corner number first"
            else:
                number = int(self.buffer)
                self.buffer = ""
                self.labels[self.sel] = number
                c = self.detected[self.sel]
                want = self.expected_dirs.get(number)
                note = ""
                if want and c.get("manual") and _direction_of(c, self.cal) != want:
                    c["curv_sign"] = -c["curv_sign"]
                    note = f" (direction flipped to {want} to match the metadata)"
                count = sum(1 for v in self.labels.values() if v == number)
                self.status = f"T{number} assigned" + note + (f" - now merges {count} detections" if count > 1 else "")
                self._move(1)
        elif key == "a":
            self.add_mode = True
            self.buffer = ""
            self.status = (f"Add: new marker copies the data of the marker at "
                           f"{self.detected[self.sel]['distance_apex_m']:.0f} m - click the track where the missed apex is (a/Esc cancels)")
        elif key == "f":
            c = self.detected[self.sel]
            if c.get("manual"):
                c["curv_sign"] = -c["curv_sign"]
                self.status = "flipped the direction of the added marker"
            else:
                self.status = "only the added markers can be flipped"
        elif key in ("x", "delete"):
            self.labels[self.sel] = "x"
            self.status = "marker removed (ignored)"
            self._move(1)
        elif key == "u":
            self.labels[self.sel] = None
            self.status = "marker unassigned"
        elif key == "right":
            self._move(1)
        elif key == "left":
            self._move(-1)
        elif key == "r":
            self.detected = [dict(c) for c in self.inital_detected]
            self.labels = dict(self.initial_labels)
            self.add_mode = False
            self._rebuild()
            self.sel = self.order[0] if self.order else None
            self.status = "reset to the automatic result (added markers removed)"
        elif key == "s":
            return "save"
        elif key in ("q", "escape"):
            return "cancel"
        return None

    def on_click(self, ax, x_px: float, y_px: float, radius_px: float = 25.0) -> None:
        if self.add_mode:
            track = ax.transData.transform(np.column_stack([self.x, self.y]))
            d = np.hypot(track[:, 0] - x_px, track[:, 1] - y_px)
            i = int(np.argmin(d))
            if d[i] <= 40.0:
                self._add_marker(float(self.dist[i]))
            else:
                self.status = "click closer to the racing line"
            return
        if not self.points:
            return
        pts = ax.transData.transform(np.array(self.points))
        d = np.hypot(pts[:, 0] - x_px, pts[:, 1] - y_px)
        i = int(np.argmin(d))
        if d[i] <= radius_px:
            self.sel = i
            self.buffer = ""
            self.status = f"selected marker at {self.detected[i]['distance_apex_m']:.0f} m"

    def draw(self, ax) -> None:
        ax.clear()
        ax.plot(self.x, self.y, color="0.45", linewidth=1.8)
        _draw_start_line(ax, self.x, self.y)
        ax.annotate("S/F", (self.x[0], self.y[0]), textcoords="offset points", xytext=(8, 8), fontsize=9)

        for i, c in enumerate(self.detected):
            px, py = self.points[i]
            label = self.labels.get(i)
            direction = _direction_of(c, self.cal)
            if label == "x":
                ax.scatter([px], [py], marker="x", s=70, color="0.5", zorder=3)
            else:
                colour = self.COLOURS.get(c["brake_type"], "tab:blue") if isinstance(label, int) else "0.6"
                ax.scatter([px], [py], s=230, color=colour, zorder=3, marker="s" if c.get("manual") else "o")
                ax.annotate(str(label) if isinstance(label, int) else "?", (px, py), ha="center", va="center", fontsize=9, color="white", zorder=5)
                want = self.expected_dirs.get(label) if isinstance(label, int) else None
                self._draw_turn_arrow(ax, c["distance_apex_m"], px, py, direction, "red" if (want and want != direction) else "black")
            ax.annotate(f"{c['distance_apex_m']:.0f} m", (px, py), textcoords="offset points", xytext=(0, -17), ha="center", fontsize=7, color="0.35")
        if self.sel is not None:
            px, py = self.points[self.sel]
            ax.scatter([px], [py], s=520, facecolors="none", edgecolors="red" if self.add_mode else "black", linewidth=2, zorder=6)

        assigned = {v for v in self.labels.values() if isinstance(v, int)}
        missing = [f"T{n}" for n in self.expected if n not in assigned]
        ax.text(0.01, 0.99, "No marker yet: " + (", ".join(missing) if missing else "none"), transform=ax.transAxes, va="top", fontsize=9)
        bad = self._mismatches()
        if bad:
            ax.text(0.01, 0.955, "Direction differs from metadata: " + "; ".join(bad), transform=ax.transAxes, va="top", fontsize=8, color="red")
        ax.text(0.5, -0.01, self.HELP, transform=ax.transAxes, ha="center", va="top", fontsize=8)
        ax.set_title(f"{self.title}\n{self.status}", fontsize=10)
        ax.set_aspect("equal")
        ax.axis("off")

    def result(self) -> dict:
        assignments: Dict[str, List[float]] = {}
        ignore: List[float] = []
        for i, label in self.labels.items():
            apex = self.detected[i]["distance_apex_m"]
            if isinstance(label, int):
                assignments.setdefault(str(label), []).append(apex)
            elif label == "x":
                ignore.append(apex)
        for key in assignments:
            assignments[key].sort()
        return{
            "version": 1,
            "ignore_apex_m": sorted(ignore),
            "assignments": dict(sorted(assignments.items(), key=lambda kv: int(kv[0]))),
        }

DRS_EDIT_KEYS = ("activation_m", "end_m", "detection_m")

def _drs_edit_path(slug: str) -> Path:
    return OVERRIDE_DIR / f"{slug}_drs.json"

def _load_drs_edits(slug: str) -> Dict[int, dict]:
    path = _drs_edit_path(slug)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        edits: Dict[int, dict] = {}
        for n, vals in data.get("zones", {}).items():
            e = {k: float(v) for k, v in vals.items() if k in DRS_EDIT_KEYS and v is not None}
            if "no_detection" in vals:
                e["no_detection"] = bool(vals["no_detection"])
            edits[int(n)] = e
        logger.info(f"Using saved DRS edits: {path}")
        return edits
    except Exception as e:
        logger.warning(f"Could not read {path}: {e} - ignoring it")
        return {}

def _save_drs_edits(slug: str, edits: Dict[int, dict]) -> None:
    path = _drs_edit_path(slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "zones": {str(n): v for n, v in sorted(edits.items())}}, f, indent=2)
    logger.info(f"Saved DRS edits to {path}")

class _DrsEditSession:
    HELP = ("drag a handle: A = activation, E = end, D = detection | <- -> = select zone | "
            "a / e / d = (re)place activation / end / detection, then click | x = remove detection | X = remove from all zones | "
             "r = reset | s = save | q = cancel")
    GRAB_PX = 16.0
    LABELS = {"activation_m": "activation", "end_m": "end", "detection_m": "detection"}

    def __init__(self, title: str, geometry: dict, cal: int, zones: Sequence, track_length: float):
        self.title = title
        self.dist = geometry["dist"]
        self.x = geometry["x"]
        self.y = -geometry["y"] if cal < 0 else geometry ["y"]
        self.L = track_length if track_length > 0 else float(self.dist[-1])
        self.names = {z.zone_number: z.straight_name for z in zones}
        self.removed: set = set()
        self.values = {
            z.zone_number: {
                "activation_m": z.activation_m or None,
                "end_m": z.end_m or None,
                "detection_m": z.detection_m or None,
            } 
            for z in zones
        }
        self.initial = {n: dict(v) for n, v in self.values.items()}
        self.numbers = sorted(self.values)
        self.sel = self.numbers[0]
        self.drag: Optional[Tuple[int, str]] = None
        self.place_key: Optional[str] = None
        self.status = "Drag a handle to move it. Arrow keys select a zone"

    def _point(self, d: float) -> Tuple[float, float]:
        return float(np.interp(d, self.dist, self.x)), float(np.interp(d, self.dist, self.y))

    def _pieces(self, a: float, b: float) -> List[Tuple[float, float]]:
        if b >= a:
            return [(a, b)]
        return [(a, float(self.dist[-1])), (float(self.dist[0]), b)]

    def _snap(self, ax, x_px: float, y_px: float, max_px: Optional[float]) -> Optional[float]:
        track = ax.transData.transform(np.column_stack([self.x, self.y]))
        d = np.hypot(track[:, 0] - x_px, track[:, 1] - y_px)
        i = int(np.argmin(d))
        if max_px is not None and d[i] > max_px:
            return None
        return float(self.dist[i])

    def _handle_at(self, ax, x_px: float, y_px: float) -> Optional[Tuple[int, str]]:
        best = None
        for n, vals in self.values.items():
            for key in DRS_EDIT_KEYS:
                v = vals[key]
                if v is None:
                    continue
                px, py = ax.transData.transform(self._point(v))
                dpx = float(np.hypot(px - x_px, py - y_px))
                if dpx <= self.GRAB_PX and (best is None or dpx < best[0]):
                    best = (dpx, n, key)
        return None if best is None else (best[1], best[2])

    def on_press(self, ax, x_px: float, y_px: float) -> None:
        if self.place_key:
            d = self._snap(ax, x_px, y_px, 60.0)
            if d is None:
                self.status = "click closer to the racing line"
                return
            self.values[self.sel][self.place_key] = d
            self.removed.discard(self.sel)
            self.status = f"zone {self.sel}: {self.LABELS[self.place_key]} placed at {d:.0f} m"
            self.place_key = None
            return
        hit = self._handle_at(ax, x_px, y_px)
        if hit:
            self.sel, key = hit
            self.drag = hit
            self.status = f"dragging zone {self.sel} {self.LABELS[key]}"

    def on_motion(self, ax, x_px: float, y_px: float) -> None:
        if not self.drag:
            return
        n, key = self.drag
        d = self._snap(ax, x_px, y_px, None)
        if d is not None:
            self.values[n][key] = d
            self.status = f"zone {n} {self.LABELS[key]}: {d:.0f} m"
    
    def on_release(self) -> None:
        if self.drag:
            n, key = self.drag
            self.status = f"zone {n} {self.LABELS[key]} set to {self.values[n][key]:.0f} m"
        self.drag = None
    
    def on_key(self, key: Optional[str]) -> Optional[str]:
        if not key:
            return None
        if key in ("q", "escape"):
            if self.place_key:
                self.place_key = None
                self.status = "placement cancelled"
                return None
            return "cancel"
        if key in ("right", "left"):
            pos = self.numbers.index(self.sel)
            self.sel = self.numbers[(pos + (1 if key == "right" else -1)) % len(self.numbers)]
            self.status = f"selected zone {self.sel}"
        elif key in ("a", "e", "d"):
            self.place_key = {"a": "activation_m", "e": "end_m", "d": "detection_m"}[key]
            self.status = f"zone {self.sel}: click the track to place the {self.LABELS[self.place_key]} point (Esc cancels)"
        elif key == "x":
            self.values[self.sel]["detection_m"] = None
            self.removed.add(self.sel)
            self.status = f"zone {self.sel}: detection removed"
        elif key == "X":
            for n in self.numbers:
                self.values[n]["detection_m"] = None
                self.removed.add(n)
            self.status = "detection removed from all zones"
        elif key == "r":
            self.values = {n: dict(v) for n, v in self.initial.items()}
            self.removed = set()
            self.place_key = None
            self.status = "reset to the values this window opened with"
        elif key == "s":
            return "save"
        return None
    
    def draw(self, ax) -> None:
        ax.clear()
        ax.plot(self.x, self.y, color="0.45", linewidth=1.8)
        _draw_start_line(ax, self.x, self.y)
        ax.annotate("S/F", (self.x[0], self.y[0]), textcoords="offset points", xytext=(8, 8), fontsize=9)

        for n in self.numbers:
            v = self.values[n]
            a, e, d = v["activation_m"], v["end_m"], v["detection_m"]
            selected = n == self.sel
            colour = "tab:blue" if selected else "0.55"
            if a is not None and e is not None:
                for lo, hi in self._pieces(a, e):
                    mask = (self.dist >= lo) & (self.dist <= hi)
                    if int(mask.sum()) > 1:
                        ax.plot(self.x[mask], self.y[mask], color="tab:blue", linewidth=9 if selected else 6,
                        alpha=0.6 if selected else 0.3, solid_capstyle="butt", zorder=2)
            for key, marker, letter in (("activation_m", "o", "A"), ("end_m", "o", "E"), ("detection_m", "o", "D")):
                val = v[key]
                if val is None:
                    continue
                px, py = self._point(val)
                ax.scatter([px], [py], s=260 if marker == "o" else 200, marker=marker, color=colour, edgecolors="white", zorder=5)
                ax.annotate(letter, (px, py), ha="center", va="center", fontsize=8, color="white", zorder=6)
                ax.annotate(f"{val:.0f} m", (px, py), textcoords="offset points", xytext=(0, -17), ha="center", fontsize=7, color="0.35")
            anchor = next((val for val in (a, d, e) if val is not None), None)
            if anchor is not None:
                px, py = self._point(anchor)
                ax.annotate(f"DRS {n}", (px, py), textcoords="offset points", xytext=(12, 12), fontsize=9, color=colour)

        v = self.values[self.sel]
        if v["activation_m"] is not None and v["end_m"] is not None:
            length = (v["end_m"] - v["activation_m"]) % self.L
            info = f"Zone {self.sel} ({self.names.get(self.sel)}): length {length:.0f} m"
        else:
            info = f"Zone {self.sel} ({self.names.get(self.sel)}): activation or end not set - press a / e to place"
        ax.text(0.01, 0.99, info, transform=ax.transAxes, va="top", fontsize=9)
        ax.text(0.5, -0.01, self.HELP, transform=ax.transAxes, ha="center", va="top", fontsize=8)
        ax.set_title(f"{self.title}\n{self.status}", fontsize=10)
        ax.set_aspect("equal")
        ax.axis("off")
    
    def result(self) -> Dict[int, dict]:
        out: Dict[int, dict] = {}
        for n, vals in self.values.items():
            changed = {}
            for key in DRS_EDIT_KEYS:
                v, v0 = vals[key], self.initial[n][key]
                if v is not None and (v0 is None or abs(v - v0) > 0.05):
                    changed[key] = round(float(v), 1)
            if "detection_m" in changed:
                changed["no_detection"] = False
            elif n in self.removed:
                changed["no_detection"] = True
            if changed:
                out[n] = changed
        return out

def _run_drs_editor(session: _DrsEditSession) -> Optional[Dict[int, dict]]:
    import matplotlib
    if matplotlib.get_backend().lower() in ("agg", "pdf", "ps", "svg", "cairo", "template"):
        logger.error("matplotlib has no interactive backend here (tkinter missing?). Try pip install PyQt5")
        return None
    import matplotlib.pyplot as plt
    for key in list(matplotlib.rcParams):
        if key.startswith("keymap."):
            matplotlib.rcParams[key] = []
    
    fig, ax = plt.subplots(figsize=(10, 10))
    outcome = {"action": None}

    def redraw() -> None:
        session.draw(ax)
        fig.canvas.draw_idle()

    def on_key(event) -> None:
        action = session.on_key(event.key)
        if action:
            outcome["action"] = action
            plt.close(fig)
            return
        redraw()
    
    def on_press(event) -> None:
        if event.inaxes is ax and event.button == 1:
            session.on_press(ax, event.x, event.y)
            redraw()

    def on_motion(event) -> None:
        if session.drag and event.inaxes is ax:
            session.on_motion(ax, event.x, event.y)
            redraw()

    def on_release(event) -> None:
        if session.drag:
            session.on_release()
            redraw()

    fig.canvas.mpl_connect("key_press_event", on_key)
    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("button_release_event", on_release)
    redraw()
    plt.show(block=True)
    return session.result() if outcome["action"] == "save" else None

def _run_review_ui(session: _ReviewSession) -> Optional[dict]:
    import matplotlib
    if matplotlib.get_backend().lower() in ("agg", "pdf", "ps", "svg", "cairo", "template"):
        logger.error("matplotlib has no interactive backend here (tkinter missing?). Try: pip install PyQt5")
        return None
    import matplotlib.pyplot as plt
    for key in list(matplotlib.rcParams):
        if key.startswith("keymap."):
            matplotlib.rcParams[key] = []

    fig, ax = plt.subplots(figsize=(10, 10))
    outcome = {"action": None}

    def redraw() -> None:
        session.draw(ax)
        fig.canvas.draw_idle()

    def on_key(event) -> None:
        action = session.on_key(event.key)
        if action:
            outcome["action"] = action
            plt.close(fig)
            return
        redraw()

    def on_click(event) -> None:
        if event.inaxes is ax:
            session.on_click(ax, event.x, event.y)
            redraw()

    fig.canvas.mpl_connect("key_press_event", on_key)
    fig.canvas.mpl_connect("button_press_event", on_click)
    redraw()
    plt.show(block=True)
    return session.result() if outcome["action"] == "save" else None

def extract_pit_boundaries(session, geometry: Optional[dict]) -> Tuple[Optional[float], Optional[float]]:
    if geometry is None:
        return None, None
    try:
        import pandas as pd
        pos_data = session.pos_data
    except Exception as e:
        logger.warning(f"No position data for pit detection: {e}")
        return None, None

    ref_x, ref_y, ref_d = geometry["x"], geometry["y"], geometry["dist"]
    entries: List[float] = []
    exits: List[float] = []
    cache: Dict[str, tuple] = {}
    stats: Counter = Counter()
    walked: Dict[str, List[float]] = {"PitInTime": [], "PitOutTime": []}
    window = np.timedelta64(int(PIT_MATCH_WINDOW_S * 1000), "ms")
    limit = np.timedelta64(int(PIT_WALK_MAX_S * 1000), "ms")

    def usable(x: float, y: float) -> Optional[float]:
        if not (np.isfinite(x) and np.isfinite(y)) or (x == 0 and y == 0):
            return None
        d2 = (ref_x - x) ** 2 + (ref_y - y) ** 2
        j = int(np.argmin(d2))
        if float(np.sqrt(d2[j])) > PIT_MAX_OFFSET_M:
            return None
        return float(ref_d[j])

    for _, lap in session.laps.iterrows():
        number = str(lap["DriverNumber"])
        if number not in cache:
            pos = pos_data.get(number)
            if pos is None or "SessionTime" not in pos.columns:
                cache[number] = None
            else:
                cache[number] = (
                    pos["SessionTime"].to_numpy(),
                    pos["X"].to_numpy(dtype=float) / 10.0,
                    pos["Y"].to_numpy(dtype=float) / 10.0,
                )
        data = cache[number]
        if data is None:
            continue
        times, px, py = data
        for column, bucket, step in (("PitInTime", entries, -1), ("PitOutTime", exits, 1)):
            t = lap.get(column)
            if t is None or pd.isna(t):
                continue
            t64 = t.to_timedelta64()
            i = int(np.argmin(np.abs(times - t64)))
            if abs(times[i] - t64) > window:
                stats["no position sample within window"] += 1
                continue
            d = usable(px[i], py[i])
            if d is not None:
                stats[f"{column} used directly"] += 1
                bucket.append(d)
                continue

            k, found = i, None
            while 0 <= k + step < len(times) and abs(times[k] - t64) <= limit:
                k += step
                d = usable(px[k], py[k])
                if d is not None:
                    found = (d, k)
                    break
            if found is None:
                stats[f"{column} no usable position within {PIT_WALK_MAX_S:.0f}s"] += 1
                continue
            stats[f"{column} recovered by walking"] += 1
            walked[column].append(abs(float((times[found[1]] - t64) / np.timedelta64(1, "s"))))
            bucket.append(found[0])


    logger.info(f"Pit event filtering: {dict(stats)}")
    for column, secs in walked.items():
        if secs:
            logger.info(f"{column}: usable position found {np.median(secs):.1f}s from the event (median), range {min(secs):.1f}-{max(secs):.1f}s")

    def summarise(values: List[float], label: str) -> Optional[float]:
        if not values:
            return None
        spread = float(np.max(values) - np.min(values))
        logger.info(f"Pit {label}: {len(values)} events, median {np.median(values):.0f} m, spread {spread:.0f} m")
        if spread > PIT_SPREAD_WARN_M:
            logger.warning(f"Pit {label} positions vary by {spread:.0f} m - check the value")
        return round(float(np.median(values)), 1)

    return summarise(entries, "entry"), summarise(exits, "exit")

def _circ_offset(value: float, ref: float, length: float) -> float:
    if length <= 0:
        return value
    return ref + ((value - ref + length / 2.0) % length) - length / 2.0

def _drs_intervals_for_lap(dist: np.ndarray, drs: np.ndarray, track_length: float) -> List[dict]:
    n = len(dist)
    if n < 3:
        return []
    is_open = drs >= DRS_OPEN_MIN
    is_elig = np.isin(drs, DRS_ELIGIBLE_VALUES)

    def boundary(i: int) -> float:
        return float((dist[i - 1] + dist[i]) / 2.0)

    raw: List[dict] = []
    cur: Optional[dict] = {"start": None, "start_idx": 0} if is_open[0] else None
    for i in range(1, n):
        if is_open[i] and not is_open[i - 1]:
            cur = {"start": boundary(i), "start_idx": i}
        elif (not is_open[i]) and is_open[i - 1] and cur is not None:
            cur["end"] = boundary(i)
            raw.append(cur)
            cur = None
    if cur is not None:
        cur["end"] = None
        raw.append(cur)

    merged: List[dict] = []
    for iv in raw:
        if merged and merged[-1]["end"] is not None and iv["start"] is not None and iv["start"] - merged[-1]["end"] < DRS_FLICKER_GAP_M:
            merged[-1]["end"] = iv["end"]
        else:
            merged.append(iv)
    raw = merged

    for iv in raw:
        iv["detection"] = None
        if iv["start"] is None:
            continue
        i0 = iv["start_idx"]
        j = i0
        while j - 1 >= 0 and is_elig[j - 1]:
            j -= 1
        if 0 < j < i0 and dist[i0] - dist[j] <= DRS_DETECT_LOOKBACK_M:
            iv["detection"] = boundary(j)

    if not raw:
        return []
    out: List[dict] = []
    first_open, last_open = raw[0]["start"] is None, raw[-1]["end"] is None
    body = list(raw)
    if first_open and last_open and len(raw) >= 2:
        joined = {"start": raw[-1]["start"], "end": raw[0]["end"] + track_length, "detection": raw[-1]["detection"]}
        body = raw[1:-1]
        out.append(joined)
    else:
        if first_open:
            body = body[1:]
        if last_open:
            body = body[:-1]
    out += [{"start": iv["start"], "end": iv["end"], "detection": iv["detection"]} for iv in body]
    return [iv for iv in out if iv["end"] - iv["start"] >= DRS_MIN_LENGTH_M]

def _cluster_drs_intervals(per_lap: List[List[dict]], track_length: float, min_laps: int) -> List[dict]:
    L = track_length
    items = []
    for lap_i, ivs in enumerate(per_lap):
        for iv in ivs:
            items.append((((iv["start"] + iv["end"]) / 2.0) % L, lap_i, iv))
    if not items:
        return []
    items.sort(key=lambda t: t[0])
    clusters: List[list] = [[items[0]]]
    for it in items[1:]:
        if it[0] - clusters[-1][-1][0] <= DRS_CLUSTER_GAP_M:
            clusters[-1].append(it)
        else:
            clusters.append([it])
    if len(clusters) > 1 and clusters[0][0][0] + L - clusters [-1][-1][0] <= DRS_CLUSTER_GAP_M:
        clusters[0] = clusters.pop() + clusters[0]

    zones: List[dict] = []
    for cl in clusters:
        laps_seen = {lap_i for _, lap_i, _ in cl}
        if len(laps_seen) < min_laps:
            continue
        ref = cl[0][2]["start"]
        starts, ends, dets = [], [], []
        for _, _, iv in cl:
            s = _circ_offset(iv["start"], ref, L)
            starts.append(s)
            ends.append(s + (iv["end"] - iv["start"]))
            if iv["detection"] is not None:
                d = _circ_offset(iv["detection"], s, L)
                if d <= s:
                    dets.append(d)
        s_med, e_med = float(np.median(starts)), float(np.median(ends))
        zones.append({
            "activation_m": round(s_med % L, 1),
            "end_m": round(e_med % L, 1),
            "detection_m": round(float(np.median(dets)) % L, 1) if dets else None,
            "length_m": round(e_med - s_med, 1),
            "n_laps": len(laps_seen),
            "start_spread_m": round(float(np.ptp(starts)), 1),
            "end_spread_m": round(float(np.ptp(ends)), 1),
        })
    zones.sort(key=lambda z: z["activation_m"])
    return zones

def extract_drs_zones_from_telemetry(session, track_length: float, num_laps: int = DRS_NUM_LAPS) -> Optional[List[dict]]:
    if track_length <= 0:
        return None
    laps = session.laps.copy()
    if "Deleted" in laps.columns:
        laps = laps[laps["Deleted"] != True]
    laps = laps.dropna(subset=["LapTime"])
    top = laps.loc[laps.groupby("Driver")["LapTime"].idxmin()].sort_values("LapTime").head(num_laps)

    per_lap: List[List[dict]] = []
    seen_values: set = set()
    for _, lap_row in top.iterrows():
        driver = lap_row["Driver"]
        try:
            tel = _get_lap_telemetry(lap_row)
            if "DRS" not in tel.columns or "Distance" not in tel.columns:
                logger.warning(f"{driver}: telemetry has no DRS channel")
                continue
            dist = tel["Distance"].to_numpy(dtype=float)
            drs = np.nan_to_num(tel["DRS"].to_numpy(dtype=float), nan=0.0)
            ok = np.isfinite(dist)
            dist, drs = dist[ok], drs[ok]
            keep = np.concatenate(([True], np.diff(dist) > 0))
            dist, drs = dist[keep], drs[keep]
            seen_values |= {int(v) for v in np.unique(drs)}
            ivs = _drs_intervals_for_lap(dist, drs, track_length)
            logger.debug(f"{driver}: {len(ivs)} DRS/SM intervals")
            per_lap.append(ivs)
        except Exception as e:
            logger.warning(f"{driver}: could not read DRS channel: {e}")

    logger.info(f"DRS channel values seen on {len(per_lap)} laps: {sorted(seen_values)} (open >= {DRS_OPEN_MIN}, eligible {DRS_ELIGIBLE_VALUES})")
    if not per_lap or not any(v >= DRS_OPEN_MIN for v in seen_values):
        logger.warning("DRS channel never reaches an 'open' value - check DRS_OPEN_MIN against the values logged above")
        return None
    min_laps = 1 if len(per_lap) < 2 else max(2, int(np.ceil(DRS_MIN_LAP_FRACTION * len(per_lap))))
    zones = _cluster_drs_intervals(per_lap, track_length, min_laps)
    for z in zones:
        det = "n/a" if z ["detection_m"] is None else f"{z['detection_m']:.0f} m"
        logger.info(
            f"Measured DRS/SM zone: detection {det}, activation {z['activation_m']:.0f} m, end {z['end_m']:.0f} m, "
            f"length {z['length_m']:.0f} m, seen on {z['n_laps']}/{len(per_lap)} laps"
        )
    return zones

def _clean_path(x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    ok = np.isfinite(x) & np.isfinite(y) & ~((x == 0) & (y == 0))
    x, y = x[ok], y[ok]
    if len(x) == 0:
        return x, y
    kx, ky = [float(x[0])], [float(y[0])]
    for a, b in zip(x[1:], y[1:]):
        if np.hypot(a - kx[-1], b - ky[-1]) >= PIT_PATH_MIN_STEP_M:
            kx.append(float(a))
            ky.append(float(b))
    return np.array(kx), np.array(ky)

def extract_pit_lane_path(session, geometry: Optional[dict]) -> Optional[dict]:
    if geometry is None:
        return None
    try:
        pos_data = session.pos_data
    except Exception as e:
        logger.warning(f"No position data for the pit lane trace: {e}")
        return None

    import pandas as pd
    laps = session.laps
    passes: List[Tuple[np.ndarray, np.ndarray]] = []
    for number in laps["DriverNumber"].unique():
        pos = pos_data.get(str(number))
        if pos is None or "SessionTime" not in pos.columns:
            continue
        rows = [r for _, r in laps[laps["DriverNumber"] == number].sort_values("LapNumber").iterrows()]
        for a, b in zip(rows, rows[1:]):
            t_in, t_out = a.get("PitInTime"), b.get("PitOutTime")
            if t_in is None or t_out is None or pd.isna(t_in) or pd.isna(t_out):
                continue
            if b["LapNumber"] != a["LapNumber"] + 1 or t_out <= t_in or (t_out - t_in).total_seconds() > PIT_PATH_MAX_S:
                continue
            sub = pos[(pos["SessionTime"] >= t_in) & (pos["SessionTime"] <= t_out)]
            x, y = _clean_path(sub["X"].to_numpy(dtype=float) / 10.0, sub["Y"].to_numpy(dtype=float) / 10.0)
            if len(x) >= PIT_PATH_MIN_POINTS:
                passes.append((x, y))
    if not passes:
        logger.warning("No pit in/out pairs with usable position data - pit lane trace not drawn")
        return None

    ref_x, ref_y = geometry["x"], geometry["y"]
    def off_track(px: float, py: float) -> float:
        return float(np.sqrt(np.min((ref_x - px) ** 2 + (ref_y - py) ** 2)))
    near = [(x, y) for x, y in passes if off_track(x[0], y[0]) <= PIT_MAX_OFFSET_M and off_track(x[-1], y[-1]) <= PIT_MAX_OFFSET_M]
    usable = near or passes
    lengths = np.array([float(np.sum(np.hypot(np.diff(x), np.diff(y)))) for x, y in usable])
    best = int(np.argmin(np.abs(lengths - np.median(lengths))))
    x, y = usable[best]
    w = 5
    if len(x) > w:
        pad = lambda a: np.pad(a, (w // 2, w - 1 - w // 2), mode="edge")
        sx = np.convolve(pad(x), np.ones(w) / w, mode="valid")
        sy = np.convolve(pad(y), np.ones(w) / w, mode="valid")
        sx[0], sy[0], sx[-1], sy[-1] = x[0], y[0], x[-1], y[-1]
        x, y = sx, sy
    logger.info(f"Pit lane trace: {len(passes)} passes ({len(near)} start/end near the track), using one of {lengths[best]:.0f} m")
    return {"x": x, "y": y, "length_m": round(float(lengths[best]), 1), "n_passes": len(passes)}

def _corner_entry_m(c) -> float:
    return c.distance_brake_m if c.distance_brake_m is not None else c.distance_apex_m

def _compute_drs_zones(manual_drs: List[dict], corners: List, track_length: float, measured: Optional[List[dict]] = None, season: Optional[int] = None, edits: Optional[Dict[int, dict]] = None) -> Tuple[List[DRSZone], List[str]]:
    edits = edits or {}
    manual_drs = [
        {**dz, **{k: v for k, v in edits.get(i + 1, {}).items() if v is not None}}
        for i, dz in enumerate(manual_drs)
    ]
    by_number = {c.corner_number: c for c in corners}
    zones: List[DRSZone] = []
    warnings: List[str] = []

    def wrap(d: float) -> float:
        return round(d % track_length, 1) if track_length > 0 else round(d, 1)
    
    expected: List[Optional[float]] = []
    for dz in manual_drs:
        after = by_number.get(dz.get("after_corner"))
        exp = dz.get("activation_m")
        if exp is None and after is not None:
            exp = after.distance_exit_m
        expected.append(exp)

    assign: Dict[int, int] = {}
    if measured:
        cands = sorted(
            (abs(_circ_offset(m["activation_m"], exp, track_length) - exp), i, k)
            for i, exp in enumerate(expected) if exp is not None
            for k, m in enumerate(measured)
        )
        used_k: set = set()
        for gap, i, k in cands:
            if gap > DRS_ASSIGN_MAX_M:
                break
            if i in assign or k in used_k:
                continue
            assign[i] = k
            used_k.add(k)
        for k, m in enumerate(measured):
            if k not in used_k:
                warnings.append(
                    f"Telemetry shows a DRS/straight mode zone {m['activation_m']:.0f}-{m['end_m']:.0f} m "
                    f"(seen on {m['n_laps']} laps) that matches no zone in the metadata"
                )

    for i, dz in enumerate(manual_drs):
        number = i + 1
        name = dz.get("straight")
        after = by_number.get(dz.get("after_corner"))
        before = by_number.get(dz.get("before_corner"))
        det = by_number.get(dz.get("detection_before_corner", dz.get("after_corner")))
        meas = measured[assign[i]] if i in assign else None
        no_detection = bool(dz.get("no_detection", season in DRS_NO_DETECTION_SEASONS))
        sources: Dict[str, str] = {}

        def pick(key: str, measured_key: str, derived):
            if dz.get(key) is not None:
                sources[key] = "metadata"
                return dz[key]
            if meas is not None and meas.get(measured_key) is not None:
                sources[key] = "telemetry"
                return meas[measured_key]
            if derived is not None:
                sources[key] = "corner estimate"
            return derived

        activation = pick("activation_m", "activation_m", after.distance_exit_m if after is not None else None)
        end = pick("end_m", "end_m", _corner_entry_m(before) if before is not None else None)
        detection = None if no_detection else pick("detection_m", "detection_m", _corner_entry_m(det) if det is not None else None)
        if measured is not None and meas is None and (season is None or season in dz.get("available_in", [season])):
            warnings.append(f"DRS zone {number} ({name}): no zone in the telemetry near T{dz.get('after_corner')} exit - using corner-based estimates")
        elif meas is not None and sources.get("detection_m") == "corner estimate":
            warnings.append(f"DRS zone {number} ({name}): detection point was never seen in the telemetry ('eligible' state) - estimated from the corner brake point")

        length = None
        required = [("activation_m", activation), ("end_m", end)] + ([] if no_detection else [("detection_m", detection)])
        missing = [k for k, v in required if v is None]
        if missing:
            warnings.append(
                f"DRS zone {number} ({name}): could not compute {', '.join(missing)} - add after_corner / before_corner "
                f"(official corner numbers, both must exist in the JSON) or set the values in the metadata"
            )
        else:
            length = (end - activation) % track_length if track_length > 0 else end - activation
            if length < DRS_MIN_LENGTH_M or length > DRS_MAX_LENGTH_M:
                warnings.append(f"DRS zone {number} ({name}): length {length:.0f} m looks wrong - check after_corner / before_corner")

        def fmt(v) -> str:
            return "n/a" if v is None else f"{v:.0f} m"

        logger.info(
            f"DRS zone{number} ({name}): detection {fmt(detection)} [{sources.get('detection_m', '-')}], "
            f"activation {fmt(activation)} [{sources.get('activation_m', '-')}], "
            f"end {fmt(end)} [{sources.get('end_m', '-')}]"
            + (f", length {length:.0f} m" if length is not None else "")
        )

        zones.append(DRSZone(
            zone_number=number,
            detection_m=wrap(detection) if detection is not None else 0.0,
            activation_m=wrap(activation) if activation is not None else 0.0,
            end_m=wrap(end) if end is not None else 0.0,
            straight_name=name,
            available_in=dz.get("available_in", [2025, 2026]),
            notes=dz.get("notes", "")
        ))
    return zones, warnings

def build_track_knowledge(
        track_id: int,
        location: str,
        session,
        manual: Optional[dict],
        reference_season: int,
        slug: str = "",
        review: bool = False,
        use_overrides: bool = True,
        use_saved_detections: bool = True,
        edit_drs: bool = False,
) -> Tuple[TrackKnowledge, dict]:
    meta = manual or {} 
    manual_corners = meta.get("corners", [])
    manual_drs = meta.get("drs_zones", [])
    manual_pit = meta.get("pit", {})

    detected, geometry = extract_corners_from_telemetry(session)
    logger.info(f"Detected {len(detected)} corners from racing line")

    overrides = _load_overrides(slug) if (use_overrides and slug) else None
    saved_detections = overrides.get("detections") if overrides else None
    if saved_detections and use_saved_detections:
        logger.info(
            f"Using the {len(saved_detections)} detections stored in the override file "
            f"(the live detection found {len(detected)}; use --redetect to use the live ones instead)"
        )
        detected = saved_detections
    raw_detected = detected
    corners_in, ignore_in, complete = _apply_overrides(manual_corners, meta.get("ignore_apex_m", []), overrides)
    detected, ignored, cal, pairs, match_notes = _match_to_metadata(raw_detected, corners_in, ignore_in, complete)

    if review:
        if geometry is None:
            logger.warning("No racing-line geometry - cannot open the review window")
        else:
            labels = _initial_review_labels(raw_detected, detected, ignored, pairs, corners_in)
            expected = [m.get("corner_number", i + 1) for i, m in enumerate(manual_corners)]
            expected_dirs = {m.get("corner_number", i + 1): m["direction"] for i, m in enumerate(manual_corners) if m.get("direction")}
            review_session = _ReviewSession(f"{slug or location} - review", geometry, raw_detected, labels, cal, expected, expected_dirs)
            result = _run_review_ui(review_session)
            if result is not None:
                raw_detected = review_session.detected
                result = dict(result, version=2, detections=raw_detected)
                _save_overrides(slug, result)
                overrides = result
                corners_in, ignore_in, complete = _apply_overrides(manual_corners, meta.get("ignore_apex_m", []), result)
                detected, ignored, cal, pairs, match_notes = _match_to_metadata(raw_detected, corners_in, ignore_in, complete)
            else:
                logger.info("Review cancelled - nothing saved")
    manual_corners = corners_in
    matched_det = {d for d, _ in pairs}
    matched_meta = {m for _, m in pairs if m is not None}
    warnings: List[str] = list(match_notes)
    _log_detection_table(detected, pairs, manual_corners, cal)

    if geometry is not None and abs(abs(geometry["heading_total_deg"]) - 360.0) > HEADING_SANITY_TOL_DEG:
        warnings.append(f"Total heading change {geometry['heading_total_deg']:.0f} deg is not close to +/-360 (position data suspect)")

    sector2_dist, sector3_dist = extract_sector_boundaries(session)
    try:
        track_length = float(session.laps.pick_fastest().get_car_data().add_distance()["Distance"].max())
    except Exception:
        track_length = 0.0

    type_map = {
        "hairpin": CornerType.HAIRPIN,
        "slow_chicane": CornerType.SLOW_CHICANE,
        "fast_chicane": CornerType.FAST_CHICANE,
        "medium_radius": CornerType.MEDIUM_RADIUS,
        "high_speed_sweep": CornerType.HIGH_SPEED_SWEEP,
        "double_apex": CornerType.DOUBLE_APEX,
        "long_radius": CornerType.LONG_RADIUS,
    }

    corners: List[CornerInfo] = []
    resolved: Dict[str, dict] = {}
    for det_i, meta_i in pairs:
        tel_c = detected[det_i]
        m = manual_corners[meta_i] if meta_i is not None else {}
        number = m.get("corner_number", len(corners) + 1)

        geo_dir = _direction_of(tel_c, cal)
        if m.get("direction") and m["direction"] != geo_dir:
            warnings.append(f"T{number}: metadata says {m['direction']} but the racing line turns {geo_dir} - check the metadata")
        direction = CornerDirection.LEFT if geo_dir == "left" else CornerDirection.RIGHT

        apex_speed = tel_c["reference_apex_speed_kph"]
        speed_class = CornerSpeed.from_apex_speed(apex_speed)
        corner_type = type_map.get(m.get("type", "medium_radius"), CornerType.MEDIUM_RADIUS)

        apex_dist = tel_c["distance_apex_m"]
        if apex_dist >= sector3_dist > 0:
            sector = SectorNumber.S3
        elif apex_dist >= sector2_dist > 0:
            sector = SectorNumber.S2
        else:
            sector = SectorNumber.S1

        if tel_c["brake_type"] == "flat" and not m.get("flat_out"):
            warnings.append(f"T{number}: no braking or throttle lift found (flat out in reference lap)")
        if tel_c["estimated_lateral_g"] > LATERAL_G_WARN:
            warnings.append(
                f"T{number}: estimated lateral g {tel_c['estimated_lateral_g']:.1f} is unrealistic "
                f"(radius {tel_c['radius_m']:.0f} m at {apex_speed:.0f} kph) - curvature spike, check smoothing"
            )

        corners.append(_make_corner_info(
            corner_number=number,
            name=m.get("name"),
            sector=sector,
            direction=direction,
            speed_class=speed_class,
            corner_type=corner_type,
            distance_brake_m=tel_c["distance_brake_m"],
            distance_apex_m=tel_c["distance_apex_m"],
            distance_exit_m=tel_c["distance_exit_m"],
            reference_apex_speed_kph=apex_speed,
            reference_braking_zone_m=tel_c["reference_braking_zone_m"],
            tyre_sensitive=m.get("tyre_sensitive", False),
            overtaking_opportunity=m.get("overtaking", False),
            drs_activation_after=m.get("drs_after", False),
            notes=m.get("notes", ""),
            lift_only=tel_c["brake_type"] == "lift",
            flat_out=tel_c["brake_type"] == "flat",
            shared_braking_with_previous=tel_c["shared_braking"],
            heading_change_deg=tel_c["heading_change_deg"],
            radius_m=tel_c["radius_m"],
            estimated_lateral_g=tel_c["estimated_lateral_g"],
        ))
        resolved[str(number)] = {
            "corner_number": number,
            "direction": geo_dir,
            "source_apex_m": list(tel_c.get("member_apex_m", [tel_c["distance_apex_m"]])),
            **{k: v for k, v in tel_c.items() if k != "member_apex_m"},
        }

    expected = [m for m in manual_corners if not m.get("flat_out")]
    if manual_corners:
        logger.info(
            f"Matched {len(matched_meta)}/{len(manual_corners)} metadata corners "
            f"({len(expected)} required), {len(detected) - len(matched_det)} detections unmatched, "
            f"{len(ignored)} ignored"
        )
    for j, m in enumerate(manual_corners):
        if j not in matched_meta and not m.get("flat_out"):
            warnings.append(f"Metadata T{m.get('corner_number', j + 1)} ({m.get('direction')}) was not found in the racing line (merged with a neighbour or too gentle)")
    for i, c in enumerate(detected):
        if not complete and i not in matched_det and c["heading_change_deg"] >= STRONG_CORNER_DEG:
            warnings.append(
                f"Unlisted {c['heading_change_deg']:.0f} deg {_direction_of(c, cal)} corner at {c['distance_apex_m']:.0f} m "
                f"({c['reference_apex_speed_kph']:.0f} kph) is not in the metadata"
            )
    for a, b in zip(corners, corners[1:]):
        gap = b.distance_apex_m - a.distance_apex_m
        if gap > MAX_APEX_GAP_M:
            warnings.append(f"{gap:.0f} m between T{a.corner_number} and T{b.corner_number} - corner missing in between?")

    measured_drs = extract_drs_zones_from_telemetry(session, track_length) if manual_drs else None
    if manual_drs and measured_drs is None:
        warnings.append("DRS channel unusable - DRS / straight mode zones are estimated from corner positions only")

    drs_edits = _load_drs_edits(slug) if (use_overrides and slug) else {}
    drs_zones, drs_warnings = _compute_drs_zones(manual_drs, corners, track_length, measured_drs, reference_season, drs_edits)

    if edit_drs and drs_zones and geometry is not None and slug:
        changes = _run_drs_editor(_DrsEditSession(f"{slug} - DRS zones", geometry, cal, drs_zones, track_length))
        if changes is None:
            logger.info("DRS edit cancelled - nothing saved")
        elif not changes:
            logger.info("No DRS changes made")
        else:
            for n, vals in changes.items():
                drs_edits[n] = {**drs_edits.get(n, {}), **vals}
            _save_drs_edits(slug, drs_edits)
            drs_zones, drs_warnings = _compute_drs_zones(manual_drs, corners, track_length, measured_drs, reference_season, drs_edits)
    warnings += drs_warnings

    pit_entry, pit_exit = extract_pit_boundaries(session, geometry)
    if manual_pit.get("entry_m") is not None:
        pit_entry = manual_pit["entry_m"]
    if manual_pit.get("exit_m") is not None:
        pit_exit = manual_pit["exit_m"]
    if manual_pit:
        for label, value in (("entry", pit_entry), ("exit", pit_exit)):
            if value is None:
                warnings.append(f"Pit {label} not found in the session's pit events - set pit['{label}_m'] in the metadata")
    pit_zone = PitZone(
        pit_entry_m=pit_entry if pit_entry is not None else 0.0,
        pit_exit_m=pit_exit if pit_exit is not None else 0.0,
        speed_limit_kph=manual_pit.get("speed_limit_kph", 80),
    ) if manual_pit else None

    pit_path = extract_pit_lane_path(session, geometry)

    if overrides is not None and use_overrides and slug:
        _save_overrides(slug, {
            "version": 2,
            "ignore_apex_m": sorted(overrides.get("ignore_apex_m", [])),
            "assignments": overrides.get("assignments", {}),
            "detections": raw_detected,
            "corners": dict(sorted(resolved.items(), key=lambda kv: int(kv[0]))),
        })

    tk = TrackKnowledge(
        track_id=track_id,
        name=meta.get("name", location),
        location=location,
        country=meta.get("country", ""),
        reference_season=reference_season,
        fastf1_name=location,
        track_length_m=round(track_length, 1),
        num_corners=len(corners),
        sector2_distance_m=sector2_dist,
        sector3_distance_m=sector3_dist,
        corners=corners,
        drs_zones=drs_zones,
        pit_zone=pit_zone,
        high_speed_circuit=meta.get("high_speed_circuit", False),
        street_circuit=meta.get("street_circuit", False),
        tyre_degradation_high=meta.get("tyre_degradation_high", False),
        overtaking_difficulty=meta.get("overtaking_difficulty", "medium"),
        elevation_change_m=meta.get("elevation_change_m", 0.0),
        notes=meta.get("notes", "")
    )

    report = {
        "warnings": warnings,
        "geometry": geometry,
        "detected": detected,
        "ignored": ignored,
        "pairs": pairs,
        "manual_corners": manual_corners,
        "cal": cal,
        "drs_zones": drs_zones,
        "pit": (pit_entry, pit_exit),
        "pit_path": pit_path,
        "track_length": track_length
    }
    return tk, report

def _draw_start_line(ax, x, y) -> None:
    from matplotlib.patches import Polygon
    k = min(len(x) - 1, 10)
    tx, ty = float(x[k] - x[0]), float(y[k] - y[0])
    norm = float(np.hypot(tx, ty)) or 1.0
    tx, ty = tx / norm, ty / norm
    nx, ny = -ty, tx
    span = float(max(np.ptp(x), np.ptp(y)))
    cols, rows = 8, 2
    size = span * 0.05 / cols
    for r in range (rows):
        for c in range(cols):
            u0 = (c - cols / 2) * size
            v0 = (r - rows / 2) * size
            corners = [(u0, v0), (u0 + size, v0), (u0 + size, v0 + size), (u0, v0 + size)]
            pts = [(float(x[0]) + nx * u + tx * v, float(y[0]) + ny * u + ty * v) for u, v in corners]
            ax.add_patch(Polygon(pts, closed=True, facecolor="black" if (r + c) % 2 == 0 else "white", edgecolor="black", linewidth=0.5, zorder=4))

def _draw_zones_and_pit(ax, dist, x, y, drs_zones, pit, track_length, pit_path=None) -> None:
    def point(d: float) -> Tuple[float, float]:
        d = d % track_length if track_length > 0 else d
        return float(np.interp(d, dist, x)), float(np.interp(d, dist, y))

    def pieces(a: float, b: float) -> List[Tuple[float, float]]:
        if b >= a:
            return [(a, b)]
        return [(a, float(dist[-1])), (float(dist[0]), b)]

    for z in drs_zones:
        if z.activation_m == 0.0 and z.end_m == 0:
            continue
        for lo, hi in pieces(z.activation_m, z.end_m):
            mask = (dist >= lo) & (dist <= hi)
            if int(mask.sum()) > 1:
                ax.plot(x[mask], y[mask], color="tab:blue", linewidth=6, alpha=0.45, solid_capstyle="butt", zorder=2)
        px, py = point(z.activation_m)
        ax.annotate(f"DRS {z.zone_number}", (px, py), textcoords="offset points", xytext=(10, -14), fontsize=8, color="tab:blue")
        if z.detection_m:
            dx, dy = point(z.detection_m)
            ax.scatter([dx], [dy], marker="D", s=40, color="tab:blue", zorder=4)

    if pit_path is not None:
        ax.plot(pit_path[0], pit_path[1], color="tab:purple", linewidth=2.5, solid_capstyle="round", zorder=3)
        mid = len(pit_path[0]) // 2
        ax.annotate("pit lane", (pit_path[0][mid], pit_path[1][mid]), textcoords="offset points", xytext=(10, -4), fontsize=8, color="tab:purple")

    for label, d in zip(("pit in", "pit out"), pit):
        if d is None:
            continue
        px, py = point(d)
        ax.scatter([px], [py], marker="v", s=70, color="tab:purple", zorder=4)
        ax.annotate(label, (px, py), textcoords="offset points", xytext=(8, 6), fontsize=8, color="tab:purple")

def _plot_track(title: str, report: dict, path: Path) -> None:
    geometry = report.get("geometry")
    if geometry is None:
        return
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
    except ImportError:
        logger.info("matplotlib not installed - skipping review plot")
        return

    dist, x, y = geometry["dist"], geometry["x"], geometry["y"]
    if report["cal"] < 0:
        y = -y

    manual = report["manual_corners"]
    matched = {d: m for d, m in report["pairs"] if m is not None}
    colours = {"brake": "tab:red", "lift": "tab:orange", "flat": "tab:green"}

    fig = Figure(figsize=(9, 9))
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    ax.plot(x, y, color="0.45", linewidth=1.8)
    _draw_start_line(ax, x, y)
    pit_path = report.get("pit_path")
    if pit_path is not None:
        pit_path = (pit_path["x"], -pit_path["y"] if report["cal"] < 0 else pit_path["y"])
    _draw_zones_and_pit(ax, dist, x, y, report.get("drs_zones", []), report.get("pit", (None, None)), report.get("track_length", 0.0), pit_path)
    ax.annotate("S/F", (x[0], y[0]), textcoords="offset points", xytext=(8, 8), fontsize=9)

    for i, c in enumerate(report["detected"]):
        px = float(np.interp(c["distance_apex_m"], dist, x))
        py = float(np.interp(c["distance_apex_m"], dist, y))
        if i in matched:
            label = str(manual[matched[i]].get("corner_number", matched[i] + 1))
            colour = colours.get(c["brake_type"], "tab:blue")
        else:
            label, colour = "?", "0.6"
        ax.scatter([px], [py], s=170, color=colour, zorder=3)
        ax.annotate(label, (px, py), ha="center", va="center", fontsize=8, color="white", zorder=5)

    ax.set_aspect("equal")
    ax.set_title(f"{title} - red: braking, orange: lift only, green: flat out, grey ?: not in metadata, blue:DRS, purple:pit", fontsize=9)
    ax.axis("off")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130, bbox_inches="tight")

def generate_circuit(
        track_id: int,
        location: str,
        slug: str,
        force: bool,
        plots: bool = True,
        review: bool = False,
        use_overrides: bool = True,
        use_saved_detections: bool = True,
        edit_drs: bool = False,
) -> Tuple[bool, List[str]]:
    output_path = OUTPUT_DIR / f"{slug}.json"

    if output_path.exists() and not force:
        logger.info(f"Skipping {location} - {output_path.name} already exists (use --force to regenerate)")
        return True, []
    try:
        session, season_used = load_fastf1_session(location, slug)
        manual = MANUAL_METADATA.get(slug)
        tk, report = build_track_knowledge(track_id, location, session, manual, season_used, slug=slug, review=review, use_overrides=use_overrides, use_saved_detections=use_saved_detections, edit_drs=edit_drs)
        if tk.num_corners == 0:
            raise RuntimeError("no corners detected - not writing an empty JSON (see warnings above)")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(track_to_dict(tk), f, indent=2, ensure_ascii=False)

        if plots:
            try:
                _plot_track(slug, report, OUTPUT_DIR / "plots" / f"{slug}.png")
            except Exception as e:
                logger.warning(f"Could not write review plot for {slug}: {e}")

        logger.info(f"Generated {output_path.name} using {season_used} telemetry: {tk.num_corners} corners, {tk.track_length_m:.0f}m")
        for w in report["warnings"]:
            logger.warning(f"[{slug}] {w}")
        return True, report["warnings"]

    except Exception as e:
        logger.error(f"Failed to generate {location}: {e}", exc_info=True)
        return False, [f"generation failed: {e}"]

def main():
    parser = argparse.ArgumentParser(
        description="Generate static circuit knowledge JSON files from FastF1"
    )
    parser.add_argument(
        "--track",
        type=str,
        default=None,
        help="Generate only this circuit (use slug e.g. 'silverstone'). Omit for all circuits.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate JSON even if it already exists"
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Do not write the review PNG (racing line with numbered apexes)",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="Open the click-to-label window for each track and save the result (implies --force)",
    )
    parser.add_argument(
        "--no-overrides",
        action="store_true",
        help="Ignore saved corner reviews and use the automatic matching only"
    )
    parser.add_argument(
        "--redetect",
        action="store_true",
        help="Ignore the detections stored in the override file and use the freshly detected corners (override assignments are re-matches by apex distance)"
    )
    parser.add_argument(
        "--edit-drs",
        action="store_true",
        help="Open the drag-to-edit window for DRS / straight mode zones after generating each track (implies --force)"
    )
    args = parser.parse_args()

    if args.track:
        target = {
            tid: (loc, slug)
            for tid, (loc, slug) in CIRCUIT_LIST.items()
            if slug == args.track
        }
        if not target:
            logger.error(
                f"Unknown track slug: '{args.track}'. "
                f"Valid slugs: {sorted(s for _, s in CIRCUIT_LIST.values())}"
            )
            sys.exit(1)
    else:
        target = CIRCUIT_LIST

    success_count = 0
    fail_count = 0
    review: Dict[str, List[str]] = {}

    for track_id, (location, slug) in target.items():
        ok, warns = generate_circuit(track_id, location, slug, args.force or args.review or args.edit_drs, plots=not args.no_plots, review=args.review, use_overrides=not args.no_overrides, use_saved_detections=not args.redetect, edit_drs=args.edit_drs)
        if ok:
            success_count += 1
        else:
            fail_count += 1
        if warns:
            review[slug] = warns

    logger.info(
        f"Generation complete: {success_count} succeeded, {fail_count} failed. "
        f"JSON files written to {OUTPUT_DIR}"
    )

    if review:
        logger.warning("---- Tracks that need a manual look ----")
        for slug, items in review.items():
            logger.warning(f"{slug}: {len(items)} items(s)")
            for item in items:
                logger.warning(f"    - {item}")
    else:
        logger.info("No validation warnings.")

    if fail_count > 0:
        logger.warning(
            "Some circuits failed. Check that FastF1 is installed and the cache directory is writable. Individual circuits can be retried with --track <slug>"
        )

    for reverse_id, primary_id in REVERSE_LAYOUT_MAP.items():
        primary_loc, primary_slug = CIRCUIT_LIST.get(primary_id, (None, None))
        if primary_slug is None:
            continue
        primary_path = OUTPUT_DIR / f"{primary_slug}.json"
        if not primary_path.exists():
            continue
        reverse_slug = {7: "silverstone_reverse", 17: "spielberg_reverse", 26: "zandvoort_reverse"}.get(primary_id)
        if reverse_slug is None:
            continue
        reverse_path = OUTPUT_DIR / f"{reverse_slug}.json"
        if reverse_path.exists() and not args.force:
            continue
        try:
            with open(primary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["track_id"] = reverse_id
            data["name"] = data["name"] + " (Reverse)"
            data["notes"] = "Reverse layout. Corner data mirrors the primary layout."
            with open(reverse_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Generated reverse layout: {reverse_path.name}")
        except Exception as e:
            logger.warning(f"Could not generate reverse layout for track_id={reverse_id}: {e}")

if __name__ == "__main__":
    main()