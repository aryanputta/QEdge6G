from __future__ import annotations

import time
from contextlib import contextmanager


@contextmanager
def profiled_timer():
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start

