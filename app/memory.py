from __future__ import annotations

import ctypes
import gc
import logging
import os


logger = logging.getLogger("mak.memory")


def release_memory(label: str = "manual") -> dict:
    collected = gc.collect()
    trimmed = False
    if os.name == "posix":
        try:
            libc = ctypes.CDLL("libc.so.6")
            trimmed = bool(libc.malloc_trim(0))
        except Exception as exc:
            logger.debug("malloc_trim unavailable after %s: %s", label, exc)
    logger.info("Memory cleanup after %s: collected=%s trimmed=%s", label, collected, trimmed)
    return {"collected": collected, "malloc_trim": trimmed}
