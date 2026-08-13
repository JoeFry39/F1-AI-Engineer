from typing import Optional, Any
import models
import parser_25
import parser_26
from models import BufferReader, PacketHeader, PacketID, HEADER_SIZE, parse_header

class PacketParser:
    def __init__(self, validate_format: bool = True):
        self.validate_format = validate_format
        # Dispatch table: packet_id --> parser function
        self._parsers_by_format = {
            models.PACKET_FORMAT_25: {
                PacketID.MOTION: parser_25.parse_motion_packet,
                PacketID.SESSION: parser_25.parse_session_packet,
                PacketID.LAP_DATA: parser_25.parse_lap_data_packet,
                PacketID.EVENT: parser_25.parse_event_packet,
                PacketID.PARTICIPANTS: parser_25.parse_participants_packet,
                PacketID.CAR_SETUPS: parser_25.parse_car_setup_packet,
                PacketID.CAR_TELEMETRY: parser_25.parse_car_telemetry_packet,
                PacketID.CAR_STATUS: parser_25.parse_car_status_packet,
                PacketID.FINAL_CLASSIFICATION: parser_25.parse_final_classification_packet,
                PacketID.LOBBY_INFO: parser_25.parse_lobby_info_packet,
                PacketID.CAR_DAMAGE: parser_25.parse_car_damage_packet,
                PacketID.SESSION_HISTORY: parser_25.parse_session_history_packet,
                PacketID.TYRE_SETS: parser_25.parse_tyre_sets_packet,
                PacketID.MOTION_EX: parser_25.parse_motion_ex_packet,
                PacketID.TIME_TRIAL: parser_25.parse_time_trial_packet,
                PacketID.LAP_POSITIONS: parser_25.parse_lap_positions_packet,
            },
            models.PACKET_FORMAT_26: {
                PacketID.MOTION: parser_26.parse_motion_packet,
                PacketID.SESSION: parser_26.parse_session_packet,
                PacketID.LAP_DATA: parser_26.parse_lap_data_packet,
                PacketID.EVENT: parser_26.parse_event_packet,
                PacketID.PARTICIPANTS: parser_26.parse_participants_packet,
                PacketID.CAR_SETUPS: parser_26.parse_car_setup_packet,
                PacketID.CAR_TELEMETRY: parser_26.parse_car_telemetry_packet,
                PacketID.CAR_STATUS: parser_26.parse_car_status_packet,
                PacketID.FINAL_CLASSIFICATION: parser_26.parse_final_classification_packet,
                PacketID.LOBBY_INFO: parser_26.parse_lobby_info_packet,
                PacketID.CAR_DAMAGE: parser_26.parse_car_damage_packet,
                PacketID.SESSION_HISTORY: parser_26.parse_session_history_packet,
                PacketID.TYRE_SETS: parser_26.parse_tyre_sets_packet,
                PacketID.MOTION_EX: parser_26.parse_motion_ex_packet,
                PacketID.TIME_TRIAL: parser_26.parse_time_trial_packet,
                PacketID.LAP_POSITIONS: parser_26.parse_lap_positions_packet,
                PacketID.CAR_TELEMETRY_2: parser_26.parse_car_telemetry_2_packet,
            },
        }

        self.packets_parsed = 0
        self.packets_failed = 0
        self.packets_unknown = 0
        self.packets_unknown_format = 0

    def parse(self, raw_data: bytes) -> Optional[Any]:
        if len(raw_data) < HEADER_SIZE:
            self.packets_failed += 1
            return None
        try:
            buf = BufferReader(raw_data)
            header = parse_header(buf)

            dispatch_table = self._parsers_by_format.get(header.packet_format)

            if dispatch_table is None:
                if self.validate_format:
                    self.packets_unknown_format += 1
                    return None
                dispatch_table = self._parsers_by_format[models.PACKET_FORMAT_26]

            parser_fn = dispatch_table.get(header.packet_id)
            if parser_fn is None:
                self.packets_unknown += 1
                return None
    
            packet = parser_fn(header, buf)
            self.packets_parsed += 1
            return packet

        except Exception:
            self.packets_failed += 1
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
            "unknown_format": self.packets_unknown_format,
            "total": self.packets_parsed + self.packets_failed + self.packets_unknown,
        }
    
    def reset_stats(self):
        self.packets_parsed = 0
        self.packets_failed = 0
        self.packets_unknown = 0
        self.packets_unknown_format = 0