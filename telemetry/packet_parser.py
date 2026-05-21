"""
Packet Parser

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
from typing import Optional, List, Tuple, Any

## Constants

PACKET_FORMAT = 2025
MAX_CARS = 22
LITTLE_ENDIAN = '<' ## F1 telemetry data is little-endian

## Packet ID Enum
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
        15: "Lap Positions"
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
    194: "Sauber '24"
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
    185: "Luca Cortez"
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
    41: "Zandvoort (Reverse)"
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
    3: "Overtake"
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
    b"DTST": "Drive Through Served",
    b"SGSV": "Stop Go Served",
    b"FLBK": "Flashback",
    b"BUTN": "Button Status",
    b"RDFL": "Red Flag",
    b"OVTK": "Overtake",
    b"SCAR": "Safety Car",
    b"COLL": "Collision"
}

## Buffer Reader Class

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
    
## Packet Header

@dataclass
class PacketHeader:
    packet_format: int                  ## 2025
    game_year: int                      ## 25
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

    ## Convenience
    @property
    def packet_name(self) -> str:
        return PacketID.NAMES.get(self.packet_id, f"Unknown ({self.packet_id})")
    
## Header Format: H B B B B B Q f I I B B
## H=uint16, B=uint8, Q=uint64, f=float, I=uint32
HEADER_FMT = 'HBBBBBBQfIIBB'
HEADER_SIZE = struct.calcsize(LITTLE_ENDIAN + HEADER_FMT) ## 29 Bytes

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

## Packet 0 - Motion

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

CAR_MOTION_FMT = "fff fff hhhhhh fff fff"
CAR_MOTION_FMT_CLEAN = "ffffffhhhhhhffffff" ## 6 floats, 6 shorts, 6 floats

@dataclass
class PacketMotionData:
    header: PacketHeader
    car_motion_data: List[CarMotionData] 

def parse_car_motion(buf: BufferReader) -> CarMotionData:
    vals = buf.read("ffffffhhhhhhffffff")
    return CarMotionData(*vals)

def parse_motion_packet(header: PacketHeader, buf: BufferReader) -> PacketMotionData:
    cars = [parse_car_motion(buf) for _ in range(MAX_CARS)]
    return PacketMotionData(header=header, car_motion_data=cars)

## Packet 1 - Session

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
    
def parse_session_packet(header: PacketHeader, buf: BufferReader) -> PacketSessionData:
    (weather,
     track_temp,
     air_temp,
     total_laps,
     track_length,
     session_type,
     track_id,
     formula,
     time_left,
     duration,
     pit_speed,
     game_paused,
     is_spectating,
     spectator_idx,
     sli_pro,
     num_marshal) = buf.read("BbbBHBbBHHHBBBBB")
    
    marshal_zones = []
    for _ in range(21):
        zs, zf = buf.read("fb")
        marshal_zones.append(MarshalZone(zone_start=zs, zone_flag=zf))
    
    (safety_car_status, network_game, num_weather) = buf.read("BBB")

    weather_samples = []
    for _ in range(64):
        vals = buf.read("BBBbbbBB")
        weather_samples.append(WeatherForecastSample(*vals))

    (forecast_accuracy, ai_difficulty,
     season_link, weekend_link, session_link,
     pit_ideal, pit_latest, pit_rejoin,
     steer_assist, brake_assist, gearbox_assist, pit_assist,
     pit_release, ers_assist, drs_assist, dyn_line,
     dyn_line_type, game_mode, rule_set, time_of_day,
     session_length, speed_lead, temp_lead,
     speed_sec, temp_sec, num_sc, num_vsc, num_rf,
     equal_perf, recovery, flashback_lim, surface,
     low_fuel, race_starts, tyre_temp, pit_tyre, car_dmg,
     car_dmg_rate, collisions, coll_first, mp_unsafe, mp_grief,
     corner_cut, parc_ferme, pit_exp, sc, sc_exp, form_lap, form_exp,
     red_flags, aff_solo, aff_mp) = buf.read("BBIIIBBBBBBBBBBBBBBIBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB")
    
    num_sessions_in_weekend = buf.read_one("B")
    weekend_structure = list(buf.read("12B"))

    sector2_dist, sector3_dist = buf.read("ff")

    return PacketSessionData(
        header=header,
        weather=weather, track_temperature=track_temp, air_temperature=air_temp,
        total_laps=total_laps, track_length=track_length, session_type=session_type,
        track_id=track_id, formula=formula,
        session_time_left=time_left, session_duration=duration,
        pit_speed_limit=pit_speed, game_paused=game_paused,
        is_spectating=is_spectating, spectator_car_index=spectator_idx,
        sli_pro_native_support=sli_pro, num_marshal_zones=num_marshal,
        marshal_zones=marshal_zones, safety_car_status=safety_car_status,
        network_game=network_game,
        num_weather_forecast_samples=num_weather,
        weather_forecast_samples=weather_samples,
        forecast_accuracy=forecast_accuracy, ai_difficulty=ai_difficulty,
        season_link_identifier=season_link, weekend_link_identifier=weekend_link,
        session_link_identifier=session_link,
        pit_stop_window_ideal_lap=pit_ideal, pit_stop_window_latest_lap=pit_latest,
        pit_stop_rejoin_position=pit_rejoin,
        steering_assist=steer_assist, braking_assist=brake_assist,
        gearbox_assist=gearbox_assist, pit_assist=pit_assist,
        pit_release_assist=pit_release, ers_assist=ers_assist, drs_assist=drs_assist,
        dynamic_racing_line=dyn_line, dynamic_racing_line_type=dyn_line_type,
        game_mode=game_mode, rule_set=rule_set, time_of_day=time_of_day,
        session_length=session_length,
        speed_units_lead_player=speed_lead, temperature_units_lead_player=temp_lead,
        speed_units_secondary_player=speed_sec, temperature_units_secondary_player=temp_sec,
        num_safety_car_periods=num_sc, num_virtual_safety_car_periods=num_vsc,
        num_red_flag_periods=num_rf,
        equal_car_performance=equal_perf, recovery_mode=recovery,
        flashback_limit=flashback_lim, surface_type=surface,
        low_fuel_mode=low_fuel, race_starts=race_starts,
        tyre_temperature=tyre_temp, pit_lane_tyre_sim=pit_tyre,
        car_damage=car_dmg, car_damage_rate=car_dmg_rate,
        collisions=collisions, collisions_off_for_first_lap_only=coll_first,
        mp_unsafe_pit_release=mp_unsafe, mp_off_for_griefing=mp_grief,
        corner_cutting_stringency=corner_cut, parc_ferme_rules=parc_ferme,
        pit_stop_experience=pit_exp, safety_car=sc, safety_car_experience=sc_exp,
        formation_lap=form_lap, formation_lap_experience=form_exp,
        red_flags=red_flags, affects_licence_level_solo=aff_solo,
        affects_licence_level_mp=aff_mp,
        num_sessions_in_weekend=num_sessions_in_weekend,
        weekend_structure=weekend_structure,
        sector2_lap_distance_start=sector2_dist,
        sector3_lap_distance_start=sector3_dist
    )

## Packet 2 - Lap Data

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

LAP_DATA_FMT = "IIHBHBHBHBfffBBBBBBBBBBBBBBHHBfB"

def parse_lap_data(buf: BufferReader) -> LapData:
    vals = buf.read(LAP_DATA_FMT)
    return LapData(*vals)

def parse_lap_data_packet(header: PacketHeader, buf: BufferReader) -> PacketLapData:
    laps = [parse_lap_data(buf) for _ in range(MAX_CARS)]
    pb_idx, rival_idx = buf.read_one("BB")
    return PacketLapData(header=header, lap_data=laps,
                         time_trial_pb_car_idx=pb_idx,
                         time_trial_rival_car_idx=rival_idx)

## Packet 3 - Event

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
    event_data: Any

    @property
    def event_name(self) -> str:
        return EVENT_CODES.get(self.event_string_code, self.event_string_code.decode('ascii', errors='replace'))
    
def parse_event_packet(header: PacketHeader, buf: BufferReader) -> PacketEventData:
    code = buf.read_bytes(4)
    details = None
    if code == b"FTLP":
        idx, lap = buf.read("Bf")
        details = EventFastestLap(vehicle_idx=idx, lap_time_ms=lap)
    elif code == b"RTMT":
        idx, reason = buf.read("BB")
        details = EventRetirement(vehicle_idx=idx, reason=reason)
    elif code == b"DRSD":
        reason = buf.read_one("B")
        details = EventDRSDisabled(reason=reason)
    elif code == b"TMPT":
        idx = buf.read_one("B")
        details = EventTeamMateInPits(vehicle_idx=idx)
    elif code == b"RCWN":
        idx = buf.read_one("B")
        details = EventRaceWinner(vehicle_idx=idx)
    elif code == b"PENA":
        vals = buf.read("BBBBBBB")
        details = EventPenalty(*vals)
    elif code == b"SPTP":
        vals = buf.read("BfBBBf")
        details = EventSpeedTrap(*vals)
    elif code == b"STLG":
        n = buf.read_one("B")
        details = EventStartLights(num_lights=n)
    elif code == b"DTSV":
        idx = buf.read_one("B")
        details = EventDriveThroughPenaltyServed(vehicle_idx=idx)
    elif code == b"SGSV":
        idx = buf.read_one("B")
        stop_time = buf.read_one("f")
        details = EventStopGoPenaltyServed(vehicle_idx=idx, stop_time=stop_time)
    elif code == b"FLBK":
        fid, ft = buf.read("If")
        details = EventFlashback(flashback_frame_identifier=fid, flashback_session_time=ft)
    elif code == b"BUTN":
        bs = buf.read_one("I")
        details = EventButtons(button_status=bs)
    elif code == b"OVTK":
        ov, bov = buf.read("BB")
        details = EventOvertake(overtaking_vehicle_idx=ov, being_overtaken_vehicle_idx=bov)
    elif code == b"SCAR":
        sc_type, ev_type = buf.read("BB")
        details = EventSafetyCar(safety_car_type=sc_type, event_type=ev_type)
    elif code == b"COLL":
        v1, v2 = buf.read("BB")
        details = EventCollision(vehicle1_idx=v1, vehicle2_idx=v2)
    
    return PacketEventData(header=header, event_string_code=code, event_details=details)

## Packet 4 - Participants

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

def parse_participant(buf: BufferReader) -> ParticipantData:
    (ai, driver_id, network_id, team_id, my_team, race_num, nationality) = buf.read("BBBBBBB")
    raw_name = buf.read_bytes(32)
    name = raw_name.split(b"\x00", 1)[0].decode('utf-8', errors='replace')
    (your_tel, show_online, tech_level, platform, num_colours) = buf.read("BBHBB")
    colours = []
    for _ in range(4):
        r, g, b = buf.read("BBB")
        colours.append(LiveryColour(red=r, green=g, blue=b))
    return ParticipantData(
        ai_controlled=ai, driver_id=driver_id, network_id=network_id,
        team_id=team_id, my_team=my_team, race_number=race_num, nationality=nationality,
        name=name, your_telemetry=your_tel, show_online_names=show_online,
        tech_level=tech_level, platform=platform, num_colours=num_colours, livery_colours=colours)

def parse_participants_packet(header: PacketHeader, buf: BufferReader) -> PacketParticipantsData:
    num_active = buf.read_one("B")
    participants = [parse_participant(buf) for _ in range(MAX_CARS)]
    return PacketParticipantsData(header=header, num_active_cars=num_active, participants=participants)

## Packet 5 - Car Setups

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

def parse_car_setup(buf: BufferReader) -> CarSetupData:
    vals = buf.read(CAR_SETUP_FMT)
    return CarSetupData(*vals)

def parse_car_setup_packet(header: PacketHeader, buf: BufferReader) -> PacketCarSetupData:
    setups = [parse_car_setup(buf) for _ in range(MAX_CARS)]
    next_fw = buf.read_one("f")
    return PacketCarSetupData(header=header, car_setups=setups, next_front_wing_value=next_fw)

## Packet 6 - Car Telemetry

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

CAR_TELEMETRY_FMT = "HfffBhHBBH4H4B4BH4f4B"

def parse_car_telemetry(buf: BufferReader) -> CarTelemetryData:
    (speed, throttle, steer, brake, clutch, gear, rpm, drs, rev_pct, rev_bit) = buf.read("HfffBhHBBH")
    brakes_temp = list(buf.read("4H"))
    tyres_surf_temp = list(buf.read("4B")) 
    tyres_inner_temp = list(buf.read("4B"))
    engine_temp = buf.read_one("H")
    tyre_pressure = list(buf.read("4f"))
    surface_type = list(buf.read("4B"))

    return CarTelemetryData(
        speed=speed, throttle=throttle, steer=steer, brake=brake, clutch=clutch, gear=gear, engine_rpm=rpm,
        drs=drs, rev_lights_percent=rev_pct, rev_lights_bit_value=rev_bit, brakes_temperature=brakes_temp,
        tyres_surface_temperature=tyres_surf_temp, tyres_inner_temperature=tyres_inner_temp, engine_temperature=engine_temp,
        tyres_pressure=tyre_pressure, surface_type=surface_type
    )

def parse_car_telemetry_packet(header: PacketHeader, buf: BufferReader) -> PacketCarTelemetryData:
    cars = [parse_car_telemetry(buf) for _ in range(MAX_CARS)]
    mfd, mfd2, sug_gear = buf.read("BBb")
    return PacketCarTelemetryData(
        header=header, car_telemetry_data=cars,
        mfd_panel_index=mfd,
        mfd_panel_index_secondary_player=mfd2,
        suggested_gear=sug_gear,
    )

## Packet 7 - Car Status

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
    engine_power_ers: float             ## W
    ers_store_energy: float             ## J
    ers_deploy_mode: int
    ers_harvested_this_lap_mguk: float
    ers_harvested_this_lap_mguh: float
    ers_deployed_this_lap: float
    network_paused: int

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

CAR_STATUS_FMT = "BBBBBfffHHBBHBBBbfffifffB"

def parse_car_status(buf: BufferReader) -> CarStatusData:
    vals = buf.read(CAR_STATUS_FMT)
    return CarStatusData(*vals)

def parse_car_status_packet(header: PacketHeader, buf: BufferReader) -> PacketCarStatusData:
    cars = [parse_car_status(buf) for _ in range(MAX_CARS)]
    return PacketCarStatusData(header=header, car_status_data=cars)

## Packet 8 - Final Classification

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

def parse_final_classification(buf: BufferReader) -> FinalClassificationData:
    (pos, num_laps, grid, points, pits, res_status, res_reason, best_lap) = buf.read("BBBBBBBi")
    pass

def parse_final_classification_packet(header: PacketHeader, buf: BufferReader) -> FinalClassificationData:
    (pos, num_laps, grid, points, pits, res_status, res_reason) = buf.read("BBBBBBB")
    best_lap = buf.read_one("I")
    total_race_time = buf.read_one("d")
    pen_time, num_pens, num_stints = buf.read("BBB")
    actual = list(buf.read("8B"))
    visual = list(buf.read("8B"))
    end_laps = list(buf.read("8B"))
    return FinalClassificationData(
        position=pos, num_laps=num_laps, grid_position=grid, points=points, num_pit_stops=pits,
        result_status=res_status, result_reason=res_reason, best_lap_time_ms=best_lap,
        total_race_time=total_race_time, penalties_time=pen_time, num_penalties=num_pens, num_tyre_stints=num_stints,
        tyre_stints_actual=actual, tyre_stints_visual=visual, tyre_stints_end_laps=end_laps)

def parse_final_classification_packet(header: PacketHeader, buf: BufferReader) -> PacketFinalClassificationData:
    num_cars = buf.read_one("B")
    cars = [parse_final_classification(buf) for _ in range(MAX_CARS)]
    return PacketFinalClassificationData(header=header, num_cars=num_cars, classification_data=cars)

## Packet 9 - Lobby Info

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

def parse_lobby_info(buf: BufferReader) -> LobbyInfoData:
    ai, team_id, nationality, platform = buf.read ("BBBB")
    raw_name = buf.read_bytes(32)
    name = raw_name.split(b"\x00")[0].decode("utf-8", errors="replace")
    car_num, your_tel, show_online, tech_level, ready = buf.read("BBBBHB"[-5:])
    car_num, your_tel, show_online = buf.read("BBB")[:3] if False else (0,0,0)
    car_num = buf.read_one("B")
    your_tel = buf.read_one("B")
    show_online = buf.read_one("B")
    tech_level = buf.read_one("H")
    ready = buf.read_one("B")
    return LobbyInfoData(
        ai_controlled=ai, team_id=team_id, nationality=nationality, platform=platform, name=name,
        car_number=car_num, your_telemetry=your_tel, show_online_names=show_online,
        tech_level=tech_level, ready_status=ready
    )

def parse_lobby_info_packet(header: PacketHeader, buf: BufferReader) -> PacketLobbyInfoData:
    num_players = buf.read_one("B")
    players = [parse_lobby_info(buf) for _ in range(MAX_CARS)]
    return PacketLobbyInfoData(header=header, num_players=num_players, lobby_players=players)

## Packet 10 - Car Damage

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

def parse_car_damage(buf: BufferReader) -> CarDamageData:
    tyres_wear = list(buf.read("4f"))
    tyres_damage = list(buf.read("4B"))
    brakes_damage = list(buf.read("4B"))
    tyre_blisters = list(buf.read("4B"))
    (fl_wing, fr_wing, rear_wing, floor, diffuser,
     sidepod, drs_fault, ers_fault, gearbox, engine,
     mguh, es, ce, ice, mguk, tc, blown, seized) = buf.read("BBBBBBBBBBBBBBBBBB")
    
    return CarDamageData(
        tyres_wear=tyres_wear, tyres_damage=tyres_damage,
        brakes_damage=brakes_damage, tyre_blisters=tyre_blisters,
        front_left_wing_damage=fl_wing, front_right_wing_damage=fr_wing,
        rear_wing_damage=rear_wing, floor_damage=floor,
        diffuser_damage=diffuser, sidepod_damage=sidepod,
        drs_fault=drs_fault, ers_fault=ers_fault,
        gear_box_damage=gearbox, engine_damage=engine,
        engine_mguh_wear=mguh, engine_es_wear=es,
        engine_ce_wear=ce, engine_ice_wear=ice,
        engine_mguk_wear=mguk, engine_tc_wear=tc,
        engine_blown=blown, engine_seized=seized,
    )
 
 
def parse_car_damage_packet(header: PacketHeader, buf: BufferReader) -> PacketCarDamageData:
    cars = [parse_car_damage(buf) for _ in range(MAX_CARS)]
    return PacketCarDamageData(header=header, car_damage_data=cars)

## Packet 11 - Session History

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

def parse_session_history_packet(header: PacketHeader, buf: BufferReader) -> PacketSessionHistoryData:
    car_idx, num_laps, num_stints = buf.read("BBB")
    (best_lap, best_s1, best_s2, best_s3) = buf.read("BBBB")
 
    laps = []
    for _ in range(100):
        (lt, s1ms, s1min, s2ms, s2min, s3ms, s3min, flags) = buf.read("IHBHBHBb")
        laps.append(LapHistoryData(
            lap_time_ms=lt,
            sector1_time_ms_part=s1ms, sector1_time_minutes_part=s1min,
            sector2_time_ms_part=s2ms, sector2_time_minutes_part=s2min,
            sector3_time_ms_part=s3ms, sector3_time_minutes_part=s3min,
            lap_valid_bit_flags=flags,
        ))

    stints = []
    for _ in range(8):
        end, act, vis = buf.read("BBB")
        stints.append(TyreStintHistoryData(end_lap=end,
                                           tyre_actual_compound=act,
                                           tyre_visual_compound=vis))
 
    return PacketSessionHistoryData(
        header=header, car_idx=car_idx, num_laps=num_laps,
        num_tyre_stints=num_stints,
        best_lap_time_lap_num=best_lap,
        best_sector1_lap_num=best_s1, best_sector2_lap_num=best_s2,
        best_sector3_lap_num=best_s3,
        lap_history_data=laps, tyre_stints_history_data=stints,
    )

## Packet 12 - Tyre Sets

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

def parse_tyre_sets_packet(header: PacketHeader, buf: BufferReader) -> PacketTyreSetsData:
    car_idx = buf.read_one("B")
    sets = []
    for _ in range(20):
        act, vis, wear, avail, rec, life, usable, delta, fitted = buf.read("BBBBBBBhB")
        sets.append(TyreSetData(
            actual_tyre_compound=act, visual_tyre_compound=vis,
            wear=wear, available=avail, recommended_session=rec,
            life_span=life, usable_life=usable, lap_delta_time=delta,
            fitted=fitted,
        ))
    fitted_idx = buf.read_one("B")
    return PacketTyreSetsData(header=header, car_idx=car_idx,
                              tyre_set_data=sets, fitted_idx=fitted_idx)

## Packet 13 - Motion Ex

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

def parse_motion_ex_packet(header: PacketHeader, buf: BufferReader) -> PacketMotionExData:
    susp_pos = list(buf.read("4f"))
    susp_vel = list(buf.read("4f"))
    susp_acc = list(buf.read("4f"))
    wheel_spd = list(buf.read("4f"))
    slip_ratio = list(buf.read("4f"))
    slip_angle = list(buf.read("4f"))
    lat_force = list(buf.read("4f"))
    long_force = list(buf.read("4f"))
    (h_cog, lv_x, lv_y, lv_z, av_x, av_y, av_z,
     aa_x, aa_y, aa_z, fw_angle) = buf.read("fffffffffff")
    vert_force = list(buf.read("4f"))
    (front_aero, rear_aero, front_roll, rear_roll,
     chassis_yaw, chassis_pitch) = buf.read("ffffff")
    wheel_camber = list(buf.read("4f"))
    wheel_camber_gain = list(buf.read("4f"))
    return PacketMotionExData(
        header=header,
        suspension_position=susp_pos, suspension_velocity=susp_vel,
        suspension_acceleration=susp_acc, wheel_speed=wheel_spd,
        wheel_slip_ratio=slip_ratio, wheel_slip_angle=slip_angle,
        wheel_lat_force=lat_force, wheel_long_force=long_force,
        height_of_cog_above_ground=h_cog,
        local_velocity_x=lv_x, local_velocity_y=lv_y, local_velocity_z=lv_z,
        angular_velocity_x=av_x, angular_velocity_y=av_y, angular_velocity_z=av_z,
        angular_acceleration_x=aa_x, angular_acceleration_y=aa_y, angular_acceleration_z=aa_z,
        front_wheels_angle=fw_angle, wheel_vert_force=vert_force,
        front_aero_height=front_aero, rear_aero_height=rear_aero,
        front_roll_angle=front_roll, rear_roll_angle=rear_roll,
        chassis_yaw=chassis_yaw, chassis_pitch=chassis_pitch,
        wheel_camber=wheel_camber, wheel_camber_gain=wheel_camber_gain,
    )

## Packet 14 - Time Trial

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

TIME_TRIAL_SET_FMT = "BBIIIIBBBBBB"

def parse_time_trial_set(buf: BufferReader) -> TimeTrialDataSet:
    vals = buf.read(TIME_TRIAL_SET_FMT)
    return TimeTrialDataSet(*vals)

def parse_time_trial_packet(header: PacketHeader, buf: BufferReader) -> PacketTimeTrialData:
    return PacketTimeTrialData(
        header=header,
        player_session_best=parse_time_trial_set(buf),
        personal_best=parse_time_trial_set(buf),
        rival=parse_time_trial_set(buf),
    )

## Packet 15 - Lap Positions

@dataclass
class PacketLapPositionsData:
    header: PacketHeader
    num_laps: int
    lap_start: int       # 0-indexed
    positions: List[List[int]]  # [lap][vehicle_idx], 0 = no record

def parse_lap_positions_packet(header: PacketHeader, buf: BufferReader) -> PacketLapPositionsData:
    num_laps, lap_start = buf.read("BB")
    positions = []
    for _ in range(50):
        row = list(buf.read(f"{MAX_CARS}B"))
        positions.append(row)
    return PacketLapPositionsData(header=header, num_laps=num_laps,
                                  lap_start=lap_start, positions=positions)

## Utility Helpers

def _ms_to_time_str(ms: int) -> str:
    if ms <= 0:
        return "--:--.---"
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{minutes}:{seconds:02d}.{millis:03d}"

## Main Dispatcher

class PacketParser:
    def __init__(self, validate_format: bool = True):
        self.validate_format = validate_format
        # Dispatch table: packet_id --> parser function
        self._parsers = {
            PacketID.MOTION:               parse_motion_packet,
            PacketID.SESSION:              parse_session_packet,
            PacketID.LAP_DATA:             parse_lap_data_packet,
            PacketID.EVENT:                parse_event_packet,
            PacketID.PARTICIPANTS:         parse_participants_packet,
            PacketID.CAR_SETUPS:           parse_car_setup_packet,
            PacketID.CAR_TELEMETRY:        parse_car_telemetry_packet,
            PacketID.CAR_STATUS:           parse_car_status_packet,
            PacketID.FINAL_CLASSIFICATION: parse_final_classification_packet,
            PacketID.LOBBY_INFO:           parse_lobby_info_packet,
            PacketID.CAR_DAMAGE:           parse_car_damage_packet,
            PacketID.SESSION_HISTORY:      parse_session_history_packet,
            PacketID.TYRE_SETS:            parse_tyre_sets_packet,
            PacketID.MOTION_EX:            parse_motion_ex_packet,
            PacketID.TIME_TRIAL:           parse_time_trial_packet,
            PacketID.LAP_POSITIONS:        parse_lap_positions_packet,
        }

        # Stats
        self.packets_parsed = 0
        self.packets_failed = 0
        self.packets_unknown = 0

    def parse(self, raw_data: bytes) -> Optional[Any]:
        if len(raw_data) < HEADER_SIZE:
            self.packets_failed += 1
            return None
        try:
            buf = BufferReader(raw_data)
            header = parse_header(buf)
 
            if self.validate_format and header.packet_format != PACKET_FORMAT:
                return None
 
            parser_fn = self._parsers.get(header.packet_id)
            if parser_fn is None:
                self.packets_unknown += 1
                return None
 
            packet = parser_fn(header, buf)
            self.packets_parsed += 1
            return packet
 
        except Exception as e:
            self.packets_failed += 1
            # Uncomment for debug:
            # import traceback; traceback.print_exc()
            return None
        
    def parse_header_only(self, raw_data: bytes) -> Optional[PacketHeader]:
        if len(raw_data) < HEADER_SIZE:
            return None
        try:
            buf = BufferReader(raw_data)
            return parse_header(buf)
        except Exception:
            return None
        
    @property
    def stats(self) -> dict:
        return {
            "parsed": self.packets_parsed,
            "failed": self.packets_failed,
            "unknown": self.packets_unknown,
            "total": self.packets_parsed + self.packets_failed + self.packets_unknown,
        }
    
    def reset_stats(self):
        self.packets_parsed = 0
        self.packets_failed = 0
        self.packets_unknown = 0