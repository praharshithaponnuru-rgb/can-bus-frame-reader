"""
can_reader_raw.py

Listens on the same virtual CAN channel as virtual_ecu_sim.py and
manually parses the raw bytes - this is the part that maps directly
to "reading/parsing CAN frames" as a skill: you get a CAN ID + up to
8 raw data bytes, and YOU decide what those bytes mean, based on the
vehicle's DBC / interface spec.

Run virtual_ecu_sim.py in one terminal and this script in another.
"""

import can
import struct

ENGINE_ID = 0x100
SPEED_ID = 0x200


def parse_engine_frame(data: bytes):
    rpm = struct.unpack("<H", data[0:2])[0]
    coolant_temp_c = data[2] - 40  # undo the +40 offset from the sender
    return rpm, coolant_temp_c


def parse_speed_frame(data: bytes):
    raw = struct.unpack("<H", data[0:2])[0]
    return raw / 100.0  # undo the *100 scale factor


def main():
    bus = can.interface.Bus(channel="239.0.0.1", interface="udp_multicast")
    print("Listening on multicast group 239.0.0.1 for raw CAN frames... (Ctrl+C to stop)")

    try:
        while True:
            msg = bus.recv(timeout=2.0)
            if msg is None:
                print("No message received in 2s...")
                continue

            if msg.arbitration_id == ENGINE_ID:
                rpm, temp = parse_engine_frame(msg.data)
                print(f"[0x{msg.arbitration_id:03X}] Engine  -> RPM: {rpm:4d}  Coolant: {temp}C   raw={msg.data.hex()}")
            elif msg.arbitration_id == SPEED_ID:
                speed = parse_speed_frame(msg.data)
                print(f"[0x{msg.arbitration_id:03X}] Speed   -> {speed:5.1f} km/h            raw={msg.data.hex()}")
            else:
                print(f"[0x{msg.arbitration_id:03X}] Unknown frame, raw={msg.data.hex()}")
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
