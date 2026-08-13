"""
Packet IDs
    0 Motion
    1 Session
    2 Lap Data
    3 Event
    4 Participants
    5 Car Setups
    6 Car Telemetry
    7 Car Status
    8 Final Classification
    9 Lobby Info
    10 Car Damage
    11 Session History
    12 Tyre Sets
    13 Time Trial
    14 Time Trial
    15 Lap Positions
"""

import struct
from dataclasses import dataclass, field
from typing import Optional, List, Any

PACKET_FORMAT_25 = 2025
PACKET_FORMAT_26 = 2026

MAX_CARS_25 = 22
MAX_CARS_26 = 24

LITTLE_ENDIAN = '<'

class PacketID:
    MOTION = 0
    SESSION = 1
    LAP_DATA = 2
    EVENT = 3
    PARTICIPANTS = 4
    CAR_SETUPS = 5
    CAR_TELEMETRY = 6
    CAR_STATUS = 7
    FINAL_CLASSIFICATION = 8
    LOBBY_INFO = 9
    CAR_DAMAGE = 10
    SESSION_HISTORY = 11
    TYRE_SETS = 12
    MOTION_EX = 13
    TIME_TRIAL = 14
    LAP_POSITIONS = 15
    CAR_TELEMETRY_2 = 16 ## F1 26 DLC

    NAMES = {
        0: "Motion",
        1: "Session",
        2: "Lap Data",
        3: "Event",
        4: "Participants",
        5: "Car Setups",
        6: "Car Telemetry",
        7: "Car Status",
        8: "Final Classification",
        9: "Lobby Info",
        10: "Car Damage",
        11: "Session History",
        12: "Tyre Sets",
        13: "Motion Ex",
        14: "Time Trial",
        15: "Lap Positions",
        16: "Car Telemetry 2",
    }

## Lookup Tables

TEAM_IDS = {
    0: "Mercedes",
    1: "Ferrari",
    2: "Red Bull Racing",
    3: "Williams",
    4: "Aston Martin",
    5: "Alpine",
    6: "RB",
    7: "Haas",
    8: "McLaren",
    9: "Sauber",
    41: "F1 Generic",
    104: "F1 Custom Team",
    129: "Konnersport",
    142: "APXGP '24",
    154: "APXGP '25",
    155: "Konnersport '24",
    158: "Art GP '24",
    159: "Campos '24",
    160: "Rodin Motorsport '24",
    161: "AIX Racing '24",
    162: "DAMS '24",
    163: "Hitech '24",
    164: "MP Motorsport '24",
    165: "Prema '24",
    166: "Trident '24",
    167: "Van Amersfoort Racing '24",
    168: "Invicta '24",
    185: "Mercedes '24",
    186: "Ferrari '24",
    187: "Red Bull Racing '24",
    188: "Williams '24",
    189: "Aston Martin '24",
    190: "Alpine '24",
    191: "RB '24",
    192: "Haas '24",
    193: "McLaren '24",
    194: "Sauber '24",
    ## F1 26 DLC
    465: "Art GP '25",
    466: "Campos '25",
    467: "Rodin Motorsport '25",
    468: "AIX Racing '25",
    469: "DAMS '25",
    470: "Hitech '25",
    471: "MP Motorsport '25",
    472: "Prema '25",
    473: "Trident '25",
    474: "Van Amersfoort Racing '25",
    475: "Invicta '25",
    476: "Mercedes '26",
    477: "Ferrari '26",
    478: "Red Bull Racing '26",
    479: "Williams '26",
    480: "Aston Martin '26",
    481: "Alpine '26",
    482: "RB '26",
    483: "Haas '26",
    484: "McLaren '26",
    485: "Audi '26",
    486: "Cadillac '26",
}

