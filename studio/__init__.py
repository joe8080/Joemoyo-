"""Studio: a script-to-finished-video engine Claude can drive.

    python -m studio render path/to/project.json
    python -m studio fix clip.mp4
    python -m studio --help
"""
from .util import ENGINE_VERSION as __version__  # noqa: F401
