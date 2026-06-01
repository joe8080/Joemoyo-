"""Thin wrappers around the ffmpeg and ffprobe CLIs."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Sequence


class FfmpegNotFound(RuntimeError):
    pass


class FfmpegError(RuntimeError):
    def __init__(self, cmd: Sequence[str], returncode: int, stderr: str):
        self.cmd = list(cmd)
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(
            f"ffmpeg exited with {returncode}\n"
            f"cmd: {' '.join(self.cmd)}\n"
            f"stderr: {stderr[-2000:]}"
        )


def _require(binary: str) -> str:
    path = shutil.which(binary)
    if not path:
        raise FfmpegNotFound(
            f"{binary!r} was not found on PATH. Install ffmpeg: "
            "`brew install ffmpeg` or `apt-get install -y ffmpeg`."
        )
    return path


def run_ffmpeg(args: Sequence[str], *, overwrite: bool = True) -> None:
    """Run ffmpeg with the given args. Raises FfmpegError on non-zero exit."""
    cmd = [_require("ffmpeg"), "-hide_banner", "-loglevel", "error"]
    if overwrite:
        cmd.append("-y")
    cmd.extend(args)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise FfmpegError(cmd, proc.returncode, proc.stderr)


def ffprobe_json(path: str | Path) -> dict:
    """Return ffprobe metadata for a media file as a dict."""
    ffprobe = _require("ffprobe")
    cmd = [
        ffprobe,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise FfmpegError(cmd, proc.returncode, proc.stderr)
    return json.loads(proc.stdout)


def quote_filter_path(path: str | Path) -> str:
    """Escape a filesystem path for use inside an ffmpeg filter string.

    ffmpeg filter syntax treats ``:`` as an argument separator and ``\\`` as
    an escape, which breaks Windows paths, paths containing colons, and
    paths containing apostrophes. This helper escapes those characters.
    """
    s = str(path)
    # Order matters: escape backslash first, then colon, then apostrophe.
    s = s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    return s