DRIVER_IDS = {
    0: "Carlos Sainz",
    2: "Daniel Ricciardo",
    3: "Fernando Alonso",
    4: "Felipe Massa",
    7: "Lewis Hamilton",
    9: "Max Verstappen",
    10: "Nico Hulkenberg",
    11: "Kevin Magnussen",
    14: "Sergio Perez",
    15: "Valtteri Bottas",
    17: "Esteban Ocon",
    19: "Lance Stroll",
    20: "Arron Barnes",
    21: "Martin Giles",
    22: "Alex Murray",
    23: "Lucas Roth",
    24: "Igor Correia",
    25: "Sophie Levasseur",
    26: "Jonas Schiffer",
    27: "Alain Forest",
    28: "Jay Letourneau",
    29: "Esto Saari",
    30: "Yasar Atiyeh",
    31: "Callisto Calabresi",
    32: "Naota Izumi",
    33: "Howard Clark",
    34: "Lars Kauffmann",
    35: "Marie Laursen",
    36: "Flavio Nieves",
    38: "Klimek Michalski",
    39: "Santiago Moreno",
    40: "Benjamin Coppens",
    41: "Noah Visser",
    50: "George Russell",
    54: "Lando Norris",
    58: "Charles Leclerc",
    59: "Pierre Gasly",
    62: "Alexander Albon",
    70: "Rashid Nair",
    71: "Jack Tremblay",
    77: "Ayrton Senna",
    80: "Guanyu Zhou",
    83: "Juan Manuel Correa",
    90: "Michael Schumacher",
    94: "Yuki Tsunoda",
    102: "Aidan Jackson",
    109: "Jenson Button",
    110: "David Coulthard",
    112: "Oscar Piastri",
    113: "Liam Lawson",
    116: "Richard Verschoor",
    123: "Enzo Fittipaldi",
    125: "Mark Webber",
    126: "Jacque Villeneuve",
    127: "Callie Mayer",
    132: "Logan Sargeant",
    136: "Jack Doohan",
    137: "Amaury Cordeel",
    138: "Dennis Hauger",
    145: "Zane Maloney",
    146: "Victor Martins",
    147: "Oliver Bearman",
    148: "Jak Crawford",
    149: "Isack Hadjar",
    152: "Roman Stanek",
    153: "Kush Maini",
    156: "Brendon Leigh",
    157: "David Tonizza",
    158: "Jarno Opmeer",
    159: "Lucas Blakeley",
    160: "Paul Aron",
    161: "Gabriel Bortoleto",
    162: "Franco Colapinto",
    163: "Taylor Barnard",
    164: "Joshua Dürksen",
    165: "Andrea-Kimi Antonelli",
    166: "Ritomo Miyata",
    167: "Rafael Villagómez",
    168: "Zak O'Sullivan",
    169: "Pepe Marti",
    170: "Sonny Hayes",
    171: "Joshua Pearce",
    172: "Callum Voisin",
    173: "Matias Zagazeta",
    174: "Nikola Tsolov",
    175: "Tim Tramnitz",
    185: "Luca Cortez",
    ## F1 26 DLC
    186: "Luke Browning",
    187: "Cian Shields",
    188: "Arvid Lindblad",
    189: "Dino Beganovic",
    190: "Leonardo Fornaroli",
    191: "Oliver Goethe",
    192: "Gabriele Mini",
    193: "Sebastián Montoya",
    194: "Alexander Dunne",
    195: "Max Esterson",
    196: "Sami Meguetounif",
    197: "John Bennett",
}

TRACK_IDS = {
    0: "Melbourne",
    2: "Shanghai",
    3: "Sakhir (Bahrain)",
    4: "Catalunya",
    5: "Monaco",
    6: "Montreal",
    7: "Silverstone",
    9: "Hungaroring",
    10: "Spa",
    11: "Monza",
    12: "Singapore",
    13: "Suzuka",
    14: "Abu Dhabi",
    15: "Texas",
    16: "Brazil",
    17: "Austria",
    19: "Mexico",
    20: "Baku (Azerbaijan)",
    26: "Zandvoort",
    27: "Imola",
    29: "Jeddah",
    30: "Miami",
    31: "Las Vegas",
    32: "Losail",
    39: "Silverstone (Reverse)",
    40: "Austria (Reverse)",
    41: "Zandvoort (Reverse)",
    ## F1 26 DLC
    42: "Madrid",
}

SESSION_TYPES = {
    0: "Unknown",
    1: "Practice 1",
    2: "Practice 2",
    3: "Practice 3",
    4: "Short Practice",
    5: "Qualifying 1",
    6: "Qualifying 2",
    7: "Qualifying 3",
    8: "Short Qualifying",
    9: "One-Shot Qualifying",
    10: "Sprint Shootout 1",
    11: "Sprint Shootout 2",
    12: "Sprint Shootout 3",
    13: "Short Sprint Shootout",
    14: "One-Shot Sprint Shootout",
    15: "Race",
    16: "Race 2",
    17: "Race 3",
    18: "Time Trial",
}

TYRE_COMPOUNDS_ACTUAL = {
    7: "Inter",
    8: "Wet",
    9: "Classic Dry",
    10: "Classic Wet",
    11: "F2 Super Soft",
    12: "F2 Soft",
    13: "F2 Medium",
    14: "F2 Hard",
    15: "F2 Wet",
    16: "C5",
    17: "C4",
    18: "C3",
    19: "C2",
    20: "C1",
    21: "C0",
    22: "C6"
}

