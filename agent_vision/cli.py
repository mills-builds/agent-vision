"""Command line tools: av_read, av_capture_range, av_teach, av_goto, av_relax, av_snap."""
import datetime
import os
import sys
import time

from . import camera, config, hx_bus
from .hx_bus import JOINTS

SUPPORT_WARNING = ("WARNING: torque is about to go OFF and the arm will go limp.\n"
                   "Support the arm with one hand first, or let it rest folded.")


def _confirm(msg):
    input(msg + "\nPress Enter to continue (Ctrl-C to cancel)... ")


def read_main(argv=None):
    """av_read: print position, temperature and voltage for each joint."""
    args = config.parser(read_main.__doc__).parse_args(argv)
    with config.open_bus(args) as bus:
        for sid, name in JOINTS.items():
            p, t, v = bus.position(sid), bus.temperature(sid), bus.voltage(sid)
            if p is None and t is None:
                print(f"{sid} {name:9s} no reply")
            else:
                print(f"{sid} {name:9s} pos {p}  temp {t} C  vin {v} V")


def relax_main(argv=None):
    """av_relax: turn torque off on every joint."""
    args = config.parser(relax_main.__doc__).parse_args(argv)
    _confirm(SUPPORT_WARNING)
    with config.open_bus(args) as bus:
        for sid in JOINTS:
            bus.torque_off(sid)
    print("Torque off on all joints.")


def capture_range_main(argv=None):
    """av_capture_range: sweep each joint by hand, record min/max, write limits.json."""
    ap = config.parser(capture_range_main.__doc__)
    ap.add_argument("--margin", type=int, default=25, help="safety margin trimmed off each end (default 25)")
    args = ap.parse_args(argv)
    _confirm(SUPPORT_WARNING)
    with config.open_bus(args) as bus:
        for sid in JOINTS:
            bus.torque_off(sid)
        lo = {s: None for s in JOINTS}
        hi = {s: None for s in JOINTS}
        print("\nGently move EACH joint to both ends of its travel.")
        print("Stop at resistance, a cable tug, or anything the arm could hit. Ctrl-C when done.\n")
        try:
            while True:
                parts = []
                for sid, name in JOINTS.items():
                    x = bus.position(sid)
                    if x is not None:
                        lo[sid] = x if lo[sid] is None else min(lo[sid], x)
                        hi[sid] = x if hi[sid] is None else max(hi[sid], x)
                    parts.append(f"{name}:{x} [{lo[sid]}-{hi[sid]}]")
                print("\r" + "  ".join(parts) + "  ", end="", flush=True)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print()
    out = {"_note": f"Captured {datetime.datetime.now():%Y-%m-%d %H:%M} with margin {args.margin}. "
                    "Specific to this arm and space."}
    for sid, name in JOINTS.items():
        if lo[sid] is None:
            print(f"WARNING: no readings for {name} (ID {sid}); not written.")
            continue
        a, b = hx_bus.apply_margin(lo[sid], hi[sid], args.margin)
        out[name] = {"id": sid, "min": a, "max": b, "raw_min": lo[sid], "raw_max": hi[sid]}
    config.save_json(args.limits, out)
    print(f"Saved {args.limits}. Torque is still OFF.")


def teach_main(argv=None):
    """av_teach NAME: place the arm by hand, press Enter, save the pose to poses.json."""
    ap = config.parser(teach_main.__doc__)
    ap.add_argument("name")
    ap.add_argument("--snap", action="store_true", help="also grab a camera frame into frames/")
    ap.add_argument("--camera", help="camera device (see av_snap)")
    args = ap.parse_args(argv)
    _confirm(SUPPORT_WARNING)
    with config.open_bus(args) as bus:
        for sid in JOINTS:
            bus.torque_off(sid)
        input(f"Place the arm for pose '{args.name}', keep supporting it, then press Enter... ")
        pose = bus.hold_here()  # read + re-lock in place
    missing = [JOINTS[s] for s, p in pose.items() if p is None]
    if missing:
        raise SystemExit(f"No reply from {missing}; pose not saved. (Joints that did reply are now holding.)")
    poses = config.load_json(args.poses, {})
    entry = {JOINTS[s]: p for s, p in pose.items()}
    if args.snap:
        entry["_frame"] = camera.snap(os.path.join("frames", f"{args.name}.jpg"), args.camera)
    poses[args.name] = entry
    config.save_json(args.poses, poses)
    print(f"Saved '{args.name}': {entry}. Arm is holding; run av_relax to release.")


