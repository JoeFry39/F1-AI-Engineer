import time
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

## Import all the packet dataclasses from the parser
from packet_parser import (
    PacketID,
    PacketHeader,
    PacketMotionData,
    PacketSessionData,
    PacketLapData,
    PacketEventData,
    PacketParticipantsData,
    PacketCarSetupData,
    PacketCarTelemetryData,
    PacketCarStatusData,
    PacketFinalClassificationData,
    PacketCarDamageData,
    PacketSessionHistoryData,
    PacketTyreSetsData,
    PacketMotionExData,
    PacketTimeTrialData,
    PacketLapPositionsData,
    PacketLobbyInfoData,
    ## Individual sub-dataclasses
    LapData,
    CarTelemetryData,
    CarStatusData,
    CarDamageData,
    CarMotionData,
    LapHistoryData,
    TyreStintHistoryData,
    TyreSetData,
    ParticipantData,
    CarSetupData,
    TRACK_IDS,
    SESSION_TYPES,
    WEATHER_TYPES,
    TYRE_COMPOUNDS_ACTUAL,
    TYRE_COMPOUNDS_VISUAL,
    ERS_DEPLOY_MODES,
    RESULT_STATUS,
    _ms_to_time_str
)

## SECTION 1: CarState

@dataclass
class CarState:
    vehicle_index: int ## which slot this car occupies (0-21)
    
    ## From Participant Packet (arrives every 5s)
    name: Optional[str] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    driver_id: Optional[int] = None
    race_number: Optional[int] = None
    nationality: Optional[int] = None
    is_ai: Optional[bool] = None
    is_player: bool = None
    participants_ts: Optional[float] = None

    ## From Lap Data Packet (arrives every frame)
    car_position: Optional[int] = None
    current_lap_num: Optional[int] = None
    last_lap_time_ms: Optional[int] = None
    current_lap_time_ms: Optional[int] = None
    sector1_time_ms: Optional[int] = None
    sector2_time_ms: Optional[int] = None
    lap_distance: Optional[float] = None
    total_distance: Optional[float] = None
    pit_status: Optional[int] = None
    num_pit_stops: Optional[int] = None
    sector: Optional[int] = None
    current_lap_invalid: Optional[bool] = None
    penalties_seconds: Optional[int] = None
    grid_postion: Optional[int] = None
    driver_status: Optional[int] = None
    result_status: Optional[int] = None
    speed_trap_fastest_speed: Optional[float] = None
    delta_to_car_in_front_ms: Optional[int] = None
    delta_to_race_leader_ms: Optional[int] = None
    lap_data_ts: Optional[float] = None

    ## From Car Telemetry Packet (arrives every frame)
    speed_kph: Optional[int] = None
    throttle: Optional[float] = None
    brake: Optional[float] = None
    steer: Optional[float] = None
    clutch: Optional[int] = None
    gear: Optional[int] = None
    engine_rpm: Optional[int] = None
    drs: Optional[bool] = None
    rev_lights_percent: Optional[int] = None
    brakes_temperature: Optional[List[int]] = None
    tyres_surface_temp: Optional[List[int]] = None
    tyres_inner_temp: Optional[List[int]] = None
    engine_temperature: Optional[int] = None
    tyres_pressure: Optional[List[float]] = None
    telemetry_ts: Optional[float] = None

    ## From Car Status Packet (arrives every frame)
    tracktion_control: Optional[int] = None
    anti_lock_brakes: Optional[bool] = None
    fuel_mix: Optional[int] = None
    fuel_in_tank: Optional[float] = None
    fuel_capacity: Optional[float] = None
    fuel_remaining_laps: Optional[float] = None
    max_rpm: Optional[int] = None
    drs_allowed: Optional[bool] = None
    drs_activation_distance: Optional[int] = None
    actual_tyre_compound: Optional[int] = None
    visual_tyre_compound: Optional[int] = None
    tyres_age_laps: Optional[int] = None
    vehicle_fia_flags: Optional[int] = None
    engine_power_ice: Optional[float] = None
    engine_power_mguk: Optional[float] = None
    ers_store_energy: Optional[float] = None
    ers_deploy_mode: Optional[int] = None
    ers_harvested_lap_mguk: Optional[float] = None
    ers_harvested_lap_mguh: Optional[float] = None
    ers_deployed_lap: Optional[float] = None
    status_ts: Optional[float] = None

    ## From Car Damage Packet (arrives every 10 seconds)
    tyres_wear: Optional[List[float]] = None
    tyres_damage: Optional[List[int]] = None
    brakes_damage: Optional[List[int]] = None
    tyre_blisters: Optional[List[int]] = None
    front_left_wing_damage: Optional[int] = None
    front_right_wing_damage: Optional[int] = None
    rear_wing_damage: Optional[int] = None
    floor_damage: Optional[int] = None
    diffuser_damage: Optional[int] = None
    engine_damage: Optional[int] = None
    gear_box_damage: Optional[int] = None
    drs_fault: Optional[bool] = None
    ers_fault: Optional[bool] = None
    engine_blown: Optional[bool] = None
    engine_seized: Optional[bool] = None
    damage_ts: Optional[float] = None

    ## From Motion Packet (arrives every frame)
    world_position_x: Optional[float] = None
    world_position_y: Optional[float] = None
    world_position_z: Optional[float] = None
    g_force_lateral: Optional[float] = None
    g_force_longitudinal: Optional[float] = None
    g_force_vertical: Optional[float] = None
    yaw: Optional[float] = None
    pitch: Optional[float] = None
    roll: Optional[float] = None
    motion_ts: Optional[float] = None

    ## Derived / Convenience Properties
    @property
    def is_active(self) -> bool:
        return self.result_status not in (None, 0, 1)
    
    @property
    def is_on_track(self) -> bool:
        return self.driver_status == 4
 
    @property
    def is_pitting(self) -> bool:
        return self.pit_status in (1, 2)
 
    @property
    def speed_mph(self) -> Optional[float]:
        if self.speed_kph is None:
            return None
        return self.speed_kph * 0.621371
 
    @property
    def ers_store_percent(self) -> Optional[float]:
        if self.ers_store_energy is None:
            return None
        return min(100.0, self.ers_store_energy / 4_000_000 * 100)
 
    @property
    def fuel_laps_remaining(self) -> Optional[float]:
        return self.fuel_remaining_laps
 
    @property
    def actual_tyre_name(self) -> str:
        return TYRE_COMPOUNDS_ACTUAL.get(self.actual_tyre_compound, "?")
 
    @property
    def visual_tyre_name(self) -> str:
        return TYRE_COMPOUNDS_VISUAL.get(self.visual_tyre_compound, "?")
 
    @property
    def ers_mode_name(self) -> str:
        return ERS_DEPLOY_MODES.get(self.ers_deploy_mode, "?")
 
    @property
    def last_lap_time_str(self) -> str:
        return _ms_to_time_str(self.last_lap_time_ms or 0)
 
    @property
    def current_lap_time_str(self) -> str:
        return _ms_to_time_str(self.current_lap_time_ms or 0)
 
    @property
    def max_tyre_wear(self) -> Optional[float]:
        if self.tyres_wear is None:
            return None
        return max(self.tyres_wear)
 
    @property
    def avg_brake_temp(self) -> Optional[float]:
        if self.brakes_temperature is None:
            return None
        return sum(self.brakes_temperature) / 4
 
    @property
    def has_critical_damage(self) -> bool:
        return (
            self.engine_blown is True
            or self.engine_seized is True
            or (self.engine_damage or 0) > 80
            or (self.gear_box_damage or 0) > 80
        )
    