TYRE_COMPOUNDS_VISUAL = {
    7: "Inter",
    8: "Wet",
    16: "Soft",
    17: "Medium",
    18: "Hard"
}

WEATHER_TYPES = {
    0: "Clear",
    1: "Light Cloud",
    2: "Overcast",
    3: "Light Rain",
    4: "Heavy Rain",
    5: "Storm"
}

ERS_DEPLOY_MODES = {
    0: "None",
    1: "Medium",
    2: "Hotlap",
    3: "Boost"
}

SAFETY_CAR_STATUS = {
    0: "None",
    1: "Full",
    2: "Virtual",
    3: "Formation Lap"
}

RESULT_STATUS = {
    0: "Invalid",
    1: "Inactive",
    2: "Active",
    3: "Finished",
    4: "Did Not Finish",
    5: "Disqualified",
    6: "Not Classified",
    7: "Retired"
}

DRIVER_STATUS = {
    0: "In Garage",
    1: "Flying Lap",
    2: "In Lap",
    3: "Out Lap",
    4: "On Track"
}

PIT_STATUS = {
    0: "None",
    1: "Pitting",
    2: "In Pit Area"
}

EVENT_CODES = {
    b"SSTA": "Session Started",
    b"SEND": "Session Ended",
    b"FTLP": "Fastest Lap",
    b"RTMT": "Retirement",
    b"DRSE": "DRS Enabled",
    b"DRSD": "DRS Disabled",
    b"TMPT": "Team Mate In Pit",
    b"CHQF": "Chequered Flag",
    b"RCWN": "Race Winner",
    b"PENA": "Penalty Issued",
    b"SPTP": "Speed Trap",
    b"STLG": "Start Lights",
    b"LGOT": "Lights Out",
    b"DTSV": "Drive Through Served",
    b"SGSV": "Stop Go Served",
    b"FLBK": "Flashback",
    b"BUTN": "Button Status",
    b"RDFL": "Red Flag",
    b"OVTK": "Overtake",
    b"SCAR": "Safety Car",
    b"COLL": "Collision"
}

class BufferReader:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def read(self, fmt: str) -> tuple:
        size = struct.calcsize(LITTLE_ENDIAN + fmt)
        if self.offset + size > len(self.data):
            raise ValueError("Not enough data in buffer")
        result = struct.unpack_from(LITTLE_ENDIAN + fmt, self.data, self.offset)
        self.offset += size
        return result
    
    def read_one(self, fmt: str) -> Any:
        return self.read(fmt)[0]
    
    def read_bytes(self, n: int) -> bytes:
        chunk = self.data[self.offset: self.offset + n]
        self.offset += n
        return chunk
    
    def remaining(self) -> int:
        return len(self.data) - self.offset

@dataclass
class PacketHeader:
    packet_format: int                  ## 2025/2026
    game_year: int                      ## 25/26
    game_major_version: int
    game_minor_version: int
    packet_version: int
    packet_id: int
    session_uid: int                    ## uint64
    session_time: float
    frame_identifier: int
    overall_frame_identifier: int
    player_car_index: int
    secondary_player_car_index: int     #255 = no second player

    @property
    def packet_name(self) -> str:
        return PacketID.NAMES.get(self.packet_id, f"Unknown ({self.packet_id})")

    @property
    def is_2026_format(self) -> bool:
        return self.packet_format >= 2026

HEADER_FMT = 'HBBBBBQfIIBB'
HEADER_SIZE = struct.calcsize(LITTLE_ENDIAN + HEADER_FMT)

def parse_header(buf: BufferReader) -> PacketHeader:
    (fmt, year, major, minor, pkt_ver, pkt_id, session_uid, session_time, frame_id, overall_frame_id, player_idx, secondary_idx) = buf.read(HEADER_FMT)
    return PacketHeader(
        packet_format=fmt,
        game_year=year,
        game_major_version=major,
        game_minor_version=minor,
        packet_version=pkt_ver,
        packet_id=pkt_id,
        session_uid=session_uid,
        session_time=session_time,
        frame_identifier=frame_id,
        overall_frame_identifier=overall_frame_id,
        player_car_index=player_idx,
        secondary_player_car_index=secondary_idx
    )

## PACKET 0 - Motion

@dataclass
class CarMotionData:
    world_position_x: float
    world_position_y: float
    world_position_z: float
    world_velocity_x: float
    world_velocity_y: float
    world_velocity_z: float
    world_forward_dir_x: int
    world_forward_dir_y: int
    world_forward_dir_z: int
    world_right_dir_x: int
    world_right_dir_y: int
    world_right_dir_z: int
    g_force_lateral: float
    g_force_longitudinal: float
    g_force_vertical: float
    yaw: float
    pitch: float
    roll: float

    @property
    def speed_ms(self) -> float:
        return (self.world_velocity_x ** 2 + self.world_velocity_y ** 2 + self.world_velocity_z ** 2) ** 0.5

