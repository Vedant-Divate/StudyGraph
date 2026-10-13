"""Configurable rate limiting + backoff (PROJECT.md 5.3, ADR-0005).

Concurrency via semaphore, requests-per-minute via a sliding window, and
exponential backoff on 429/5xx. Pure helpers + a small guard class; no I/O.
"""

import threading
import time
from collections import deque


class RateLimiter:
    def __init__(self, *, rpm: int, concurrency: int) -> None:
        self._rpm = max(1, rpm)
        self._semaphore = threading.Semaphore(max(1, concurrency))
        self._window: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        self._semaphore.acquire()
        try:
            with self._lock:
                now = time.monotonic()
                window = 60.0 / self._rpm
                while self._window and now - self._window[0] >= 60.0:
                    self._window.popleft()
                if len(self._window) >= self._rpm:
                    sleep_for = window - (now - self._window[0])
                    if sleep_for > 0:
                        time.sleep(sleep_for)
                        now = time.monotonic()
                self._window.append(now)
        except Exception:
            self._semaphore.release()
            raise

    def release(self) -> None:
        self._semaphore.release()


def backoff_delay(attempt: int, *, base_s: float = 1.0, cap_s: float = 30.0) -> float:
    return min(cap_s, base_s * (2.0 ** max(0, attempt)))


def is_retryable_status(status_code: int | None) -> bool:
    return status_code is not None and (status_code == 429 or 500 <= status_code <= 599)
