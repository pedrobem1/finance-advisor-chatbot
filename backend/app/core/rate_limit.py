from collections import deque
from dataclasses import dataclass
from threading import Lock
from time import monotonic


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int = 0


class SlidingWindowRateLimiter:
    """Limits requests per client inside a rolling time window."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = {}
        self._lock = Lock()

    def check(self, client_id: str) -> RateLimitResult:
        now = monotonic()

        with self._lock:
            timestamps = self._requests.setdefault(client_id, deque())
            window_start = now - self.window_seconds

            while timestamps and timestamps[0] <= window_start:
                timestamps.popleft()

            if len(timestamps) >= self.max_requests:
                retry_after = max(1, int(timestamps[0] + self.window_seconds - now) + 1)
                return RateLimitResult(allowed=False, retry_after_seconds=retry_after)

            timestamps.append(now)
            return RateLimitResult(allowed=True)
