"""
can_reader_dbc.py

Industry-standard approach: instead of manually unpacking bytes, load
a DBC file (vehicle.dbc) that defines each signal's position, scale,
and offset within each CAN message, and let `cantools` decode frames
for you. This is how real automotive test/diagnostic tools work.

Run virtual_ecu_sim.py in one terminal and this script in another.
"""

import can
import cantools

DBC_FILE = "vehicle.dbc"


def main():
    db = cantools.database.load_file(DBC_FILE)
    bus = can.interface.Bus(channel="239.0.0.1", interface="udp_multicast")
    print(f"Loaded {DBC_FILE} with messages: {[m.name for m in db.messages]}")
    print("Listening on multicast group 239.0.0.1... (Ctrl+C to stop)")

    try:
        while True:
            msg = bus.recv(timeout=2.0)
            if msg is None:
                print("No message received in 2s...")
                continue

            try:
                decoded = db.decode_message(msg.arbitration_id, msg.data)
                message_def = db.get_message_by_frame_id(msg.arbitration_id)
                print(f"[{message_def.name}] {decoded}")
            except KeyError:
                print(f"[0x{msg.arbitration_id:03X}] Not in DBC, raw={msg.data.hex()}")
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
