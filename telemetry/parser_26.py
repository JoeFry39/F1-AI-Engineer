from models import (
    BufferReader, PacketHeader,
    CarMotionData, PacketMotionData,
    MarshalZone, ActiveAeroZone, DRSZone, WeatherForecastSample, PacketSessionData,
    LAP_DATA_FMT, LapData, PacketLapData,
    EventFastestLap, EventRetirement, EventDRSDisabled, EventTeamMateInPits,
    EventRaceWinner, EventPenalty, EventSpeedTrap, EventStartLights,
    EventDriveThroughPenaltyServed, EventStopGoPenaltyServed, EventFlashback,
    EventButtons, EventOvertake, EventSafetyCar, EventCollision,
    PacketEventData,
    LiveryColour, ParticipantData, PacketParticipantsData,
    CAR_SETUP_FMT, CarSetupData, PacketCarSetupData,
    CarTelemetryData, PacketCarTelemetryData,
    CarTelemetry2Data, PacketCarTelemetry2Data, CAR_TELEMETRY_2_FMT,
    CarStatusData, PacketCarStatusData,
    FinalClassificationData, PacketFinalClassificationData,
    LobbyInfoData, PacketLobbyInfoData,
    CarDamageData, PacketCarDamageData,
    LAP_HISTORY_FMT, LapHistoryData, TyreStintHistoryData, PacketSessionHistoryData,
    TYRE_SET_FMT, TyreSetData, PacketTyreSetsData,
    PacketMotionExData,
    TimeTrialDataSet, PacketTimeTrialData,
    PacketLapPositionsData,
)

MAX_CARS = 24

CAR_MOTION_FMT = "ffffffhhhhhhhhhfff"

SESSION_HEAD_FMT = "BbbBHBbBHHBBBBBB"
SESSION_TAIL_FMT = "BBIIIBBBBBBBBBBBBBBIBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"

CAR_TELEMETRY_HEAD_FMT = "HfffBbHBBH"

CAR_STATUS_FMT = "BBBBBfffHHBBHBBBbfffBffffB"

PARTICIPANT_HEAD_FMT = "BHHHBBB"
PARTICIPANT_TAIL_FMT = "BBHBB"

LOBBY_HEAD_FMT = "BHBB"
LOBBY_TAIL_FMT = "BBBHB"

TIME_TRIAL_SET_FMT = "BHIIIIBBBBBB"

## PACKET 0 - Motion

def parse_car_motion(buf: BufferReader) -> CarMotionData:
    (wpx, wpy, wpz, wvx, wvy, wvz, fdx, fdy, fdz, rdx, rdy, rdz, g_lat_q, g_lon_q, g_vert_q, yaw, pitch, roll) = buf.read(CAR_MOTION_FMT)
    return CarMotionData(
        world_position_x = wpx, world_position_y = wpy, world_position_z = wpz,
        world_velocity_x = wvx, world_velocity_y = wvy, world_velocity_z = wvz,
        world_forward_dir_x = fdx, world_forward_dir_y = fdy, world_forward_dir_z = fdz,
        world_right_dir_x = rdx, world_right_dir_y = rdy, world_right_dir_z = rdz,
        g_force_lateral = g_lat_q / 1000.0,
        g_force_longitudinal = g_lon_q / 1000.0,
        g_force_vertical = g_vert_q / 1000.0,
        yaw = yaw, pitch = pitch, roll = roll,
    )

def parse_motion_packet(header: PacketHeader, buf: BufferReader) -> PacketMotionData:
    cars = [parse_car_motion(buf) for _ in range(MAX_CARS)]
    return PacketMotionData(header=header, car_motion_data=cars)

## PACKET 1 - Session

def parse_session_packet(header: PacketHeader, buf: BufferReader) -> PacketSessionData:
    (weather, track_temp, air_temp, total_laps, track_length, session_type,
     track_id, formula, time_left, duration, pit_speed, game_paused,
     is_spectating, spectator_idx, sli_pro, num_marshal) = buf.read(SESSION_HEAD_FMT)
    
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
     red_flags, aff_solo, aff_mp) = buf.read(SESSION_TAIL_FMT)
    
    num_sessions_in_weekend = buf.read_one("B")
    weekend_structure = list(buf.read("12B"))

    sector2_dist, sector3_dist = buf.read("ff")

    active_aero_track_status = buf.read_one("B")
    num_active_aero_zones_full = buf.read_one("B")
    active_aero_zones_full = []
    for _ in range(8):
        zs, ze = buf.read("ff")
        active_aero_zones_full.append(ActiveAeroZone(zone_start = zs, zone_end = ze))

    num_active_aero_zones_partial = buf.read_one("B")
    active_aero_zones_partial = []
    for _ in range(8):
        zs, ze = buf.read("ff")
        active_aero_zones_partial.append(ActiveAeroZone(zone_start = zs, zone_end = ze))

    num_drs_zones = buf.read_one("B")
    drs_zones = []
    for _ in range(4):
        zs, ze = buf.read("ff")
        drs_zones.append(DRSZone(zone_start = zs, zone_end = ze))

    start_reaction_time = buf.read_one("f")
    (anti_lock_brakes_assist, traction_control_assist,
     dynamic_racing_line_hi_vis, dynamic_racing_line_colour_blind,
     recurring_rewind_prompt) = buf.read("BBBBB")

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
        sector3_lap_distance_start=sector3_dist,
        active_aero_track_status=active_aero_track_status,
        num_active_aero_zones_partial=num_active_aero_zones_partial,
        active_aero_zones_partial=active_aero_zones_partial,
        num_drs_zones=num_drs_zones,
        drs_zones=drs_zones,
        start_reaction_time=start_reaction_time,
        anti_lock_brakes_assist=anti_lock_brakes_assist,
        traction_control_assist=traction_control_assist,
        dynamic_racing_line_hi_vis=dynamic_racing_line_hi_vis,
        dynamic_racing_line_colour_blind=dynamic_racing_line_colour_blind,
        recurring_rewind_prompt=recurring_rewind_prompt,
    )

