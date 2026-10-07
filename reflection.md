# Reflection — PawPal+ (Module 2 Project)

## 1. System Design

### 1a. Initial design

I identified **four core classes** from the client feature request:

| Class | Responsibility | Key attributes | Key methods |
|---|---|---|---|
| **Task** | A single care activity | `description`, `time`, `due_date`, `completed`, `frequency`, `priority` | `mark_complete()`, `to_dict()`, `from_dict()` |
| **Pet** | A pet and its task list | `name`, `species`, `age`, `tasks` | `add_task()`, `get_tasks()`, `get_incomplete_tasks()` |
| **Owner** | The user and their pets | `name`, `pets` | `add_pet()`, `get_all_tasks()` |
| **Scheduler** | The "brain" — all algorithms | (stateless) | `sort_by_time()`, `sort_by_priority()`, `filter_by_completion()`, `filter_by_pet_name()`, `detect_conflicts()`, `detect_overlaps()`, `handle_recurring()`, `find_next_available_slot()` |

**Three core actions a user can perform:**
1. **Register a pet** under their name (Owner → add_pet → Pet).
2. **Schedule a care task** for a specific pet (Pet → add_task → Task).
3. **View today's plan** across all pets, sorted by time or priority.

**Design rationale:**
- The **data classes** (Task, Pet, Owner) are pure `@dataclass` containers — no behavior beyond tiny helpers.
- The **Scheduler** is a separate service class holding all algorithms. This keeps logic testable in isolation (I can pass a plain `list[Task]` without setting up an Owner/Pet hierarchy).

### 1b. Design changes

After implementing the algorithms and running the Streamlit UI, I made these changes:

1. **Added `priority` field to Task.** The original design only had `time` and `frequency`. After testing, it became clear that a real pet owner cares about "high priority vs low priority", and it enabled a useful sort dimension.

2. **Added `detect_overlaps()` beyond `detect_conflicts()`.** The original design only detected *exact* time collisions. But two tasks at 07:00 and 07:15 visually "overlap" from a pet owner's perspective (assuming 30-minute tasks). Adding this method required deciding on a fixed 30-minute duration assumption (documented in ADR-003 and ADR-004).

3. **Added `find_next_available_slot()`.** Originally not in the design. When a user tries to add a new task and there's a conflict, showing them the next free 30-min or 60-min window is a small feature with high UX payoff.

4. **Switched to session-only data storage for the deployed version.** The original design wrote to a single `data.json` on the server. I realized during deployment that this leaks every user's data to every other user. Fixed by keeping state in `st.session_state` and offering manual export/import. Documented in ADR-007.

---

## 2. Scheduling Logic and Tradeoffs

### 2a. Constraints and priorities

The scheduling logic is built around these constraints:

- **Time window:** The working day is 06:00–22:00 (configurable constant in `find_next_available_slot()`).
- **Priority ordering:** Tasks are ranked `high` > `medium` > `low`. Within the same priority, earlier `time` wins.
- **Duration assumption:** Since Task has no `duration` field, I assume **every task takes 30 minutes** when computing overlaps and gaps. This is a simplification — see Tradeoffs below.
- **Conflict types:**
  - *Exact conflict:* two tasks share the same `time`.
  - *Overlap:* two tasks' 30-minute windows intersect.

### 2b. Tradeoffs

| Tradeoff | Decision | Why |
|---|---|---|
| **Time as string vs `datetime.time`** | Chose string `"HH:MM"` | Zero-padded 24-hour strings sort correctly with default `sorted()`. Simplifies JSON serialization and Streamlit's `st.time_input` integration. Loses seconds/timezone granularity (acceptable). |
| **`detect_conflicts()` O(n²) vs O(n) hashmap** | Chose O(n²) | For a single owner with a handful of pets and tasks, n stays small (< 50). Simpler, obviously correct. Would refactor to a hashmap if scaling to hundreds of tasks. |
| **30-min duration assumption** | Hardcoded constant | Task has no duration field, so overlap/gap logic needs an assumption. 30 min is a reasonable default for pet care tasks (a walk, a feeding). Users can't customize yet. |
| **Regex AI parser vs LLM** | Chose regex | Zero cost, offline, deterministic, sub-millisecond, no flakiness. Covers 95% of realistic phrasings like "walk Cooper at 7am daily, high priority". An LLM layer could handle ambiguous inputs, but the marginal gain doesn't justify the cost. |
| **Session-only data vs DB** | Chose session-only | A public demo should not store PII on a shared server. Manual JSON export/import gives users full control. Documented in ADR-007. |

---

## 3. AI Collaboration

### 3a. How I used AI

I used **ChatGPT and Gemini** as design sparring partners, not code generators. Specifically:

