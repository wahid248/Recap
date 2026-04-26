import platform
from typing import Optional

import numpy as np

_backend = None


def _load_backend() -> None:
    global _backend
    os_name = platform.system()
    if os_name == "Windows":
        from audio._windows import WindowsCapture
        _backend = WindowsCapture()
    elif os_name == "Linux":
        from audio._linux import LinuxCapture
        _backend = LinuxCapture()
    elif os_name == "Darwin":
        from audio._macos import MacOSCapture
        _backend = MacOSCapture()
    else:
        raise RuntimeError(f"Unsupported platform: {os_name}")


def start() -> None:
    """Start audio capture for the current platform."""
    if _backend is None:
        _load_backend()
    _backend.start()  # type: ignore[union-attr]


def stop() -> None:
    """Stop audio capture."""
    if _backend is not None:
        _backend.stop()


def get_chunk() -> Optional[np.ndarray]:
    """Return the next available PCM chunk (float32, 16kHz mono), or None."""
    if _backend is None:
        return None
    return _backend.get_chunk()