CAR_MOTION_FMT = "ffffffhhhhhhffffff"

@dataclass
class PacketMotionData:
    header: PacketHeader
    car_motion_data: List[CarMotionData] 

## PACKET 1 - Session

@dataclass
class MarshalZone:
    zone_start: float ## Fraction 0..1 of way through the lap where the marshal zone starts
    zone_flag: int ## 0 = none, 1 = green, 2 = blue, 3 = yellow

    @property
    def flag_name(self) -> str:
        return {
            -1: "Unknown",
            0: "None",
            1: "Green",
            2: "Blue",
            3: "Yellow"
        }.get(self.zone_flag, "?")
    
@dataclass
class WeatherForecastSample:
    session_type: int
    time_offset: int ## minutes
    weather: int
    track_temperature: int
    track_temp_change: int ## 0=up, 1=down, 2=no change
    air_temperature: int
    air_temp_change: int ## 0=up, 1=down, 2=no change
    rain_percentage: int

    @property
    def weather_name(self) -> str:
        return WEATHER_TYPES.get(self.weather, "Unknown")

## F1 2026 DLC
@dataclass
class ActiveAeroZone:
    zone_start: float
    zone_end: float

## F1 2025
@dataclass
class DRSZone:
    zone_start: float
    zone_end: float

@dataclass
class PacketSessionData:
    header: PacketHeader
    weather: int
    track_temperature: int
    air_temperature: int
    total_laps: int
    track_length: int           ## in meters
    session_type: int
    track_id: int
    formula: int
    session_time_left: int      ## in seconds
    session_duration: int       ## in seconds
    pit_speed_limit: int        ## in km/h
    game_paused: int
    is_spectating: int
    spectator_car_index: int
    sli_pro_native_support: int
    num_marshal_zones: int
    marshal_zones: List[MarshalZone] ## 21 marshal zones max
    safety_car_status: int
    network_game: int
    num_weather_forecast_samples: int
    weather_forecast_samples: List[WeatherForecastSample] ## 64 samples max
    forecast_accuracy: int
    ai_difficulty: int          ## 0-110
    season_link_identifier: int
    weekend_link_identifier: int
    session_link_identifier: int
    pit_stop_window_ideal_lap: int
    pit_stop_window_latest_lap: int
    pit_stop_rejoin_position: int
    steering_assist: int
    braking_assist: int
    gearbox_assist: int
    pit_assist: int
    pit_release_assist: int
    ers_assist: int
    drs_assist: int
    dynamic_racing_line: int
    dynamic_racing_line_type: int
    game_mode: int
    rule_set: int
    time_of_day: int            ## minutes since midnight
    session_length: int         
    speed_units_lead_player: int
    speed_units_secondary_player: int
    temperature_units_secondary_player: int
    num_safety_car_periods: int
    num_virtual_safety_car_periods: int
    num_red_flags_periods: int
    equal_car_performance: int
    recovery_mode: int
    flashback_limit: int
    surface_type: int
    low_fuel_mode: int
    race_starts: int
    tyre_temperature: int
    pit_lane_tyre_sim: int
    car_damage: int
    car_damage_rate: int
    collisions: int
    collisions_off_for_first_lap_only: int
    mp_unsafe_pit_release: int
    mp_off_for_griefing: int
    corner_cutting_stringency: int
    parc_ferme_rules: int
    pit_stop_experience: int
    safety_car: int
    safety_car_experience: int
    formation_lap: int
    formation_lap_experience: int
    red_flags: int
    affects_licence_level_solo: int
    affects_licence_level_mp: int
    num_sessions_in_weekend: int
    weekend_structure: List[int]   # 12 entries
    sector2_lap_distance_start: float
    sector3_lap_distance_start: float
    ## F1 2026 DLC
    active_aero_track_status: Optional[int] = None
    num_active_aero_zones_full: Optional[int] = None
    active_aero_zones_full: List[ActiveAeroZone] = field(default_factory=list)
    num_active_aero_zones_partial: Optional[int] = None
    active_aero_zones_partial: List[ActiveAeroZone] = field(default_factory=list)
    num_drs_zones: Optional[int] = None
    drs_zones: List[DRSZone] = field(default_factory=list)
    start_reaction_time: Optional[float] = None
    anti_lock_brakes_assist: Optional[int] = None
    traction_control_assist: Optional[int] = None
    dynamic_racing_line_hi_vis: Optional[int] = None
    dynamic_racing_line_colour_blind: Optional[int] = None
    recurring_rewind_prompt: Optional[int] = None

    @property
    def track_name(self) -> str:
        return TRACK_IDS.get(self.track_id, f"Unknown ({self.track_id})")
    
    @property
    def session_type_name(self) -> str:
        return SESSION_TYPES.get(self.session_type, "Unknown")
    
    @property
    def weather_name(self) -> str:
        return WEATHER_TYPES.get(self.weather, "Unknown")
    
    @property
    def safety_car_status_name(self) -> str:
        return SAFETY_CAR_STATUS.get(self.safety_car_status, "Unknown")