- **UML brainstorming:** I asked ChatGPT to help me enumerate the four candidate classes and their likely attributes/methods. Then I refined the diagram manually.
- **Class scaffolding:** I asked Gemini to generate `@dataclass` skeletons for Task, Pet, and Owner. It initially suggested plain classes with manual `__init__` — I redirected it to `@dataclass` to reduce boilerplate.
- **Algorithm drafting:** I asked for `find_next_available_slot()` and `detect_overlaps()` implementations. It proposed clean algorithms, but I caught a subtle assumption in the overlap logic (30-minute fixed duration) that wasn't documented — I added the docstring myself.
- **Natural language parser:** I asked both models for a regex-based task parser. ChatGPT's version was more Pythonic (used `enumerate()` and slicing); Gemini's was more readable but verbose. I combined the best parts.
- **Refactoring review:** I asked ChatGPT to review `nl_parser.py` for edge cases. It suggested adding a "no time found" error, which I adopted.

### 3b. Judgment and verification

**Where I rejected AI suggestions:**

1. **ChatGPT suggested extracting a `Recurrence` class** to handle recurring tasks separately from `Scheduler`. I rejected this because the logic was only 3 lines (`task.due_date + timedelta(days=1 or 7)`) and adding a 5th class would break the UML I'd already committed to.

2. **Gemini suggested adding `Optional[X]` type hints** to methods that might return `None`. I rejected this because the file uses `from __future__ import annotations`, which allows the cleaner `X | None` syntax. Ruff (in CI) later flagged the same issue — my choice was validated by the linter.

3. **Both models suggested using an LLM (OpenAI API) for the natural language parser.** I rejected this because:
   - It adds cost per request
   - It requires an API key on the deployment (security issue)
   - It's non-deterministic (harder to test)
   - The bounded vocabulary of pet care tasks is handled fine by regex

**How I verified everything:**

- **28 pytest tests**, 100% coverage on `pawpal_system.py`
- **Manual testing** of the Streamlit UI end-to-end
- **GitHub Actions CI** running both tests and linting on every push
- **Ruff linter** clean (`ruff check .` → `All checks passed!`)
- **Deployed live** to Streamlit Cloud and tested in a browser

---

## 4. Testing and Verification

### 4a. What I tested

The test suite (`tests/test_pawpal.py`) covers:

- **Task behavior:** `mark_complete()`, default fields, `to_dict()`/`from_dict()` round-trip
- **Pet behavior:** `add_task()`, `get_incomplete_tasks()` filtering, JSON round-trip
- **Owner behavior:** `get_all_tasks()` aggregation across pets, empty-owner edge case
- **Scheduler sorting:** `sort_by_time()`, `sort_by_priority()` with tie-breaking
- **Scheduler filtering:** by completion, by pet name, unknown-pet returns empty
- **Conflict detection:** duplicate times, empty list, 30-minute overlaps, exact-boundary case
- **Recurring tasks:** daily (+1 day), weekly (+7 days), once (returns `None`)
- **Next-slot finder:** first-gap, dense morning, fully-booked day
- **JSON persistence:** save/load round-trip, missing-file fallback

**28 tests total, 100% line coverage on `pawpal_system.py`.**

### 4b. Confidence

⭐⭐⭐⭐⭐ (5/5)

- Every line of domain logic is covered by an automated test.
- The critical algorithms (conflicts, overlaps, next-slot) are tested with both happy-path and edge cases.
- CI runs the full suite on **Python 3.12 and 3.13** on every push.
- The deployed app was manually verified end-to-end.

**Remaining gaps (out of scope):**
- No tests for `app.py` UI logic (Streamlit makes this harder).
- No stress test beyond 2000 tasks (though `benchmark.py` shows scalability).

---

## 5. Reflection

### 5a. What went well

- **Modular architecture.** The four-class split kept everything testable and made it easy to add the FastAPI layer and AI parser without touching the core.
- **High test coverage from day one.** Writing tests alongside the algorithms caught bugs immediately.
- **Deployment was smooth.** Streamlit Cloud was a 5-minute setup. Having the app live made everything feel "real".
- **The AI parser demo is a showstopper.** Typing `"walk Cooper at 7am daily"` and seeing a structured preview feels like magic, even though it's just regex.
- **CI green from day one.** Once I fixed the `python -m pytest` sys.path issue, the badge was green and stayed green.

### 5b. What you would improve

- **Add a database layer** (SQLite or Supabase) with user authentication so data persists per-user properly.
- **Add task durations.** Currently everything is assumed 30 min. A real app would track actual durations.
- **Better time zone handling.** Using `date.today()` is timezone-naive.
- **Expand the AI parser** with an optional LLM fallback for ambiguous inputs (e.g., "walk the dog sometime in the morning").
- **More UI polish.** Right now the Streamlit UI is functional but plain. Adding tabs animations, custom CSS, and a nicer mobile layout would help.
- **Split the UI into pages.** Streamlit's multi-page pattern would be cleaner than four tabs for a growing app.

### 5c. Key takeaway

**AI is a force multiplier when used as a design reviewer, not a code oracle.**

The two most valuable things AI did for me were:
1. **Challenging my design** (proposing a `Recurrence` class forced me to articulate *why* I was rejecting it).
2. **Comparing multiple approaches** (ChatGPT's regex vs Gemini's regex showed me two valid tradeoff profiles).

But every suggestion had to be **verified, tested, and often modified**. The 28 tests + CI pipeline weren't just for the rubric — they were the safety net that let me accept AI code with confidence.

**"The bugs were the curriculum"** — I learned more from debugging the AI's suggestions than from any tutorial I've taken.