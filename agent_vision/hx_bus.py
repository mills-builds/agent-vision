"""Minimal driver for Hiwonder HX bus servos on a BusLinker V3 (USB serial).

Packet format (both directions):
    0x55 0x55 ID LEN CMD [params...] CHK
    LEN = 3 + len(params)
    CHK = ~(ID + LEN + CMD + sum(params)) & 0xFF

Positions run 0..1000. Pure helpers (build_packet, parse_frames, clamp, ...)
have no serial dependency so they can be unit tested without hardware.
"""
import os
import time

# Command numbers
MOVE = 1        # params: pos lo, pos hi, time_ms lo, time_ms hi
TEMP_READ = 26  # reply: 1 byte, degrees C
VIN_READ = 27   # reply: 2 bytes little endian, millivolts
POS_READ = 28   # reply: 2 bytes little endian, signed
UNLOAD = 31     # params: 0 = torque off, 1 = torque on

POS_MIN, POS_MAX = 0, 1000
DEFAULT_BAUD = 1000000

# Joint IDs, daisy-chained base -> wrist roll.
JOINTS = {1: "base", 2: "shoulder", 3: "elbow", 4: "wrist", 5: "roll"}


def checksum(body):
    """Checksum over ID, LEN, CMD and params."""
    return (~sum(body)) & 0xFF


def build_packet(servo_id, cmd, params=b""):
    params = bytes(params)
    body = bytes([servo_id, 3 + len(params), cmd]) + params
    return b"\x55\x55" + body + bytes([checksum(body)])


def move_packet(servo_id, pos, time_ms):
    pos = clamp(int(pos), POS_MIN, POS_MAX)
    time_ms = clamp(int(time_ms), 0, 30000)
    return build_packet(servo_id, MOVE, [pos & 0xFF, pos >> 8, time_ms & 0xFF, time_ms >> 8])


def parse_frames(buf):
    """Return (frames, leftover). Each frame is (id, cmd, params) with a valid checksum.
    Bad checksums are skipped; incomplete trailing data is returned as leftover."""
    frames = []
    i = 0
    while True:
        i = buf.find(b"\x55\x55", i)
        if i < 0:
            return frames, b""
        if len(buf) < i + 4:
            return frames, buf[i:]
        ln = buf[i + 3]
        end = i + 3 + ln
        if ln < 3:
            i += 2
            continue
        if len(buf) < end:
            return frames, buf[i:]
        body, chk = buf[i + 2:end - 1], buf[end - 1]
        if checksum(body) == chk:
            frames.append((body[0], body[2], bytes(body[3:])))
            i = end
        else:
            i += 2


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def apply_margin(lo, hi, margin):
    """Shrink a hand-swept [lo, hi] range by margin on each side (never inverts)."""
    a, b = lo + margin, hi - margin
    if a > b:
        mid = (lo + hi) // 2
        return mid, mid
    return a, b


def interpolate(start, target, steps):
    """Yield `steps` dicts moving each joint linearly from start to target."""
    for k in range(1, steps + 1):
        f = k / steps
        yield {j: round(start[j] + (target[j] - start[j]) * f) for j in target}


def resolve_port(cli_port=None, config=None):
    """Port priority: --port, then $AV_PORT, then config['port']."""
    port = cli_port or os.environ.get("AV_PORT") or (config or {}).get("port")
    if not port:
        raise SystemExit("No serial port. Use --port, set AV_PORT, or add \"port\" to av_config.json.\n"
                         "  macOS: ls /dev/cu.usb*    Linux: ls /dev/ttyUSB* /dev/ttyACM*")
    return port


def resolve_baud(cli_baud=None, config=None):
    return int(cli_baud or os.environ.get("AV_BAUD") or (config or {}).get("baud") or DEFAULT_BAUD)


class Bus:
    """A BusLinker serial connection. Use as a context manager."""

    def __init__(self, port, baud=DEFAULT_BAUD):
        import serial  # pyserial; imported here so tests don't need it
        self.ser = serial.Serial(port, baud, timeout=0.02)
        time.sleep(0.2)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.ser.close()

    def send(self, pkt):
        self.ser.write(pkt)
        self.ser.flush()

    def query(self, servo_id, cmd, timeout=0.1):
        """Send a read command, return the reply params or None."""
        self.ser.reset_input_buffer()
        out = build_packet(servo_id, cmd)
        self.send(out)
        buf, t0 = b"", time.time()
        while time.time() - t0 < timeout:
            buf += self.ser.read(64)
            frames, _ = parse_frames(buf)
            for fid, fcmd, data in frames:
                # The BusLinker may echo our own request (no data); skip it.
                if fid == servo_id and fcmd == cmd and data:
                    return data
        return None

    def position(self, sid):
        d = self.query(sid, POS_READ)
        return None if d is None else int.from_bytes(d[:2], "little", signed=True)

    def temperature(self, sid):
        d = self.query(sid, TEMP_READ)
        return None if d is None else d[0]

    def voltage(self, sid):
        d = self.query(sid, VIN_READ)
        return None if d is None else int.from_bytes(d[:2], "little") / 1000

    def move(self, sid, pos, time_ms):
        self.send(move_packet(sid, pos, time_ms))

    def torque_off(self, sid):
        self.send(build_packet(sid, UNLOAD, [0]))
        time.sleep(0.02)

    def positions(self, ids=JOINTS):
        return {sid: self.position(sid) for sid in ids}

    def hold_here(self, ids=JOINTS):
        """Re-lock joints where they are by commanding MOVE to their current position."""
        cur = self.positions(ids)
        for sid, p in cur.items():
            if p is not None:
                self.move(sid, p, 300)
        return cur