## PACKET 2 - Lap Data

@dataclass
class LapData:
    last_lap_time_ms: int
    current_lap_time_ms: int
    sector1_time_ms_part: int
    sector1_time_minutes_part: int
    sector2_time_ms_part: int
    sector2_time_minutes_part: int
    delta_to_car_in_front_ms_part: int
    delta_to_car_in_front_minutes_part: int
    delta_to_race_leader_ms_part: int
    delta_to_race_leader_minutes_part: int
    lap_distance: float
    total_distance: float
    safety_car_delta: float
    car_position: int
    current_lap_num: int
    pit_status: int
    num_pit_stops: int
    sector: int         ## 0=sector 1, 1=sector 2, 2=sector 3
    current_lap_invalid: int
    penalties: int      ## seconds
    total_warnings: int
    corner_cutting_warnings: int
    num_unserved_drive_through_pens: int
    num_unserved_stop_go_pens: int
    grid_position: int
    driver_status: int
    result_status: int
    pit_lane_timer_active: int
    pit_lane_time_in_lane_ms: int
    pit_stop_timer_ms: int
    pit_stop_should_serve_pen: int
    speed_trap_fastest_speed: float
    speed_trap_fastest_lap: int

    @property
    def last_lap_time(self) -> str:
        return _ms_to_time_str(self.last_lap_time_ms)
    
    @property
    def current_lap_time(self) -> str:
        return _ms_to_time_str(self.current_lap_time_ms)
    
    @property
    def sector1_time(self) -> str:
        total_ms = self.sector1_time_minutes_part * 60000 + self.sector1_time_ms_part
        return _ms_to_time_str(total_ms)
    
    @property
    def sector2_time(self) -> str:
        total_ms = self.sector2_time_minutes_part * 60000 + self.sector2_time_ms_part
        return _ms_to_time_str(total_ms)
    
    @property
    def pit_status_name(self) -> str:
        return PIT_STATUS.get(self.pit_status, "Unknown")
    
    @property
    def driver_status_name(self) -> str:
        return DRIVER_STATUS.get(self.driver_status, "Unknown")
    
    @property
    def result_status_name(self) -> str:
        return RESULT_STATUS.get(self.result_status, "Unknown")

@dataclass
class PacketLapData:
    header: PacketHeader
    lap_data: List[LapData]
    time_trial_pb_car_idx: int
    time_trial_rival_car_idx: int

LAP_DATA_FMT = "IIHBHBHBHBfffBBBBBBBBBBBBBBBHHBfB"

## PACKET 3 - Event

@dataclass
class EventFastestLap:
    vehicle_idx: int
    lap_time_ms: float ## seconds

@dataclass
class EventRetirement:
    vehicle_idx: int
    reason: int

@dataclass
class EventDRSDisabled:
    reason:int ## 0=wet, 1=safety car, 2=red flag, 3=min lap not reached

@dataclass
class EventTeamMateInPits:
    vehicle_idx: int

@dataclass
class EventRaceWinner:
    vehicle_idx: int

@dataclass
class EventPenalty:
    penalty_type: int
    infringement_type: int
    vehicle_idx: int
    other_vehicle_idx: int
    time: int
    lap_num: int
    places_gained: int

@dataclass
class EventSpeedTrap:
    vehicle_idx: int
    speed: float
    is_overall_fastest: int
    is_drivers_fastest: int
    fastest_vehicle_idx: int
    fastest_speed: float

@dataclass
class EventStartLights:
    num_lights: int

@dataclass
class EventDriveThroughPenaltyServed:
    vehicle_idx: int

@dataclass
class EventStopGoPenaltyServed:
    vehicle_idx: int
    stop_time: int

@dataclass
class EventFlashback:
    flashback_frame_identifier: int
    flashback_session_time: float

@dataclass
class EventButtons:
    button_status: int

@dataclass
class EventOvertake:
    overtaking_vehicle_idx: int
    being_overtaken_vehicle_idx: int

@dataclass
class EventSafetyCar:
    safety_car_type: int ## 0=none, 1=full, 2=virtual, 3=formation lap
    event_type: int      ## 0=deployed, 1=returning, 2=returned, 3=resume