## SECTION 2: SessionState

@dataclass
class SessionState:
    
    ## Core session identity
    track_id: Optional[int] = None
    track_name: Optional[str] = None
    session_type: Optional[int] = None
    session_type_name: Optional[str] = None
    formula: Optional[int] = None
    game_mode: Optional[int] = None
    rule_set: Optional[int] = None
 
    ## Session progress
    total_laps: Optional[int] = None
    track_length_m: Optional[int] = None
    session_time_left: Optional[int] = None
    session_duration: Optional[int] = None
 
    ## Conditions
    weather: Optional[int] = None
    weather_name: Optional[str] = None
    track_temperature: Optional[int] = None
    air_temperature: Optional[int] = None
    forecast_accuracy: Optional[int] = None
 
    ## Safety car
    safety_car_status: Optional[int] = None
    num_safety_car_periods: Optional[int] = None
    num_virtual_safety_car_periods: Optional[int] = None
    num_red_flag_periods: Optional[int] = None
 
    ## Pit strategy window (player)
    pit_stop_window_ideal_lap: Optional[int] = None
    pit_stop_window_latest_lap: Optional[int] = None
    pit_stop_rejoin_position: Optional[int] = None
    pit_speed_limit: Optional[int] = None
 
    ## Track sector distances
    sector2_distance_start: Optional[float] = None
    sector3_distance_start: Optional[float] = None
 
    ## Assists active
    steering_assist: Optional[int] = None
    braking_assist: Optional[int] = None
    gearbox_assist: Optional[int] = None
    ers_assist: Optional[int] = None
    drs_assist: Optional[int] = None
 
    ## Network
    network_game: Optional[bool] = None
    game_paused: Optional[bool] = None
 
    ## Session/weekend link IDs (for storage/replay)
    session_uid: Optional[int] = None
    session_link_id: Optional[int] = None
    weekend_link_id: Optional[int] = None
    season_link_id: Optional[int] = None
 
    ## Timestamp of last update
    session_ts: Optional[float] = None
 
    @property
    def is_race(self) -> bool:
        return self.session_type in (15, 16, 17)
 
    @property
    def is_qualifying(self) -> bool:
        return self.session_type in (5, 6, 7, 8, 9)
 
    @property
    def is_practice(self) -> bool:
        return self.session_type in (1, 2, 3, 4)
 
    @property
    def safety_car_deployed(self) -> bool:
        return self.safety_car_status in (1, 2, 3)
 
    @property
    def laps_remaining(self) -> Optional[int]:
        return self.total_laps
 
    @property
    def is_wet(self) -> bool:
        return self.weather in (3, 4, 5)
    
