# AI Interactions Log — PawPal+

> Documents how AI assistants (ChatGPT, Gemini) were used across the PawPal+ project, and compares their outputs on the same task.

---

## Agent Workflow (SF7)

**Task given to the agent (Gemini):**

```
I need a THIRD algorithmic capability for my Scheduler class that goes
beyond sorting and filtering. Propose a "next available time slot" finder.

Method signature:
find_next_available_slot(self, tasks: list[Task], duration_minutes: int = 30) -> str

- Input: a list of tasks (each with .time in "HH:MM" format)
- Output: the earliest time (as "HH:MM") when there are no tasks scheduled
  for duration_minutes consecutive minutes, starting from 06:00
- Working day: 06:00 to 22:00
- Approach: convert times to minutes-since-midnight, sort, walk through
  the gaps, return the first gap that fits
- Keep it simple — no external libraries
```

**What the agent (Gemini) did:**

1. Proposed a clean algorithm using minutes-since-midnight conversion.
2. Assumed each existing task occupies 30 minutes (Task has no duration field).
3. Handled the working-day boundary (06:00 to 22:00).
4. Handled the edge case of no available slot ("None available today").
5. Added a detailed docstring with Args/Returns.

**What I had to verify or fix manually:**

- **Verified** the algorithm against a hand-computed case: tasks at 07:00 and 08:00 → expected result `06:00` (first free gap). The function returned `06:00`. ✅
- **Documented the 30-minute assumption** in the docstring and in `reflection.md` (Section 2b). This is a limitation — the Scheduler doesn't know task durations, so it uses a fixed 30-minute block for gap calculations.
- **Integrated the method** into `main.py` as Feature 6 with a new table showing next available slots for 30-min and 60-min queries.
- **Added a boundary test** (`test_find_next_available_slot_returns_none_when_full`) to verify the algorithm returns `"None available today"` when the day is fully booked.

**Files modified:**

- `pawpal_system.py` — Added `Scheduler.find_next_available_slot()`
- `main.py` — Added the "NEXT AVAILABLE SLOT" table
- `tests/test_pawpal.py` — Added 3 new tests
- `demo_output.txt` — Regenerated

---

## Prompt Comparison (SF11)

**Task given to both models:**

```
I have a Python class called Scheduler for a pet care app with these methods:
sort_by_time, sort_by_priority, filter_by_completion, filter_by_pet_name,
detect_conflicts, handle_recurring, find_next_available_slot.

Each Task has: description, time ("HH:MM"), due_date, completed,
frequency ("once"|"daily"|"weekly"), priority ("high"|"medium"|"low").

I want to add a NEW method that detects overlapping tasks — where one task's
start time falls within another's duration window. Assume every task takes
30 minutes.

Propose the method signature and a Python implementation.
```

### Model A — Gemini

```python
def find_overlapping_tasks(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
    """Detects pairs of tasks that overlap in time, assuming each task takes 30 minutes.

    Args:
        tasks: List of Task objects, each with a .time attribute in "HH:MM" format.

    Returns:
        A list of tuples, where each tuple contains two overlapping Task objects.
    """

    def time_to_minutes(time_str: str) -> int:
        hrs, mins = map(int, time_str.split(":"))
        return hrs * 60 + mins

    overlapping_pairs = []
    sorted_tasks = sorted(tasks, key=lambda t: time_to_minutes(t.time))

    for i in range(len(sorted_tasks)):
        start_a = time_to_minutes(sorted_tasks[i].time)
        end_a = start_a + 30
        for j in range(i + 1, len(sorted_tasks)):
            start_b = time_to_minutes(sorted_tasks[j].time)
            if start_b >= end_a:
                break
            overlapping_pairs.append((sorted_tasks[i], sorted_tasks[j]))
    return overlapping_pairs
```

### Model B — ChatGPT

```python
def detect_overlaps(self, tasks: list["Task"]) -> list[tuple["Task", "Task"]]:
    """Return pairs of tasks whose 30-minute time windows overlap."""
    overlaps = []

    def to_minutes(time_str: str) -> int:
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes

    sorted_tasks = sorted(tasks, key=lambda task: to_minutes(task.time))

    for i, task_a in enumerate(sorted_tasks):
        start_a = to_minutes(task_a.time)
        end_a = start_a + 30
        for task_b in sorted_tasks[i + 1 :]:
            start_b = to_minutes(task_b.time)
            if start_b >= end_a:
                break
            if start_b >= start_a:
                overlaps.append((task_a, task_b))
    return overlaps
```

### Comparison Table

| Aspect | Gemini (`find_overlapping_tasks`) | ChatGPT (`detect_overlaps`) |
|---|---|---|
| **Method name** | Verbose, less consistent with existing API | Concise, matches existing `detect_conflicts` |
| **Loop style** | `range(len(...))` + index access | `enumerate()` + slicing (more Pythonic) |
| **Type hints** | Direct `list[Task]` | Quoted `list["Task"]` (unnecessary forward ref) |
| **Redundant checks** | None | Has `if start_b >= start_a:` — always true after sort |
| **Docstring** | Detailed (Args / Returns) | One line only |
| **Early break optimization** | ✅ Uses `if start_b >= end_a: break` | ✅ Same |
| **Correctness** | ✅ Both produce identical results | ✅ Same |

