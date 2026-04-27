import math
import queue
import threading
from typing import Optional

import numpy as np
import pyaudiowpatch as pyaudio
import sounddevice as sd
from scipy.signal import resample_poly

from config import CHANNELS, SAMPLE_RATE
from utils.logger import get_logger

logger = get_logger(__name__)

class WindowsCapture:
    def __init__(self) -> None:
        self._loopback_queue: queue.Queue[np.ndarray] = queue.Queue()
        self._mic_queue: queue.Queue[np.ndarray] = queue.Queue()
        self._pa: Optional[pyaudio.PyAudio] = None
        self._loopback_stream: Optional[pyaudio.Stream] = None
        self._mic_stream: Optional[sd.InputStream] = None

    def start(self) -> None:
        """Start WASAPI loopback (system audio) + default mic capture simultaneously."""
        self._pa = pyaudio.PyAudio()
        loopback_device = self._find_loopback_device()
        loopback_rate = int(loopback_device["defaultSampleRate"])
        loopback_channels = min(loopback_device["maxInputChannels"], 2)
        # Match sounddevice blocksize so resampled output is 512 samples — Silero VAD's window size
        loopback_chunk = 512 * max(1, loopback_rate // SAMPLE_RATE)

        self._loopback_stream = self._pa.open(
            format=pyaudio.paFloat32,
            channels=loopback_channels,
            rate=loopback_rate,
            frames_per_buffer=loopback_chunk,
            input=True,
            input_device_index=loopback_device["index"],
            stream_callback=self._make_loopback_callback(loopback_rate, loopback_channels, loopback_chunk),
        )
        self._loopback_stream.start_stream()

        input_device = sd.default.device[0]
        mic_rate = self._get_sd_device_rate(input_device)
        mic_blocksize = 512 * max(1, mic_rate // SAMPLE_RATE)

        self._mic_stream = sd.InputStream(
            samplerate=mic_rate,
            channels=CHANNELS,
            dtype="float32",
            device=input_device,
            blocksize=mic_blocksize,
            callback=self._make_sd_callback(self._mic_queue, mic_rate),
        )
        self._mic_stream.start()

        logger.info(
            "Windows audio capture started — loopback=%s rate=%s, mic device=%s rate=%s",
            loopback_device["name"], loopback_rate, input_device, mic_rate,
        )

    def stop(self) -> None:
        if self._loopback_stream:
            self._loopback_stream.stop_stream()
            self._loopback_stream.close()
            self._loopback_stream = None
        if self._pa:
            self._pa.terminate()
            self._pa = None
        if self._mic_stream:
            self._mic_stream.stop()
            self._mic_stream.close()
            self._mic_stream = None
        logger.info("Windows audio capture stopped")

    def get_chunk(self) -> Optional[np.ndarray]:
        loopback = self._try_get(self._loopback_queue)
        mic = self._try_get(self._mic_queue)
        if loopback is not None and mic is not None:
            n = min(len(loopback), len(mic))
            return np.clip((loopback[:n] + mic[:n]) * 0.5, -1.0, 1.0).astype(np.float32)
        return loopback if loopback is not None else mic

    def _find_loopback_device(self) -> dict:
        """Return the pyaudiowpatch loopback device matching the default output."""
        wasapi_info = self._pa.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_output_idx = wasapi_info["defaultOutputDevice"]
        default_output_name = self._pa.get_device_info_by_index(default_output_idx)["name"]
        for loopback in self._pa.get_loopback_device_info_generator():
            if default_output_name in loopback["name"]:
                return loopback
        # Fallback: first available loopback device
        for loopback in self._pa.get_loopback_device_info_generator():
            return loopback
        raise RuntimeError("No WASAPI loopback device found")

    def _make_loopback_callback(self, device_rate: int, device_channels: int, chunk_size: int):
        def callback(in_data, frame_count, time_info, status):
            audio = np.frombuffer(in_data, dtype=np.float32).copy()
            expected = frame_count * device_channels
            if len(audio) < expected:
                audio = np.pad(audio, (0, expected - len(audio)))
            if device_channels > 1:
                audio = audio[:frame_count * device_channels].reshape(-1, device_channels).mean(axis=1)
            else:
                audio = audio[:frame_count]
            if device_rate != SAMPLE_RATE:
                g = math.gcd(device_rate, SAMPLE_RATE)
                audio = resample_poly(audio, SAMPLE_RATE // g, device_rate // g).astype(np.float32)
            self._loopback_queue.put(audio)
            return (None, pyaudio.paContinue)
        return callback

    @staticmethod
    def _make_sd_callback(target: queue.Queue, device_rate: int):
        def callback(indata: np.ndarray, frames: int, time: object, status: object) -> None:
            if status:
                logger.warning("Mic capture status: %s", status)
            audio = indata.copy().flatten()
            if device_rate != SAMPLE_RATE:
                g = math.gcd(device_rate, SAMPLE_RATE)
                audio = resample_poly(audio, SAMPLE_RATE // g, device_rate // g).astype(np.float32)
            target.put(audio)
        return callback

    @staticmethod
    def _try_get(q: queue.Queue) -> Optional[np.ndarray]:
        try:
            return q.get_nowait()
        except queue.Empty:
            return None

    @staticmethod
    def _get_sd_device_rate(device_index: Optional[int]) -> int:
        try:
            return int(sd.query_devices(device_index)["default_samplerate"])
        except Exception:
            return 48000
