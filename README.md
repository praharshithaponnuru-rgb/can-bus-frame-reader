# CAN Bus Frame Reader/Parser (Simulated + DBC-based)

A small project demonstrating CAN bus frame generation, parsing, and
DBC-based signal decoding in Python — no CAN hardware required to run.

## What this project shows
- How CAN frames are structured (arbitration ID + up to 8 data bytes)
- How signals are packed into bytes with scale factors and offsets
  (the same way a real vehicle ECU encodes RPM, speed, temperature, etc.)
- Two ways to decode frames: manual byte-parsing, and the industry-standard
  way using a DBC file + `cantools`

## Setup
```bash
pip install -r requirements.txt
```

## Running it (no hardware needed)
Open **two terminals** in this folder (same folder in both).

Terminal 1 — simulated ECU sending frames:
```bash
python virtual_ecu_sim.py
```

Terminal 2 — EITHER of these readers:
```bash
python can_reader_raw.py      # manual byte parsing
# or
python can_reader_dbc.py      # DBC-based decoding with cantools
```

You should see the reader printing decoded RPM, speed, and coolant
temperature values as the simulated ECU "drives."

### Why `udp_multicast` instead of `virtual`
`python-can`'s `virtual` interface only shares messages **within a single
Python process** — it keeps its list of connected buses in memory, so two
separate terminals (two separate processes) running `bustype="virtual"`
can never see each other's frames, even with the same channel name. That
shows up exactly as: the sender prints "Sent ->" happily, while the reader
sits at "No message received" forever.

`udp_multicast` fixes this by using real UDP network sockets, which work
across processes (and even across machines on the same network) — no
hardware required, and no code changes needed beyond the `Bus(...)` line.
If you ever see the same "sender OK, reader empty" symptom with any
`python-can` script, this mismatch is the first thing to check.

### A real bug we hit: Motorola vs. Intel byte order
The first version of `vehicle.dbc` defined signals as `@0` (Motorola /
big-endian), while the simulator packed bytes as plain big-endian too —
but the result still decoded to nonsense (RPM values in the tens of
thousands, speeds over 400 km/h). This is a classic, very common
real-world CAN bug: DBC "Motorola" bit-numbering counts bits in a
specific cross-byte order that does **not** line up 1:1 with a naive
`struct.pack(">H", ...)`, even though both are conceptually
"big-endian." Getting Motorola start-bit numbering exactly right by
hand is a frequent source of real integration bugs.

The fix here: switch everything to **Intel / little-endian (`@1`)**,
which has simple, unambiguous bit numbering (`start_bit` is just the
LSB's position, counted plainly from 0), and pack data with
`struct.pack("<H", ...)` to match. Same signals, same values, far
fewer ways to get it wrong — which is also why Intel format is the
more common choice in a lot of real automotive DBCs.

## Files
| File | Purpose |
|---|---|
| `virtual_ecu_sim.py` | Simulates an ECU sending Engine (0x100) and Speed (0x200) CAN frames |
| `can_reader_raw.py` | Reads frames and manually unpacks the bytes (shows the low-level logic) |
| `vehicle.dbc` | Defines the signals (name, position, scale, offset, unit) for the two messages |
| `can_reader_dbc.py` | Reads frames and decodes them automatically using `vehicle.dbc` + `cantools` |

## Upgrading to real hardware
Once you want to go beyond simulation, a cheap **USB-to-CAN adapter**
is the easiest entry point:

- **CANable** (~€25–35, open-source hardware/firmware, widely supported) —
  good first adapter, works with `python-can` via the `slcan` or `gs_usb` backend.
- **PCAN-USB** (PEAK-System) — more expensive (~€200) but an industry-standard
  tool you'll see referenced in real automotive job postings.

With real hardware, you only need to change ONE line in each script —
the `can.interface.Bus(...)` call:
```python
# Virtual (no hardware):
bus = can.interface.Bus(channel="test", bustype="virtual")

# Real hardware, e.g. CANable on Linux (SocketCAN):
bus = can.interface.Bus(channel="can0", bustype="socketcan")

# Real hardware, e.g. CANable as a serial/slcan device on Windows:
bus = can.interface.Bus(channel="COM5", bustype="slcan", bitrate=500000)
```
Everything else — the parsing logic, the DBC file, the decoding code —
stays exactly the same. That's the real lesson here: once you understand
frames, IDs, and DBCs, the hardware underneath is just a transport detail.

## Running the tests
```bash
pip install pytest
pytest -v
```
These tests check that encoding and decoding frames round-trips
correctly, and - critically - that the manual parser and the DBC-based
`cantools` decoder agree with each other. This second check is the one
that would have caught the Motorola-vs-Intel byte-order bug hit during
development, automatically. A GitHub Actions workflow
(`.github/workflows/ci.yml`) runs these same tests on every push - see
the **Actions** tab on the GitHub repo.

## Next steps / ideas to extend this
- Log decoded signals to a CSV file over time
- Plot RPM/Speed live with `matplotlib`
- Add a third message (e.g. fuel level) and extend the DBC yourself
- Try `candump`/`cansniffer` equivalents by printing raw frames before decoding