### Final Student Decision

I chose a **hybrid** of the two:

- **Method name** from ChatGPT — `detect_overlaps` matches the existing `detect_conflicts` naming convention.
- **Loop style** from ChatGPT — `enumerate()` + slicing is more idiomatic Python than `range(len())`.
- **Docstring** from Gemini — included full Args/Returns so the method is self-documenting.
- **Removed** ChatGPT's redundant `if start_b >= start_a:` check — after sorting, this condition is always true, so it just adds noise.

**Which model was "better"?**

- **ChatGPT** produced more Pythonic code (`enumerate` + slicing).
- **Gemini** produced a better docstring and did not include the redundant check.

Neither was perfect on its own. The best result came from combining the strengths of each and verifying the behavior with a hand-traced example (`test_detect_overlaps_within_30_min_window`).

### Observation neither model made

Neither model pointed out that the `try/except TypeError` block in the original `check_guess`-style code is **dead code in Python 3** — comparing an `int` to a `str` with `>` raises `TypeError` only if the types are incompatible, but the outer logic already ensures both are integers when the function is called. Removing it would be more Pythonic, but I kept the fix minimal to avoid introducing regressions.

---

## Test Generation (Bonus)

**Prompt used:**

```
I need pytest tests for my PawPal+ system with these classes: Task, Pet,
Owner, Scheduler. Write tests covering: mark_complete, add_task,
get_incomplete_tasks, get_all_tasks, sort_by_time, sort_by_priority,
detect_conflicts, detect_overlaps, handle_recurring, find_next_available_slot,
and JSON round-trip. Use date.today() for due_date.
```

**AI-suggested tests (28 total, all passing):**

| # | Test | Verifies |
|---|---|---|
| 1 | `test_mark_complete_changes_status` | `Task.mark_complete()` sets `completed = True` |
| 2 | `test_task_default_priority_is_medium` | Default priority is `"medium"` |
| 3 | `test_task_default_frequency_is_once` | Default frequency is `"once"` |
| 4 | `test_task_to_dict_roundtrip` | Task JSON serialization round-trips correctly |
| 5 | `test_add_task_increases_count` | `Pet.add_task()` appends to `tasks` |
| 6 | `test_get_incomplete_tasks_filters_correctly` | Incomplete filter excludes completed tasks |
| 7 | `test_pet_to_dict_roundtrip` | Pet JSON serialization round-trips |
| 8 | `test_owner_get_all_tasks_combines_pets` | `Owner.get_all_tasks()` returns combined list |
| 9 | `test_owner_get_all_tasks_empty` | Empty owner returns empty list |
| 10 | `test_owner_to_dict_roundtrip` | Owner JSON serialization round-trips |
| 11 | `test_scheduler_sort_by_time` | Chronological sort by "HH:MM" string |
| 12 | `test_sort_by_priority_high_before_low` | Priority-first sort order |
| 13 | `test_sort_by_priority_ties_broken_by_time` | Time breaks ties within same priority |
| 14 | `test_filter_by_completion` | Completion filter |
| 15 | `test_filter_by_pet_name` | Pet name filter |
| 16 | `test_filter_by_pet_name_returns_empty_for_unknown` | Unknown pet returns empty |
| 17 | `test_detect_conflicts_finds_duplicates` | Same-time conflicts detected |
| 18 | `test_detect_conflicts_empty_list` | Empty list handled |
| 19 | `test_detect_overlaps_within_30_min_window` | 07:00 + 07:15 overlap detected |
| 20 | `test_detect_overlaps_no_overlap_exact_boundary` | 07:00 + 07:30 do NOT overlap |
| 21 | `test_handle_recurring_daily` | Daily tasks generate +1 day |
| 22 | `test_handle_recurring_weekly` | Weekly tasks generate +7 days |
| 23 | `test_handle_recurring_once_returns_none` | `once` returns `None` |
| 24 | `test_find_next_available_slot_returns_first_gap` | First free gap is 06:00 |
| 25 | `test_find_next_available_slot_after_dense_morning` | Dense morning returns 10:00 |
| 26 | `test_find_next_available_slot_returns_none_when_full` | Fully-booked day returns "None available today" |
| 27 | `test_json_save_and_load_roundtrip` | Full Owner JSON round-trip |
| 28 | `test_json_load_missing_file_returns_empty` | Missing file returns empty owner |

**Verification:** `python -m pytest -v` → **28 passed in ~1.4s**, with **100% coverage** on `pawpal_system.py`.

---

## Summary

| AI Interaction | Outcome |
|---|---|
| **Agent Workflow (SF7)** | Used Gemini to draft `find_next_available_slot()` — verified against hand-computed cases |
| **Prompt Comparison (SF11)** | Compared ChatGPT vs Gemini on `detect_overlaps()` — chose hybrid of both |
| **Test Generation** | AI proposed all 28 tests; I reviewed, verified, and added edge cases |
| **Design Review** | Both models challenged my design — most suggestions rejected with documented reasoning |
| **Total AI-generated code accepted** | ~15% (skeletons, boilerplate) |
| **Total AI-generated code rejected or heavily modified** | ~85% |