## SECTION 3: LapRecord

@dataclass
class LapRecord:
    lap_number: int
    lap_time_ms: int

    ## Sector Times
    sector1_time_ms: int = 0
    sector2_time_ms: int = 0
    sector3_time_ms: int = 0

    ## Validity
    lap_valid: bool = True
    sector1_valid: bool = True
    sector2_valid: bool = True
    sector3_valid: bool = True

    ## Tyre Data and End of Lap
    tyre_compound_actual: Optional[int] = None
    tyre_compound_visual: Optional[int] = None
    tyre_age_at_end: Optional[int] = None
    tyre_wear_at_end: Optional[List[float]] = None

    ## Fuel at Start of Lap
    fuel_at_lap_start: Optional[float] = None

    ## ERS Usage Over Lap
    ers_deployed: Optional[float] = None
    ers_harvested_mguk: Optional[float] = None
    ers_harvested_mguh: Optional[float] = None

    ## Pit Stop This Lap?
    pit_stop_this_lap: bool = False
    pit_stop_time_ms: Optional[int] = None

    ## Timestamp When Lap was Recorded
    recorded_at: float = field(default_factory=time.perf_counter)

    ## Convenience

    @property
    def lap_time_str(self) -> str:
        return _ms_to_time_str(self.lap_time_ms)
    
    @property
    def sector1_str(self) -> str:
        return _ms_to_time_str(self.sector1_time_ms)
    
    @property
    def sector2_str(self) -> str:
        return _ms_to_time_str(self.sector2_time_ms)
    
    @property
    def sector3_str(self) -> str:
        return _ms_to_time_str(self.sector3_time_ms)
    
    @property
    def tyre_name(self) -> str:
        return TYRE_COMPOUNDS_VISUAL.get(self.tyre_compound_visual, "?")
    
    @property
    def theoretical_best_ms(self) -> int:
        return self.sector1_time_ms + self.sector2_time_ms + self.sector3_time_ms
    
    def sector_delta_ms(self, other: "LapRecord", sector: int) -> int:
        times = {1: self.sector1_time_ms, 2: self.sector2_time_ms, 3: self.sector3_time_ms}
        other_times = {1: other.sector1_time_ms, 2: other.sector2_time_ms, 3: other.sector3_time_ms}
        return times[sector] - other_times[sector]
    
## SECTION 4: EventRecord

@dataclass
class EventRecord:
    event_code: str
    event_name: str
    session_time: float
    wall_time: float
    vehicle_idx: Optional[int] = None
    details: Optional[Any] = None

## SECTION 5: TelemetryState

