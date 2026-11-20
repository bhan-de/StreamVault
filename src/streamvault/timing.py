"""Time each step of the run and print the times as a small table."""
from __future__ import annotations

import time
from contextlib import contextmanager


class StageTimer:
    def __init__(self) -> None:
        self.rows: list[tuple[str, float, bool]] = []   # (step name, seconds, counts toward the time budget?)

    @contextmanager
    def stage(self, name: str, timed: bool = True):
        start = time.perf_counter()
        try:
            yield
        finally:
            self.rows.append((name, time.perf_counter() - start, timed))

    def computation_seconds(self) -> float:
        return sum(s for _, s, t in self.rows if t)

    def table(self) -> str:
        width = max([len(r[0]) for r in self.rows] + [5])
        out = [f"{'stage':<{width}}  {'seconds':>9}  in budget?", "-" * (width + 24)]
        for name, secs, timed in self.rows:
            out.append(f"{name:<{width}}  {secs:>9.4f}  {'yes' if timed else 'no (network/setup)'}")
        budget = sum(s for _, s, t in self.rows if t)
        out.append("-" * (width + 24))
        out.append(f"{'computation total':<{width}}  {budget:>9.4f}")
        return "\n".join(out)
