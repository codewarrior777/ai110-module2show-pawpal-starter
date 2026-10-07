"""Benchmark script for PawPal+ Scheduler algorithms.

Measures how each algorithm scales with the number of tasks.
Useful for validating O(n) vs O(n log n) vs O(n²) expectations.

Run with:
    python benchmark.py
"""

import time
from datetime import date

from tabulate import tabulate

from pawpal_system import Scheduler, Task


def _make_tasks(n: int) -> list[Task]:
    """Create n tasks with varied times, priorities, frequencies."""
    priorities = ["high", "medium", "low"]
    frequencies = ["once", "daily", "weekly"]
    tasks = []
    for i in range(n):
        hour = 6 + (i % 16)
        minute = (i * 7) % 60
        tasks.append(
            Task(
                description=f"Task {i}",
                time=f"{hour:02d}:{minute:02d}",
                due_date=date.today(),
                priority=priorities[i % 3],
                frequency=frequencies[i % 3],
            )
        )
    return tasks


def _time_it(func, *args, runs: int = 5, **kwargs) -> float:
    """Run func N times, return the best (fastest) duration in ms."""
    best = float("inf")
    for _ in range(runs):
        start = time.perf_counter()
        func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        best = min(best, elapsed)
    return round(best, 3)


def main() -> None:
    scheduler = Scheduler()

    sizes = [10, 100, 500, 1000, 2000]

    algorithms = [
        ("sort_by_time", scheduler.sort_by_time),
        ("sort_by_priority", scheduler.sort_by_priority),
        ("detect_conflicts (O(n²))", scheduler.detect_conflicts),
        ("detect_overlaps (O(n log n))", scheduler.detect_overlaps),
        ("find_next_available_slot", scheduler.find_next_available_slot),
    ]

    print("\n🔬 PawPal+ Algorithm Benchmark")
    print("=" * 80)
    print("Times shown in milliseconds (best of 5 runs)\n")

    headers = ["Algorithm"] + [f"n={n}" for n in sizes]
    rows = []

    for name, method in algorithms:
        row = [name]
        for n in sizes:
            tasks = _make_tasks(n)
            ms = _time_it(method, tasks)
            row.append(f"{ms:.2f}")
        rows.append(row)

    print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

    print("\n📊 filter_by_completion (O(n))\n")
    filter_rows = []
    for n in sizes:
        tasks = _make_tasks(n)
        for i, t in enumerate(tasks):
            if i % 2 == 0:
                t.mark_complete()
        ms = _time_it(scheduler.filter_by_completion, tasks, completed=True)
        filter_rows.append([f"n={n}", f"{ms:.2f} ms"])

    print(
        tabulate(
            filter_rows,
            headers=["Input Size", "Time"],
            tablefmt="fancy_grid",
        )
    )

    print("\n✅ Benchmark complete.")


if __name__ == "__main__":
    main()
