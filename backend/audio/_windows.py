import math
import queue
from typing import Optional

import numpy as np
import sounddevice as sd
from scipy.signal import resample_poly

from config import CHANNELS, SAMPLE_RATE
from utils.logger import get_logger

logger = get_logger(__name__)


class WindowsCapture:
    def __init__(self) -> None:
        self._queue: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: Optional[sd.InputStream] = None
        self._device_rate: int = SAMPLE_RATE

    def start(self) -> None:
        """Start WASAPI loopback capture on the default output device."""
        loopback_device = self._find_wasapi_loopback()
        self._device_rate = self._get_device_rate(loopback_device)
        blocksize = 512 * max(1, self._device_rate // SAMPLE_RATE)  # gives ~512 samples at 16kHz after resampling
        self._stream = sd.InputStream(
            samplerate=self._device_rate,
            channels=CHANNELS,
            dtype="float32",
            device=loopback_device,
            blocksize=blocksize,
            callback=self._callback,
        )
        self._stream.start()
        logger.info(
            "Windows WASAPI loopback capture started (device=%s, rate=%s)",
            loopback_device,
            self._device_rate,
        )

    def stop(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        logger.info("Windows audio capture stopped")

    def get_chunk(self) -> Optional[np.ndarray]:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def _callback(self, indata: np.ndarray, frames: int, time: object, status: object) -> None:
        if status:
            logger.warning("Audio capture status: %s", status)
        audio = indata.copy().flatten()
        if self._device_rate != SAMPLE_RATE:
            g = math.gcd(self._device_rate, SAMPLE_RATE)
            audio = resample_poly(audio, SAMPLE_RATE // g, self._device_rate // g).astype(np.float32)
        self._queue.put(audio)

    @staticmethod
    def _get_device_rate(device_index: Optional[int]) -> int:
        """Return the default sample rate of the given device, falling back to 48000."""
        try:
            info = sd.query_devices(device_index)
            return int(info["default_samplerate"])
        except Exception:
            return 48000

    @staticmethod
    def _find_wasapi_loopback() -> Optional[int]:
        """Return the index of the first WASAPI loopback input device, or None for default."""
        for i, device in enumerate(sd.query_devices()):
            try:
                host = sd.query_hostapis(device["hostapi"])
                if "WASAPI" in host["name"] and device["max_input_channels"] > 0:
                    return i
            except Exception:
                continue
        return None
