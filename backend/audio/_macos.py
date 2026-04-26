import queue
import struct
import subprocess
import threading
from pathlib import Path
from typing import Optional

import numpy as np

from config import SAMPLE_RATE
from utils.logger import get_logger

logger = get_logger(__name__)

# Pre-compiled Swift helper that reads system audio via ScreenCaptureKit
# and writes raw float32 PCM to stdout.
_SWIFT_HELPER = Path(__file__).parent / "macos_helper"


class MacOSCapture:
    def __init__(self) -> None:
        self._queue: queue.Queue[np.ndarray] = queue.Queue()
        self._process: Optional[subprocess.Popen] = None  # type: ignore[type-arg]
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Launch the Swift ScreenCaptureKit helper and read PCM from its stdout."""
        self._process = subprocess.Popen(
            [str(_SWIFT_HELPER), str(SAMPLE_RATE)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        logger.info("macOS ScreenCaptureKit capture started")

    def stop(self) -> None:
        if self._process:
            self._process.terminate()
            self._process = None
        logger.info("macOS audio capture stopped")

    def get_chunk(self) -> Optional[np.ndarray]:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def _read_loop(self) -> None:
        """Read raw float32 PCM frames from the helper's stdout in 1-second chunks."""
        bytes_per_sample = 4
        chunk_samples = SAMPLE_RATE  # 1 second
        while self._process and self._process.poll() is None:
            raw = self._process.stdout.read(chunk_samples * bytes_per_sample)  # type: ignore[union-attr]
            if not raw:
                break
            count = len(raw) // bytes_per_sample
            samples = struct.unpack(f"{count}f", raw)
            self._queue.put(np.array(samples, dtype=np.float32))