## PACKET 2 - Lap Data

def parse_lap_data(buf: BufferReader) -> LapData:
    vals = buf.read(LAP_DATA_FMT)
    return LapData(*vals)

def parse_lap_data_packet(header: PacketHeader, buf: BufferReader) -> PacketLapData:
    laps = [parse_lap_data(buf) for _ in range(MAX_CARS)]
    pb_idx, rival_idx = buf.read_one("BB")
    return PacketLapData(header=header, lap_data=laps,
                         time_trial_pb_car_idx=pb_idx,
                         time_trial_rival_car_idx=rival_idx)

## PACKET 3 - Event

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
        v1, v2, severity = buf.read("BBB")
        details = EventCollision(vehicle1_idx=v1, vehicle2_idx=v2, severity=severity)
    
    return PacketEventData(header=header, event_string_code=code, event_details=details)

## PACKET 4 - Participants

def parse_participant(buf: BufferReader) -> ParticipantData:
    (ai, driver_id, network_id, team_id, my_team, race_num, nationality) = buf.read(PARTICIPANT_HEAD_FMT)
    raw_name = buf.read_bytes(32)
    name = raw_name.split(b"\x00", 1)[0].decode('utf-8', errors='replace')
    (your_tel, show_online, tech_level, platform, num_colours) = buf.read(PARTICIPANT_TAIL_FMT)
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

## PACKET 5 - Car Setups

def parse_car_setup(buf: BufferReader) -> CarSetupData:
    vals = buf.read(CAR_SETUP_FMT)
    return CarSetupData(*vals)

def parse_car_setup_packet(header: PacketHeader, buf: BufferReader) -> PacketCarSetupData:
    setups = [parse_car_setup(buf) for _ in range(MAX_CARS)]
    next_fw = buf.read_one("f")
    return PacketCarSetupData(header=header, car_setups=setups, next_front_wing_value=next_fw)

## PACKET 6 - Car Telemetry

def parse_car_telemetry(buf: BufferReader) -> CarTelemetryData:
    (speed, throttle, steer, brake, clutch, gear, rpm, drs, rev_pct, rev_bit) = buf.read(CAR_TELEMETRY_HEAD_FMT)
    brakes_temp = list(buf.read("4H"))
    tyres_surf_temp = list(buf.read("4B")) 
    tyres_inner_temp = list(buf.read("4B"))
    engine_temp = buf.read_one("B")
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

## PACKET 16 - Car Telemetry 2 (F1 2026 DLC)

def parse_car_telemetry_2(buf: BufferReader) -> CarTelemetry2Data:
    vals = buf.read(CAR_TELEMETRY_2_FMT)
    return CarTelemetry2Data(*vals)

def parse_car_telemetry_2_packet(header: PacketHeader, buf: BufferReader) -> PacketCarTelemetry2Data:
    cars = [parse_car_telemetry_2(buf) for _ in range(MAX_CARS)]
    return PacketCarTelemetry2Data(header=header, car_telemetry_2_data=cars)

## PACKET 7 - Car Status