def plan_goto(start, target, limits, max_step=20):
    """Clamp target to limits and return (clamped_target, list of waypoint dicts).
    Waypoints move every joint together, at most max_step units per step."""
    clamped = {s: hx_bus.clamp(target[s], *limits[s]) for s in target}
    dist = max(abs(clamped[s] - start[s]) for s in clamped) if clamped else 0
    steps = max(1, -(-dist // max_step))
    return clamped, list(hx_bus.interpolate(start, clamped, steps))


def goto_main(argv=None):
    """av_goto NAME: move slowly to a saved pose, clamped to limits.json."""
    ap = config.parser(goto_main.__doc__)
    ap.add_argument("name")
    ap.add_argument("--max-temp", type=int, default=55, help="abort above this servo temperature in C (default 55)")
    ap.add_argument("--step", type=int, default=20, help="max position units per step (default 20)")
    ap.add_argument("--step-ms", type=int, default=100, help="time per step in ms (default 100)")
    args = ap.parse_args(argv)

    limits = config.load_limits(args.limits)
    if limits is None:
        raise SystemExit(f"{args.limits} not found. Run av_capture_range first; av_goto never moves without limits.")
    poses = config.load_json(args.poses, {})
    if args.name not in poses:
        raise SystemExit(f"No pose '{args.name}' in {args.poses}. Known: {', '.join(poses) or 'none'}")
    by_name = {n: s for s, n in JOINTS.items()}
    target = {by_name[k]: v for k, v in poses[args.name].items() if k in by_name}
    if not target or not all(isinstance(v, int) for v in target.values()):
        raise SystemExit(f"Pose '{args.name}' needs integer positions; teach it with av_teach.")
    unlimited = [JOINTS[s] for s in target if s not in limits]
    if unlimited:
        raise SystemExit(f"No limits for {unlimited} in {args.limits}; refusing to move.")

    with config.open_bus(args) as bus:
        start = bus.positions(target)
        if None in start.values():
            raise SystemExit(f"Could not read every joint: {start}")
        clamped, waypoints = plan_goto(start, target, limits, args.step)
        for s in target:
            if clamped[s] != target[s]:
                print(f"note: {JOINTS[s]} clamped {target[s]} -> {clamped[s]}")
        print(f"Moving to '{args.name}' in {len(waypoints)} steps...")
        for i, wp in enumerate(waypoints):
            for s, p in wp.items():
                bus.move(s, p, args.step_ms)
            time.sleep(args.step_ms / 1000)
            if i % 10 == 0:  # check temperatures every 10 steps
                for s in target:
                    t = bus.temperature(s)
                    if t is not None and t > args.max_temp:
                        bus.hold_here(target)
                        raise SystemExit(f"ABORT: {JOINTS[s]} at {t} C > {args.max_temp} C. Holding position.")
        time.sleep(0.5)
        print("Arrived:", {JOINTS[s]: p for s, p in bus.positions(target).items()})


def snap_main(argv=None):
    """av_snap [OUT]: grab one camera frame."""
    import argparse
    ap = argparse.ArgumentParser(description=snap_main.__doc__)
    ap.add_argument("out", nargs="?", default=None)
    ap.add_argument("--camera", help="macOS: avfoundation index (ffmpeg -f avfoundation -list_devices true -i \"\"); "
                                     "Linux: /dev/videoN")
    ap.add_argument("--size", default="1280x720")
    args = ap.parse_args(argv)
    out = args.out or os.path.join("frames", f"snap_{datetime.datetime.now():%Y%m%d_%H%M%S}.jpg")
    print(camera.snap(out, args.camera, args.size))


if __name__ == "__main__":
    sys.exit("Use the av_* commands (pip install -e .)")