class TelemetryState:
    
    MAX_EVENT_HISTORY = 50
    MAX_LAP_HISTORY = 100

    def __init__(self):
        ## 22 Car Slots
        self.cars: List[CarState] = [CarState(vehicle_index=i) for i in range(22)]

        ## Session Wide State
        self.session = SessionState()

        ## Player Identity
        self.player_index: int = 255
        self.secondary_play_index: int = 255

        ## Lap History For Players Car
        self.lap_history: List[LapRecord] = []

        ## Session History For All Cars
        self.session_history_raw: Dict[int, List[LapHistoryData]] = {}
        self.tyre_stint_history: Dict[int, List[TyreStintHistoryData]] = {}

        ## Per-Car Tyre Set Data
        self.tyre_sets: Dict[int, List[TyreSetData]] = {}
        self.tyre_sets_fitted_idx: Dict[int, int] = {}

        ## Per-Car Setup Data
        self.car_setups: Dict[int, CarSetupData] = {}
        self.next_front_wing_value: Optional[float] = None

        ## Event Log
        self.events: deque = deque(maxlen=self.MAX_EVENT_HISTORY)

        ## Final Classification
        self.classified: List[Any] = []
        self.classification_received: bool = False

        ## Lap Positions Chart Data
        self.lap_positions: Dict[int, Dict[int, int]] = {}

        ## Time Trial Data
        self.time_trial_session_best: Optional[Any] = None
        self.time_trial_personal_best: Optional[Any] = None
        self.time_trial_rival: Optional[Any] = None

        ## Packet Counters
        self._packet_counts: Dict[int, int] = {i:0 for i in range(16)}
        self._last_update_ts: float = 0.0
        self._session_started: bool = False

        ## Thread Safety
        self._lock = threading.RLock()
        
    def update(self, packet: Any) -> None:
        if packet is None:
            return
        
        with self._lock:
            ## Always Update Player Index From Header
            self._sync_player_index(packet.header)
            self._last_update_ts = time.perf_counter()

            pid = packet.header.packet_id
            self._packet_counts[pid] = self._packet_counts.get(pid, 0) + 1

            ## Dispatch Table - Maps Packet ID to Handler Method
            _dispatch = {
                PacketID.MOTION: self._handle_motion,
                PacketID.SESSION: self._handle_session,
                PacketID.LAP_DATA: self._handle_lap_data,
                PacketID.EVENT: self._handle_event,
                PacketID.PARTICIPANTS: self._handle_participants,
                PacketID.CAR_SETUPS: self._handle_car_setups,
                PacketID.CAR_TELEMETRY: self._handle_car_telemetry,
                PacketID.CAR_STATUS: self._handle_car_status,
                PacketID.FINAL_CLASSIFICATION: self._handle_final_classification,
                PacketID.CAR_DAMAGE: self._handle_car_damage,
                PacketID.SESSION_HISTORY: self._handle_session_history,
                PacketID.TYRE_SETS: self._handle_tyre_sets,
                PacketID.MOTION_EX: self._handle_motion_ex,
                PacketID.TIME_TRIAL: self._handle_time_trial,
                PacketID.LAP_POSITIONS: self._handle_lap_positions
            }

            handler = _dispatch.get(pid)
            if handler:
                handler(packet)

    def _sync_player_index(self, header: PacketHeader) -> None:
        new_idx = header.m_playerCarIndex if hasattr(header, 'm_PlayerCarIndex') else header.player_car_index
        sec_idx = header.secondary_player_car_index

        if new_idx != self.player_index and new_idx < 22:
            ## Player Index Changed
            if self.player_index < 22:
                self.cars[self.player_index].is_player = False
            self.player_index = new_idx
            self.cars[new_idx].is_player = True

        self.secondary_play_index = sec_idx

    ## SECTION 6: Packet Handlers

    def _handle_session(self, packet: PacketSessionData) -> None:
        s = self.session
        now = time.perf_counter()

        s.track_id = packet.track_id
        s.track_name = TRACK_IDS.get(packet.track_id, f"Unknown({packet.track_id})")
        s.session_type = packet.session_type
        s.session_type_name = SESSION_TYPES.get(packet.session_type, "Unknown")
        s.formula = packet.formula
        s.game_mode = packet.game_mode
        s.rule_set = packet.rule_set
        s.total_laps = packet.total_laps
        s.track_length_m = packet.track_length
        s.session_time_left = packet.session_time_left
        s.session_duration = packet.session_duration
        s.weather = packet.weather
        s.weather_name = WEATHER_TYPES.get(packet.weather, "Unknown")
        s.track_temperature = packet.track_temperature
        s.air_temperature = packet.air_temperature
        s.forecast_accuracy = packet.forecast_accuracy
        s.safety_car_status = packet.safety_car_status
        s.num_safety_car_periods = packet.num_safety_car_periods
        s.num_virtual_safety_car_periods = packet.num_virtual_safety_car_periods
        s.num_red_flag_periods = packet.num_red_flags_periods
        s.pit_stop_window_ideal_lap = packet.pit_stop_window_ideal_lap
        s.pit_stop_window_latest_lap = packet.pit_stop_window_latest_lap
        s.pit_stop_rejoin_position = packet.pit_stop_rejoin_position
        s.pit_speed_limit = packet.pit_speed_limit
        s.sector2_distance_start = packet.sector2_lap_distance_start
        s.sector3_distance_start = packet.sector3_lap_distance_start
        s.steering_assist = packet.steering_assist
        s.braking_assist = packet.braking_assist
        s.gearbox_assist = packet.gearbox_assist
        s.ers_assist = packet.ers_assist
        s.drs_assist = packet.drs_assist
        s.network_game = bool(packet.network_game)
        s.game_paused = bool(packet.game_paused)
        s.session_uid = packet.session_link_identifier
        s.weekend_link_id = packet.weekend_link_identifier
        s.season_link_id = packet.season_link_identifier
        s.session_ts = now

        if not self._session_started:
            self._session_started = True

    def _handle_lap_data(self, packet: PacketLapData) -> None:
        now = time.perf_counter()

        for i, ld in enumerate(packet.lap_data):
            car = self.cars[i]

            car.car_position = ld.car_position
            car.current_lap_num = ld.current_lap_num
            car.last_lap_time_ms = ld.last_lap_time_ms
            car.current_lap_time_ms = ld.current_lap_time_ms
            car.lap_distance = ld.lap_distance
            car.total_distance = ld.total_distance
            car.pit_status = ld.pit_status
            car.num_pit_stops = ld.num_pit_stops
            car.sector = ld.sector
            car.current_lap_invalid = bool(ld.current_lap_invalid)
            car.penalties_seconds = ld.penalties
            car.grid_postion = ld.grid_position
            car.driver_status = ld.driver_status
            car.result_status = ld.result_status
            car.speed_trap_fastest_speed = ld.speed_trap_fastest_speed

            ## Combine Minute + ms Parts Into Single ms Value
            car.sector1_time_ms = (
                ld.sector1_time_minutes_part * 60_000 + ld.sector1_time_ms_part
            )

            car.sector2_time_ms = (
                ld.sector2_time_minutes_part * 60_000 + ld.sector2_time_ms_part
            )

            car.delta_to_car_in_front_ms = (
                ld.delta_to_car_in_front_minutes_part * 60_000 + ld.delta_to_car_in_front_ms_part
            )

            car.delta_to_race_leader_ms = (
                ld.delta_to_race_leader_minutes_part * 60_000 + ld.delta_to_race_leader_ms_part
            )

            car.lap_data_ts = now

    def _handle_car_telemetry(self, packet: PacketCarTelemetryData) -> None:
        now = time.perf_counter()

        for i, ct in enumerate(packet.car_telemetry_data):
            car = self.cars[i]

            car.speed_kph = ct.speed
            car.throttle = ct.throttle
            car.brake = ct.brake
            car.steer = ct.steer
            car.clutch = ct.clutch
            car.gear = ct.gear
            car.engine_rpm = ct.engine_rpm
            car.drs = bool(ct.drs)
            car.rev_lights_percent = ct.rev_lights_percent
            car.brakes_temperature = ct.brakes_temperature
            car.tyres_surface_temp = ct.tyres_surface_temperature
            car.tyres_inner_temp = ct.tyres_inner_temperature
            car.engine_temperature = ct.engine_temperature
            car.tyres_pressure = ct.tyres_pressure
            car.telemetry_ts = now

    def _handle_car_status(self, packet: PacketCarStatusData) -> None:
        now = time.perf_counter()

        for i, cs in enumerate(packet.car_status_data):
            car = self.cars[i]
 
            car.traction_control = cs.traction_control
            car.anti_lock_brakes = bool(cs.anti_lock_brakes)
            car.fuel_mix = cs.fuel_mix
            car.front_brake_bias = cs.front_brake_bias if hasattr(cs, 'front_brake_bias') else None
            car.pit_limiter_status = cs.pit_limiter_status if hasattr(cs, 'pit_limiter_status') else None
            car.max_rpm = cs.max_rpm
            car.drs_allowed = bool(cs.drs_allowed)
            car.drs_activation_distance = cs.drs_activation_distance
            car.actual_tyre_compound = cs.actual_tyre_compound
            car.visual_tyre_compound = cs.visual_tyre_compound
            car.tyres_age_laps = cs.tyres_age_laps
            car.vehicle_fia_flags = cs.vehicle_fia_flags
            car.ers_deploy_mode = cs.ers_deploy_mode

            ## Only Store Restricted Fields If Non-Zero
            if cs.fuel_in_tank > 0:
                car.fuel_in_tank = cs.fuel_in_tank
            if cs.fuel_capacity > 0:
                car.fuel_capacity = cs.fuel_capacity
            if cs.fuel_remaining_laps != 0:
                car.fuel_remaining_laps = cs.fuel_remaining_laps
            if cs.ers_store_energy > 0:
                car.ers_store_energy = cs.ers_store_energy
            if cs.engine_power_ice > 0:
                car.engine_power_ice = cs.engine_power_ice
            if cs.engine_power_mguk > 0:
                car.engine_power_mguk = cs.engine_power_mguk

            car.ers_harvested_lap_mguk = cs.ers_harvested_this_lap_mguk
            car.ers_harvested_lap_mguh = cs.ers_harvested_this_lap_mguh
            car.ers_deployed_lap = cs.ers_deployed_this_lap
            car.status_ts = now

    def _handle_car_damage(self, packet: PacketCarDamageData) -> None:
        now = time.perf_counter()

        for i, cd in enumerate(packet.car_damage_data):
            car = self.cars[i]

            ## Store Tyre Wear If Non-Zero
            if any(w > 0 for w in cd.tyres_wear):
                car.tyres_wear = cd.tyres_wear
 
            car.tyres_damage = cd.tyres_damage
            car.brakes_damage = cd.brakes_damage
            car.tyre_blisters = cd.tyre_blisters
            car.front_left_wing_damage = cd.front_left_wing_damage
            car.front_right_wing_damage = cd.front_right_wing_damage
            car.rear_wing_damage = cd.rear_wing_damage
            car.floor_damage = cd.floor_damage
            car.diffuser_damage = cd.diffuser_damage
 
            ## Engine/Gearbox Damage Are Restricted
            if cd.engine_damage > 0 or car.engine_damage is None:
                car.engine_damage = cd.engine_damage
            if cd.gear_box_damage > 0 or car.gear_box_damage is None:
                car.gear_box_damage = cd.gear_box_damage
 
            car.drs_fault = bool(cd.drs_fault)
            car.ers_fault = bool(cd.ers_fault)
            car.engine_blown = bool(cd.engine_blown)
            car.engine_seized = bool(cd.engine_seized)
            car.damage_ts = now

    def _handle_motion(self, packet: PacketMotionData) -> None:
        now = time.perf_counter()

        for i, cm in enumerate(packet.car_motion_data):
            car = self.cars[i]

            car.world_position_x = cm.world_position_x
            car.world_position_y = cm.world_position_y
            car.world_position_z = cm.world_position_z
            car.g_force_lateral = cm.g_force_lateral
            car.g_force_longitudinal = cm.g_force_longitudinal
            car.g_force_vertical = cm.g_force_vertical
            car.yaw = cm.yaw
            car.pitch = cm.pitch
            car.roll = cm.roll
            car.motion_ts = now

    def _handle_participants(self, packet: PacketParticipantsData) -> None:
        now = time.perf_counter()

        for i, p in enumerate(packet.participants):
            car = self.cars[i]

            car.name = p.name
            car.team_id = p.team_id
            car.team_name = p.team_name
            car.driver_id = p.driver_id
            car.race_number = p.race_number
            car.nationality = p.nationality
            car.is_ai = bool(p.ai_controlled)
            car.is_player = (i == self.player_index)
            car.participants_ts = now

    def _handle_car_setups(self, packet: PacketCarSetupData) -> None:
        for i, setup in enumerate(packet.car_setups):
            self.car_setups[i] = setup
        self.next_front_wing_value = packet.next_front_wing_value

    def _handle_event(self, packet: PacketEventData) -> None:
        record = EventRecord(
            event_code = packet.event_string_code.decode("ascii", errors="replace").strip("\x00"),
            event_name = packet.event_name,
            session_time = packet.header.session_time,
            wall_time = time.perf_counter(),
            vehicle_idx = getattr(packet.event_details, "vehicle_idx", None),
            details = packet.event_details,
        )

        self.events.append(record)

        ## Handle Session Start/End Flags
        if packet.event_string_code == b"SSTA":
            self._session_started = True
        elif packet.event_string_code == b"SEND":
            self._session_started = False

    def _handle_session_history(self, packet: PacketSessionHistoryData) -> None:
        car_idx = packet.car_idx

        ## Store Raw History For All Cars
        self.session_history_raw[car_idx] = packet.lap_history_data[:packet.num_laps]
        self.tyre_stint_history[car_idx] = packet.tyre_stints_history_data[:packet.num_tyre_stints]

        ## Rebuild LapRecord List Only For Player Car
        if car_idx != self.player_index:
            return
        
        new_records = []
        for lap_num, lh in enumerate(packet.lap_history_data[:packet.num_laps], start=1):
            if lh.lap_time_ms == 0:
                continue

            record = LapRecord(
                lap_number = lap_num,
                lap_time_ms = lh.lap_time_ms,
                sector1_time_ms = lh.sector1_time_total_ms,
                sector2_time_ms = lh.sector2_time_total_ms,
                sector3_time_ms = lh.sector3_time_total_ms,
                lap_valid = lh.lap_valid,
                sector1_valid = bool(lh.lap_valid_bit_flags & 0x02),
                sector2_valid = bool(lh.lap_valid_bit_flags & 0x04),
                sector3_valid = bool(lh.lap_valid_bit_flags & 0x08),
            )

            ## Use Tyre Data From Current CarState
            player_car = self.card[car_idx]
            record.tyre_compound_actual = player_car.actual_tyre_compound
            record.tyre_compound_visual = player_car.visual_tyre_compound

            new_records.append(record)

        ## Replace History List
        self.lap_history = new_records[-self.MAX_LAP_HISTORY:]

    def _handle_tyre_sets(self, packet: PacketTyreSetsData) -> None:
        self.tyre_sets[packet.car_idx] = packet.tyre_set_data
        self.tyre_sets_fitted_idx[packet.car_idx] = packet.fitted_idx

    def _handle_motion_ex(self, packet: PacketMotionExData) -> None:
        ## Store On The Player Car As Raw Snapshot
        if self.player_index < 22:
            self.cars[self.player_index]._motion_ex = packet

    def _handle_final_classification(self, packet: PacketFinalClassificationData) -> None:
        self.classified = packet.classification_data[:packet.num_cars]
        self.classification_received = True

    def _handle_time_trial(self, packet: PacketTimeTrialData) -> None:
        self.time_trial_session_best = packet.player_session_best
        self.time_trial_personal_best = packet.personal_best
        self.time_trial_rival = packet.rival
    
    def _handle_lap_positions(self, packet: PacketLapPositionsData) -> None:
        for lap_offset in range(packet.num_laps):
            lap_number = packet.lap_start + lap_offset + 1
            self.lap_positions[lap_number] = {
                vehicle_idx: packet.positions[lap_offset][vehicle_idx]
                for vehicle_idx in range(22)
                if packet.positions[lap_offset][vehicle_idx] != 0
            }

    ## SECTION 7 - Public Read API

    @property
    def player(self) -> Optional[CarState]:
        if self.player_index < 22:
            return self.cars[self.player_index]
        return None
    
    @property
    def secondary_player(self) -> Optional[CarState]:
        if self.secondary_play_index < 22:
            return self.cars[self.secondary_play_index]
        return None
    
    @property
    def active_cars(self) -> List[CarState]:
        return [c for c in self.cars if c.is_active]
    
    def get_car_by_position(self, position: int) -> Optional[CarState]:
        for car in self.cars:
            if car.car_position == position:
                return car
        return None
        
    def get_cars_sorted_by_position(self) -> List[CarState]:
        known = [c for c in self.active_cars if c.car_position is not None]
        unknown = [c for c in self.active_cars if c.car_position is None]
        return sorted(known, key=lambda c: c.car_position) + unknown
    
    def get_player_lap_record(self, lap_number: int) -> Optional[LapRecord]:
        for record in self.lap_history:
            if record.lap_number == lap_number:
                return record
        return None
    
    def get_best_lap_record(self) -> Optional[LapRecord]:
        valid_laps = [r for r in self.lap_history if r.lap_valid and r.lap_time_ms > 0]
        if not valid_laps:
            return None
        return min(valid_laps, key=lambda r: r.lap_time_ms)
    
    def get_last_completed_lap(self) -> Optional[LapRecord]:
        if not self.lap_history:
            return None
        return self.lap_history[-1]
    
    def get_player_tyre_sets(self) -> Optional[List[TyreSetData]]:
        return self.tyre_sets.get(self.player_index)
    
    def get_player_fitted_tyre_set(self) -> Optional[TyreSetData]:
        sets = self.tyre_sets.get(self.player_index)
        fitted_idx = self.tyre_sets_fitted_idx.get(self.player_index)
        if sets is not None and fitted_idx is not None and fitted_idx < len(sets):
            return sets[fitted_idx]
        
        return None
    
    def get_recent_events(self, n: int = 5) -> List[EventRecord]:
        return list(self.events)[-n:]
    
    def get_events_by_code(self, code: str) -> List[EventRecord]:
        return [e for e in self.events if e.event_code == code]
    
    def get_car_lap_history(self, vehicle_idx: int) -> List[LapHistoryData]:
        return self.session_history_raw.get(vehicle_idx, [])
    
    def get_position_at_lap(self, vehicle_idx: int, lap_number: int) -> Optional[int]:
        lap_data = self.lap_positions.get(lap_number, {})
        return lap_data.get(vehicle_idx)
    
    ## SECTION 8: Computed Analytic Helpers

    def player_gap_to_leader(self) -> Optional[float]:
        p = self.player
        if p is None or p.delta_to_race_leader_ms is None:
            return None
        return p.delta_to_race_leader_ms / 1000.0
    
    def player_gap_to_car_ahead(self) -> Optional[float]:
        p = self.player
        if p is None or p.delta_to_car_in_front_ms is None:
            return None
        return p.delta_to_car_in_front_ms / 1000.0
    
    def player_sector_delta_vs_best(self, sector: int) -> Optional[int]:
        if sector not in (1, 2, 3):
            return None
        p = self.player
        if p is None:
            return None
        
        current_ms = {1: p.sector1_time_ms, 2: p.sector2_time_ms}.get(sector)
        if not current_ms:
            return None
        
        best_record = self.get_best_lap_record()
        if best_record is None:
            return None

        best_ms = {1: best_record.sector1_time_ms, 2: best_record.sector2_time_ms, 3: best_record.sector3_time_ms}.get(sector, 0)
        if best_ms == 0:
            return None
        
        return current_ms - best_ms
    
    def laps_remaining(self) -> Optional[int]:
        p = self.player
        if p is None or p.current_lap_num is None:
            return None
        if self.session.total_laps is None or self.session.total_laps == 0:
            return None
        return max(0, self.session.total_laps - p.current_lap_num)
    
    def is_drs_available_for_player(self) -> bool:
        p = self.player
        if p is None:
            return False
        return bool(p.drs_allowed and (p.drs_activation_distance or 0) > 0)
    
    ## SECTION 9: Diagnostics and State Inspection

    @property
    def is_live(self) -> bool:
        return (time.perf_counter() - self._last_update_ts) < 5.0
    
    @property
    def packet_counts(self) -> Dict[int, int]:
        return dict(self._packet_counts)
    
    def summary(self) -> str:
        p = self.player
        s = self.session

        if p is None:
            return "TelemetryState: no player data"
        
        parts = [
            f"Track={s.track_name or '?'}",
            f"Session={s.session_type_name or '?'}",
            f"Lap={p.current_lap_num or '?'}/{s.total_laps or '?'}",
            f"Pos={p.car_position or '?'}",
            f"Speed={p.speed_kph or 0}kph",
            f"Gear={p.gear}",
            f"Tyres={p.actual_tyre_name}({p.tyres_age_laps or 0}L)",
            f"Fuel={p.fuel_remaining_laps:.1f}L" if p.fuel_remaining_laps else "Fuel=?",
            f"ERS={p.ers_store_percent:.0f}%" if p.ers_store_percent is not None else "ERS=?",
        ]
        return " | ".join(parts)
    
    def reset(self) -> None:
        with self._lock:
            self.cars = [CarState(vehicle_index=i) for i in range(22)]
            self.session = SessionState()
            self.player_index = 255
            self.lap_history = []
            self.session_history_raw = {}
            self.tyre_stint_history = {}
            self.tyre_sets = {}
            self.tyre_sets_fitted_idx = {}
            self.car_setups = {}
            self.next_front_wing_value = None
            self.events = deque(maxlen=self.MAX_EVENT_HISTORY)
            self.classified = []
            self.classification_received = False
            self.lap_positions = {}
            self.time_trial_session_best = None
            self.time_trial_personal_best = None
            self.time_trial_rival = None
            self._packet_counts = {i: 0 for i in range(16)}
            self._last_update_ts = 0.0
            self._session_started = False

    def __repr__(self) -> str:
        return(
            f"TelemetryState("
            f"player_idx={self.player_index}, "
            f"active_cars={len(self.active_cars)}, "
            f"laps={len(self.lap_history)}, "
            f"events={len(self.events)}, "
            f"live={self.is_live}"
            f")"
        )