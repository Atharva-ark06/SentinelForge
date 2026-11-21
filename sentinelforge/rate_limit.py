"""Bounded, in-process fixed-window limiter for local single-worker deployments.

Use an edge gateway or shared store for multi-worker and internet-facing deployments.
Do not trust client-supplied forwarding headers as an identity source.
"""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class FixedWindowLimiter:
    def __init__(self, *, limit: int, window_seconds: float = 60.0, max_clients: int = 10000):
        if limit < 1 or window_seconds <= 0 or max_clients < 1:
            raise ValueError("rate limit settings must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_clients = max_clients
        self._requests = defaultdict(deque)
        self._lock = Lock()

    def allow(self, client: str, *, now: float | None = None) -> bool:
        timestamp = monotonic() if now is None else now
        with self._lock:
            if client not in self._requests and len(self._requests) >= self.max_clients:
                # Reclaim expired identities before rejecting a new client.
                cutoff = timestamp - self.window_seconds
                for identity, history in list(self._requests.items()):
                    while history and history[0] <= cutoff:
                        history.popleft()
                    if not history:
                        del self._requests[identity]
                if len(self._requests) >= self.max_clients:
                    # Fail closed if every tracked identity remains active.
                    return False
            recent = self._requests[client]
            while recent and recent[0] <= timestamp - self.window_seconds:
                recent.popleft()
            if len(recent) >= self.limit:
                return False
            recent.append(timestamp)
            return True
