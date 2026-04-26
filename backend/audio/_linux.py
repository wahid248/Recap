import queue
from typing import Optional

import numpy as np
import sounddevice as sd

from config import CHANNELS, SAMPLE_RATE
from utils.logger import get_logger

logger = get_logger(__name__)


class LinuxCapture:
    def __init__(self) -> None:
        self._queue: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: Optional[sd.InputStream] = None

    def start(self) -> None:
        """Start PulseAudio/PipeWire monitor source capture."""
        monitor_device = self._find_monitor_device()
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            device=monitor_device,
            callback=self._callback,
        )
        self._stream.start()
        logger.info("Linux monitor capture started (device=%s)", monitor_device)

    def stop(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        logger.info("Linux audio capture stopped")

    def get_chunk(self) -> Optional[np.ndarray]:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def _callback(self, indata: np.ndarray, frames: int, time: object, status: object) -> None:
        if status:
            logger.warning("Audio capture status: %s", status)
        self._queue.put(indata.copy().flatten())

    @staticmethod
    def _find_monitor_device() -> Optional[int]:
        """Return the index of the first PulseAudio monitor source, or None."""
        for i, device in enumerate(sd.query_devices()):
            if "monitor" in device["name"].lower() and device["max_input_channels"] > 0:
                return i
        return None