def parse_car_status(buf: BufferReader) -> CarStatusData:
    vals = buf.read(CAR_STATUS_FMT)
    (traction_control, anti_lock_brakes, fuel_mix, front_brake_bias, pit_limiter_status,
     fuel_in_tank, fuel_capacity, fuel_remaining_laps,
     max_rpm, idle_rpm, max_gears, drs_allowed, drs_activation_distance,
     actual_tyre_compound, visual_tyre_compound, tyres_age_laps, vehicle_fia_flags,
     engine_power_ice, engine_power_mguk, ers_store_energy, ers_deploy_mode,
     ers_harvested_this_lap_mguk, ers_harvested_this_lap_mguh,
     ers_harvest_limit_per_lap, ers_deployed_this_lap,
     network_paused) = vals
    return CarStatusData(
        traction_control=traction_control, anti_lock_brakes=anti_lock_brakes, fuel_mix=fuel_mix,
        front_brake_bias=front_brake_bias, pit_limiter_status=pit_limiter_status,
        fuel_in_tank=fuel_in_tank, fuel_capacity=fuel_capacity, fuel_remaining_laps=fuel_remaining_laps,
        max_rpm=max_rpm, idle_rpm=idle_rpm, max_gears=max_gears, drs_allowed=drs_allowed,
        drs_activation_distance=drs_activation_distance,
        actual_tyre_compound=actual_tyre_compound, visual_tyre_compound=visual_tyre_compound,
        tyres_age_laps=tyres_age_laps, vehicle_fia_flags=vehicle_fia_flags,
        engine_power_ice=engine_power_ice, engine_power_mguk=engine_power_mguk,
        ers_store_energy=ers_store_energy, ers_deploy_mode=ers_deploy_mode,
        ers_harvested_this_lap_mguk=ers_harvested_this_lap_mguk,
        ers_harvested_this_lap_mguh=ers_harvested_this_lap_mguh,
        ers_harvest_limit_per_lap=ers_harvest_limit_per_lap,
        ers_deployed_this_lap=ers_deployed_this_lap, network_paused=network_paused,
    )
 
 
def parse_car_status_packet(header: PacketHeader, buf: BufferReader) -> PacketCarStatusData:
    cars = [parse_car_status(buf) for _ in range(MAX_CARS)]
    return PacketCarStatusData(header=header, car_status_data=cars)

## PACKET 8 - Final Classification

def parse_final_classification(buf: BufferReader) -> FinalClassificationData:
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

## PACKET 9 - Lobby Info

def parse_lobby_info(buf: BufferReader) -> LobbyInfoData:
    ai, team_id, nationality, platform = buf.read(LOBBY_HEAD_FMT)
    raw_name = buf.read_bytes(32)
    name = raw_name.split(b"\x00", 1)[0].decode("utf-8", errors="replace")
    car_num, your_tel, show_online, tech_level, ready = buf.read(LOBBY_TAIL_FMT)
    return LobbyInfoData(
        ai_controlled=ai, team_id=team_id, nationality=nationality, platform=platform, name=name,
        car_number=car_num, your_telemetry=your_tel, show_online_names=show_online,
        tech_level=tech_level, ready_status=ready
    )
 
 
def parse_lobby_info_packet(header: PacketHeader, buf: BufferReader) -> PacketLobbyInfoData:
    num_players = buf.read_one("B")
    players = [parse_lobby_info(buf) for _ in range(MAX_CARS)]
    return PacketLobbyInfoData(header=header, num_players=num_players, lobby_players=players)

## PACKET 10 - Car Damage

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

## PACKET 11 - Session History

def parse_session_history_packet(header: PacketHeader, buf: BufferReader) -> PacketSessionHistoryData:
    car_idx, num_laps, num_stints = buf.read("BBB")
    (best_lap, best_s1, best_s2, best_s3) = buf.read("BBBB")
 
    laps = []
    for _ in range(100):
        (lt, s1ms, s1min, s2ms, s2min, s3ms, s3min, flags) = buf.read(LAP_HISTORY_FMT)
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
        stints.append(TyreStintHistoryData(end_lap=end, tyre_actual_compound=act, tyre_visual_compound=vis))
 
    return PacketSessionHistoryData(
        header=header, car_idx=car_idx, num_laps=num_laps,
        num_tyre_stints=num_stints,
        best_lap_time_lap_num=best_lap,
        best_sector1_lap_num=best_s1, best_sector2_lap_num=best_s2,
        best_sector3_lap_num=best_s3,
        lap_history_data=laps, tyre_stints_history_data=stints,
    )

## PACKET 12 - Tyre Sets

def parse_tyre_sets_packet(header: PacketHeader, buf: BufferReader) -> PacketTyreSetsData:
    car_idx = buf.read_one("B")
    sets = []
    for _ in range(20):
        act, vis, wear, avail, rec, life, usable, delta, fitted = buf.read(TYRE_SET_FMT)
        sets.append(TyreSetData(
            actual_tyre_compound=act, visual_tyre_compound=vis,
            wear=wear, available=avail, recommended_session=rec,
            life_span=life, usable_life=usable, lap_delta_time=delta,
            fitted=fitted,
        ))
    fitted_idx = buf.read_one("B")
    return PacketTyreSetsData(header=header, car_idx=car_idx,
                               tyre_set_data=sets, fitted_idx=fitted_idx)

## PACKET 13 - Motion Ex

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

## PACKET 14 - Time Trial

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

## PACKET 15 - Lap Positions

def parse_lap_positions_packet(header: PacketHeader, buf: BufferReader) -> PacketLapPositionsData:
    num_laps, lap_start = buf.read("BB")
    positions = []
    for _ in range(50):
        row = list(buf.read(f"{MAX_CARS}B"))
        positions.append(row)
    return PacketLapPositionsData(header=header, num_laps=num_laps, lap_start=lap_start, positions=positions)