@dataclass
class EventCollision:
    vehicle1_idx: int
    vehicle2_idx: int

@dataclass
class PacketEventData:
    header: PacketHeader
    event_string_code: bytes
    event_details: Any

    @property
    def event_name(self) -> str:
        return EVENT_CODES.get(self.event_string_code, self.event_string_code.decode('ascii', errors='replace'))

## PACKET 4 - Participants

@dataclass
class LiveryColour:
    red: int
    green: int
    blue: int

@dataclass
class ParticipantData:
    ai_controlled: int
    driver_id: int              ## 255 = network human
    network_id: int
    team_id: int
    my_team: int
    race_number: int
    nationality: int
    name: str                   ## UTF-8, max 32 chars
    your_telemetry: int         ## 0 = restricted, 1 = public
    show_online_names: int
    tech_level: int
    platform: int               ## 1=Steam, 3=PS, 4=Xbox, 6=Origin, 255=Unknown
    num_colours: int
    livery_colours: List[LiveryColour] ## up to 4

    @property
    def team_name(self) -> str:
        return TEAM_IDS.get(self.team_id, f"Unknown ({self.team_id})")
    
    @property
    def is_human(self) -> bool:
        return self.ai_controlled == 0
    
@dataclass
class PacketParticipantsData:
    header: PacketHeader
    num_active_cars: int
    participants: List[ParticipantData]

## PACKET 5 - Car Setups

@dataclass
class CarSetupData:
    front_wing: int
    rear_wing: int
    on_throttle: int
    off_throttle: int
    front_camber: float
    rear_camber: float
    front_toe: float
    rear_toe: float
    front_suspension: int
    rear_suspension: int
    front_anti_roll_bar: int
    rear_anti_roll_bar: int
    front_suspension_height: int
    rear_suspension_height: int
    brake_pressure: int
    brake_bias: int
    engine_breaking: int
    rear_left_tyre_pressure: float
    rear_right_tyre_pressure: float
    front_left_tyre_pressure: float
    front_right_tyre_pressure: float
    ballast: int
    fuel_load: float

@dataclass
class PacketCarSetupData:
    header: PacketHeader
    car_setups: List[CarSetupData]
    next_front_wing_value: float

CAR_SETUP_FMT = "BBBBffffBBBBBBBBBffffBf"

## PACKET 6 - Car Telemetry

@dataclass
class CarTelemetryData:
    speed: int                          ## km/h
    throttle: float                     ## 0.0-1.0
    steer: float                        ## -1.0-1.0
    brake: float                        ## 0.0-1.0
    clutch: int                         ## 0-100
    gear: int                           ## -1 = R, 0 = N, 1-8 = forward gears
    engine_rpm: int
    drs: int                            ## 0 = off, 1 = on
    rev_lights_percent: int
    rev_lights_bit_value: int
    brakes_temperature: List[int]       ## 4 wheels
    tyres_surface_temperature: List[int] ## 4 wheels
    tyres_inner_temperature: List[int]  ## 4 wheels
    engine_temperature: int
    tyres_pressure: List[float]         ## 4 wheels
    surface_type: List[int]             ## 4 wheels

    @property
    def drs_active(self) -> bool:
        return self.drs == 1
    
    @property
    def speed_mph(self) -> float:
        return self.speed * 0.621371
    
@dataclass
class PacketCarTelemetryData:
    header: PacketHeader
    car_telemetry_data: List[CarTelemetryData]
    mfd_panel_index: int
    mfd_panel_index_secondary_player: int
    suggested_gear: int ## 0 = no suggestion

## PACKET 16 - Car Telemetry 2 (F1 2026 DLC)

@dataclass
class CarTelemetry2Data:
    active_aero_mode: int                   ## 0 = corner mode, 1 = straight mode
    active_aero_available: int              ## 0 = not available, 1 = available
    active_aero_activation_distance: int    ## 0 = unavailable, else metres to activation
    overtake_available: int                 ## 0 = not available, 1 = available
    overtake_active: int                    ## 0 = not active, 1 = active
    overtake_activation_distance: int       ## 0 = unavailable, else metres to activation
    regulations_2026: int                   ## 0 = 2025 regulations, 1 = 2026 regulations
    driving_wrong_way: int          

@dataclass
class PacketCarTelemetry2Data:
    header: PacketHeader
    car_telemetry_2_data: List[CarTelemetry2Data]

CAR_TELEMETRY_2_FMT = "BBHBBHBB"

## PACKET 7 - Car Status

