"""Shared CLI options and JSON files (av_config.json, limits.json, poses.json)."""
import argparse
import json
import os

from . import hx_bus

CONFIG_FILE = os.environ.get("AV_CONFIG", "av_config.json")


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def parser(description):
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--port", help="serial port (or $AV_PORT, or \"port\" in av_config.json)")
    ap.add_argument("--baud", type=int, help="baud rate (default 1000000)")
    ap.add_argument("--limits", default="limits.json", help="limits file (default limits.json)")
    ap.add_argument("--poses", default="poses.json", help="poses file (default poses.json)")
    return ap


def open_bus(args):
    cfg = load_json(CONFIG_FILE, {})
    return hx_bus.Bus(hx_bus.resolve_port(args.port, cfg), hx_bus.resolve_baud(args.baud, cfg))


def load_limits(path):
    """Return {servo_id: (min, max)} from limits.json, or None if missing."""
    data = load_json(path)
    if data is None:
        return None
    return {int(v["id"]): (int(v["min"]), int(v["max"]))
            for k, v in data.items() if not k.startswith("_")}
