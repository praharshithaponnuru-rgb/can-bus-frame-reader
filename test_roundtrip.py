"""
test_roundtrip.py

Automated tests for the CAN frame encode/decode logic. Run with:
    pytest

These tests cover two things:
1. Round-trip correctness: build_*_frame() -> parse_*_frame() recovers
   the original values.
2. Cross-check against the DBC file: manually parsed values must match
   what cantools decodes using vehicle.dbc. This specific check is the
   one that would have caught the real Motorola-vs-Intel byte-order bug
   hit during development, automatically, on every push.
"""

import struct
import cantools

from virtual_ecu_sim import build_engine_frame, build_speed_frame
from can_reader_raw import parse_engine_frame, parse_speed_frame

DBC_FILE = "vehicle.dbc"


def test_engine_frame_roundtrip():
    for rpm, temp in [(800, 20), (3200, 90), (6000, 95), (0, -40)]:
        msg = build_engine_frame(rpm, temp)
        decoded_rpm, decoded_temp = parse_engine_frame(msg.data)
        assert decoded_rpm == rpm
        assert decoded_temp == temp


def test_speed_frame_roundtrip():
    for speed in [0.0, 55.5, 159.99, 100.0]:
        msg = build_speed_frame(speed)
        decoded_speed = parse_speed_frame(msg.data)
        assert abs(decoded_speed - speed) < 0.01


def test_engine_frame_matches_dbc_decode():
    """Catches byte-order / scale-factor mismatches between the manual
    parser and the DBC definition - exactly the class of bug hit
    during development (Motorola vs. Intel byte order)."""
    db = cantools.database.load_file(DBC_FILE)

    rpm, temp = 3200, 90
    msg = build_engine_frame(rpm, temp)

    manual_rpm, manual_temp = parse_engine_frame(msg.data)
    dbc_decoded = db.decode_message(msg.arbitration_id, msg.data)

    assert dbc_decoded["EngineRPM"] == manual_rpm == rpm
    assert dbc_decoded["CoolantTemp"] == manual_temp == temp


def test_speed_frame_matches_dbc_decode():
    db = cantools.database.load_file(DBC_FILE)

    speed = 55.5
    msg = build_speed_frame(speed)

    manual_speed = parse_speed_frame(msg.data)
    dbc_decoded = db.decode_message(msg.arbitration_id, msg.data)

    assert abs(dbc_decoded["VehicleSpeed"] - manual_speed) < 0.01
    assert abs(dbc_decoded["VehicleSpeed"] - speed) < 0.01