@dataclass
class CarStatusData:
    traction_control: int               ## 0 = off, 1 = medium, 2 = full
    anti_lock_brakes: int
    fuel_mix: int                       ## 0 = lean, 1 = standard, 2 = rich, 3 = max
    front_brake_bias: int               ## 0-100 percentage
    pit_limiter_status: int
    fuel_in_tank: float
    fuel_capacity: float
    fuel_remaining_laps: float
    max_rpm: int
    idle_rpm: int
    max_gears: int
    drs_allowed: int
    drs_activation_distance: int        ## 0=unavailable, >0 = distance in metres to next activation
    actual_tyre_compound: int
    visual_tyre_compound: int
    tyres_age_laps: int
    vehicle_fia_flags: int              ## -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow
    engine_power_ice: float             ## W
    engine_power_mguk: float             ## W
    ers_store_energy: float             ## J
    ers_deploy_mode: int
    ers_harvested_this_lap_mguk: float
    ers_harvested_this_lap_mguh: float
    ers_deployed_this_lap: float
    network_paused: int
    ## F1 2026 DLC
    ers_harvest_limit_per_lap: Optional[int] = None

    @property
    def actual_tyre_name(self) -> str:
        return TYRE_COMPOUNDS_ACTUAL.get(self.actual_tyre_compound, f"Unknown ({self.actual_tyre_compound})")
    
    @property
    def visual_tyre_name(self) -> str:
        return TYRE_COMPOUNDS_VISUAL.get(self.visual_tyre_compound, f"Unknown ({self.visual_tyre_compound})")
    
    @property
    def ers_store_percent(self) -> float:
        return min(100.0, self.ers_store_energy / 4000000 * 100)
    
    @property
    def ers_deploy_mode_name(self) -> str:
        return ERS_DEPLOY_MODES.get(self.ers_deploy_mode, "Unknown")
    
@dataclass
class PacketCarStatusData:
    header: PacketHeader
    car_status_data: List[CarStatusData]


## PACKET 8 - Final Classification

@dataclass
class FinalClassificationData:
    position: int
    num_laps: int
    grid_position: int
    points: int
    num_pit_stops: int
    result_status: int
    result_reason: int
    best_lap_time_ms: int
    total_race_time: float ## seconds, no penalties
    penalties_time: float   ## seconds
    num_penalties: int
    num_tyre_stints: int
    tyre_stints_actual: List[int] ## up to 8 stints
    tyre_stints_visual: List[int] ## up to 8 stints
    tyre_stints_end_laps: List[int] ## up to 8 stints

    @property
    def best_lap_time(self) -> str:
        return _ms_to_time_str(self.best_lap_time_ms)
    
    @property
    def result_status_name(self) -> str:
        return RESULT_STATUS.get(self.result_status, "Unknown")
    
@dataclass
class PacketFinalClassificationData:
    header: PacketHeader
    num_cars: int
    classification_data: List[FinalClassificationData]

## PACKET 9 - Lobby Info

@dataclass
class LobbyInfoData:
    ai_controlled: int
    team_id: int
    nationality: int
    platform: int
    name: str
    car_number: int 
    your_telemetry: int
    show_online_names: int
    tech_level: int
    ready_status: int       ## 0=not ready, 1=ready, 2=spectating

@dataclass
class PacketLobbyInfoData:
    header: PacketHeader
    num_players: int
    lobby_players: List[LobbyInfoData]

## PACKET 10 - Car Damage

@dataclass
class CarDamageData:
    tyres_wear: List[float]           # [4] %
    tyres_damage: List[int]           # [4] %
    brakes_damage: List[int]          # [4] %
    tyre_blisters: List[int]          # [4] %
    front_left_wing_damage: int
    front_right_wing_damage: int
    rear_wing_damage: int
    floor_damage: int
    diffuser_damage: int
    sidepod_damage: int
    drs_fault: int
    ers_fault: int
    gear_box_damage: int
    engine_damage: int
    engine_mguh_wear: int
    engine_es_wear: int
    engine_ce_wear: int
    engine_ice_wear: int
    engine_mguk_wear: int
    engine_tc_wear: int
    engine_blown: int
    engine_seized: int

    @property
    def is_critical(self) -> bool:
        return (
            any(w > 80 for w in self.tyres_wear)
            or self.engine_damage > 80
            or self.gear_box_damage > 80
            or self.engine_blown == 1
            or self.engine_seized == 1
        )
    
@dataclass
class PacketCarDamageData:
    header: PacketHeader
    car_damage_data: List[CarDamageData]

## PACKET 11 - Session History

