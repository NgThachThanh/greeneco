
# app/cam_capture_cli.py
import subprocess, shlex
from datetime import datetime
from pathlib import Path

def capture_jpeg_cli(path: str, width=1280, height=720, quality=80, hflip=False, vflip=False, extra_args=None):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    args = [
        "rpicam-still",
        f"-o {shlex.quote(path)}",
        f"--width {width}", f"--height {height}",
        f"--quality {quality}",
        "--immediate", "--timeout 1"
    ]
    if hflip: args.append("--hflip")
    if vflip: args.append("--vflip")
    if extra_args: args += extra_args
    cmd = " ".join(args)
    subprocess.run(cmd, check=True, shell=True)
    return path, datetime.utcnow().isoformat()
