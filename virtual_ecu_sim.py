"""
virtual_ecu_sim.py

Simulates a car ECU sending CAN frames on a *virtual* CAN bus.
No hardware required - python-can's 'virtual' backend lets multiple
processes on the same machine talk to each other as if they were on
a real CAN network.

Run this in one terminal, and can_reader.py in another, at the same time.
"""

import can
import time
import random
import struct

# Two "real-looking" CAN messages, like you'd find in a real vehicle DBC:
#   0x100 - Engine data: RPM (2 bytes) + Coolant Temp (1 byte)
#   0x200 - Speed data:  Vehicle Speed (2 bytes, km/h * 100)

def build_engine_frame(rpm: int, coolant_temp_c: int) -> can.Message:
    # Big-endian, 2 bytes RPM + 1 byte temp (offset -40, common automotive convention)
    data = struct.pack("<H", rpm) + struct.pack("B", coolant_temp_c + 40) + b"\x00" * 5
    return can.Message(arbitration_id=0x100, data=data, is_extended_id=False)


def build_speed_frame(speed_kmh: float) -> can.Message:
    raw = int(speed_kmh * 100)  # scale factor 0.01, like real DBCs often use
    data = struct.pack("<H", raw) + b"\x00" * 6
    return can.Message(arbitration_id=0x200, data=data, is_extended_id=False)


def main():
    # udp_multicast works ACROSS separate terminals/processes (unlike bustype="virtual",
    # which only works within a single Python process). The multicast group address
    # must match exactly on both sender and receiver.
    bus = can.interface.Bus(channel="239.0.0.1", interface="udp_multicast")
    print("ECU simulator started. Sending frames on multicast group 239.0.0.1... (Ctrl+C to stop)")

    rpm = 800
    speed = 0.0
    coolant = 20

    try:
        while True:
            # Fake some realistic driving behaviour
            rpm = max(700, min(6000, rpm + random.randint(-150, 200)))
            speed = max(0.0, min(160.0, speed + random.uniform(-3, 4)))
            coolant = min(95, coolant + random.choice([0, 0, 1]))

            bus.send(build_engine_frame(rpm, coolant))
            bus.send(build_speed_frame(speed))

            print(f"Sent -> RPM: {rpm:4d}  Speed: {speed:5.1f} km/h  Coolant: {coolant}C")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