@dataclass
class LapHistoryData:
    lap_time_ms: int
    sector1_time_ms_part: int
    sector1_time_minutes_part: int
    sector2_time_ms_part: int
    sector2_time_minutes_part: int
    sector3_time_ms_part: int
    sector3_time_minutes_part: int
    lap_valid_bit_flags: int   # 0x01=lap,0x02=s1,0x04=s2,0x08=s3
 
    @property
    def lap_valid(self) -> bool:
        return bool(self.lap_valid_bit_flags & 0x01)
 
    @property
    def lap_time_str(self) -> str:
        return _ms_to_time_str(self.lap_time_ms)
 
    @property
    def sector1_time_total_ms(self) -> int:
        return self.sector1_time_minutes_part * 60000 + self.sector1_time_ms_part
 
    @property
    def sector2_time_total_ms(self) -> int:
        return self.sector2_time_minutes_part * 60000 + self.sector2_time_ms_part
 
    @property
    def sector3_time_total_ms(self) -> int:
        return self.sector3_time_minutes_part * 60000 + self.sector3_time_ms_part
    
@dataclass
class TyreStintHistoryData:
    end_lap: int            # 255 = current tyre
    tyre_actual_compound: int
    tyre_visual_compound: int

@dataclass
class PacketSessionHistoryData:
    header: PacketHeader
    car_idx: int
    num_laps: int
    num_tyre_stints: int
    best_lap_time_lap_num: int
    best_sector1_lap_num: int
    best_sector2_lap_num: int
    best_sector3_lap_num: int
    lap_history_data: List[LapHistoryData]          # up to 100
    tyre_stints_history_data: List[TyreStintHistoryData]  # up to 8

LAP_HISTORY_FMT = "IHBHBHBb"

## PACKET 12 - Tyre Sets

@dataclass
class TyreSetData:
    actual_tyre_compound: int
    visual_tyre_compound: int
    wear: int
    available: int
    recommended_session: int
    life_span: int         # laps remaining
    usable_life: int       # max recommended laps
    lap_delta_time: int    # ms vs fitted set
    fitted: int
 
    @property
    def actual_compound_name(self) -> str:
        return TYRE_COMPOUNDS_ACTUAL.get(self.actual_tyre_compound, f"Unknown({self.actual_tyre_compound})")
    
@dataclass
class PacketTyreSetsData:
    header: PacketHeader
    car_idx: int
    tyre_set_data: List[TyreSetData]   # 13 dry + 7 wet = 20
    fitted_idx: int

TYRE_SET_FMT = "BBBBBBBhB"

## PACKET 13 - Motion Ex

@dataclass
class PacketMotionExData:
    header: PacketHeader
    # All arrays: [0]=RL, [1]=RR, [2]=FL, [3]=FR
    suspension_position: List[float]
    suspension_velocity: List[float]
    suspension_acceleration: List[float]
    wheel_speed: List[float]
    wheel_slip_ratio: List[float]
    wheel_slip_angle: List[float]
    wheel_lat_force: List[float]
    wheel_long_force: List[float]
    height_of_cog_above_ground: float
    local_velocity_x: float
    local_velocity_y: float
    local_velocity_z: float
    angular_velocity_x: float
    angular_velocity_y: float
    angular_velocity_z: float
    angular_acceleration_x: float
    angular_acceleration_y: float
    angular_acceleration_z: float
    front_wheels_angle: float
    wheel_vert_force: List[float]
    front_aero_height: float
    rear_aero_height: float
    front_roll_angle: float
    rear_roll_angle: float
    chassis_yaw: float
    chassis_pitch: float
    wheel_camber: List[float]
    wheel_camber_gain: List[float]

## PACKET 14 - Time Trial

@dataclass
class TimeTrialDataSet:
    car_idx: int
    team_id: int
    lap_time_ms: int
    sector1_time_ms: int
    sector2_time_ms: int
    sector3_time_ms: int
    traction_control: int
    gearbox_assist: int
    anti_lock_brakes: int
    equal_car_performance: int
    custom_setup: int
    valid: int
 
    @property
    def lap_time_str(self) -> str:
        return _ms_to_time_str(self.lap_time_ms)
    
@dataclass
class PacketTimeTrialData:
    header: PacketHeader
    player_session_best: TimeTrialDataSet
    personal_best: TimeTrialDataSet
    rival: TimeTrialDataSet

## PACKET 15 - Lap Positions

@dataclass
class PacketLapPositionsData:
    header: PacketHeader
    num_laps: int
    lap_start: int       # 0-indexed
    positions: List[List[int]]  # [lap][vehicle_idx], 0 = no record

## UTILITY HELPERS

def _ms_to_time_str(ms: int) -> str:
    if ms <= 0:
        return "--:--.---"
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{minutes}:{seconds:02d}.{millis:03d}"