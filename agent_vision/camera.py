"""Grab one frame from the wrist USB camera with ffmpeg."""
import os
import platform
import shutil
import subprocess


def snap_command(out, device=None, size="1280x720"):
    """Build the ffmpeg command for this OS. device: avfoundation index (macOS) or /dev/videoN (Linux)."""
    if platform.system() == "Darwin":
        src = ["-f", "avfoundation", "-framerate", "30", "-video_size", size, "-i", str(device or "0")]
    else:
        src = ["-f", "v4l2", "-video_size", size, "-i", device or "/dev/video0"]
    # Skip a few frames so auto-exposure settles, then keep one.
    return ["ffmpeg", "-y", "-loglevel", "error"] + src + ["-vf", "select=gte(n\\,10)", "-frames:v", "1", out]


def snap(out, device=None, size="1280x720"):
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found (macOS: brew install ffmpeg, Linux: apt install ffmpeg)")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    subprocess.run(snap_command(out, device, size), check=True)
    return out
