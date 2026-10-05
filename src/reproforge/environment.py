"""Environment capture used as reproduction evidence."""

from __future__ import annotations

import os
import platform
import sys
from typing import Any

from .hashing import sha256_object


def capture_environment() -> dict[str, Any]:
    data: dict[str, Any] = {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "executable": sys.executable,
        "env": {
            key: os.environ[key]
            for key in ("CUDA_VISIBLE_DEVICES", "PYTHONHASHSEED")
            if key in os.environ
        },
    }
    data["environment_hash"] = sha256_object(data)
    return data
