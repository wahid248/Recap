import gc

import torch

from utils.logger import get_logger

logger = get_logger(__name__)

_loaded_models: dict[str, object] = {}


def get_vram_usage_gb() -> float:
    """Return current VRAM usage in GB, or 0.0 if CUDA is unavailable."""
    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.memory_allocated() / (1024**3)


def get_vram_total_gb() -> float:
    """Return total VRAM in GB, or 0.0 if CUDA is unavailable."""
    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.get_device_properties(0).total_memory / (1024**3)


def register_model(name: str, model: object) -> None:
    """Track a loaded model and log VRAM usage."""
    _loaded_models[name] = model
    logger.info("Model loaded: %s | VRAM: %.2fGB / %.2fGB", name, get_vram_usage_gb(), get_vram_total_gb())


def unload_model(name: str) -> None:
    """Unload a tracked model and free VRAM."""
    if name not in _loaded_models:
        return
    del _loaded_models[name]
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("Model unloaded: %s | VRAM: %.2fGB", name, get_vram_usage_gb())


def unload_all_models() -> None:
    """Unload every tracked model."""
    for name in list(_loaded_models.keys()):
        unload_model(name)
