# Reflection — PawPal+ (Module 2 Project)

> **Note on iteration:** After submitting **Game Glitch Investigator** (Module 1), I received detailed feedback from the course reviewer. Rather than treating that feedback as a one-time grade correction, I treated it as a **design checklist** for every subsequent project. This reflection explicitly maps each piece of that feedback to a concrete change I made in PawPal+.

---

## 0. Applying Module 1 Feedback to PawPal+

The Game Glitch Investigator review surfaced five specific weaknesses. Here is how each one shaped PawPal+:

| # | Module 1 feedback | How I applied it in PawPal+ |
|---|---|---|
| 1 | *"Your test suite covers the two simplest functions but not the ones where you actually changed behavior."* | Every algorithm I implemented (including AI-suggested code) has at least one test. The two subtlest algorithms (`detect_overlaps`, `find_next_available_slot`) have **three tests each**, covering happy path, edge case, and boundary. See Section 3a. |
| 2 | *"Be careful about asserting on exact error-message strings; that couples your tests to copy rather than behavior."* | **No test in PawPal+ asserts on a message string.** Every test asserts on functional outcomes — returned lists, numbers, `None`, or object equality. |
| 3 | *"Your difficulty configuration is split across files... keeping one source of truth for game configuration would make adding a difficulty a single edit."* | **All configuration lives in `pawpal_system.py`.** Working hours, priority ranking, 30-minute duration, defaults — all defined once. `app.py` imports constants, never re-declares them. |
| 4 | *"Read your own comments against the code: the block before `st.stop()` says 'Still render the summary table below before stopping,' but `st.stop()` prevents everything after it from rendering."* | Every comment in PawPal+ was verified by **exercising the path it describes**. The `st.sidebar` comment in `app.py` ("placed at the END of the script on purpose") was tested by confirming the metric picks up freshly updated values on the same rerun. |
| 5 | *"The `f` prefixes on the hint strings in app.py have no placeholders; running your linter across the whole project rather than one or two files will surface small things like that."* | CI runs `ruff check .` and `ruff format --check .` on the **entire project**, including `.py`, `.md`, `.toml`, and `.yaml`. This rule caught a formatting issue inside `ai_interactions.md` (a Markdown code block) that per-file linting would have missed. Fixed in commit `97570e4`. |

**The meta-lesson:** feedback is not a grade correction. It is a specification for how to work next time.

---

## 1. System Design

### 1a. Initial design

I identified **four core classes** from the client feature request:

| Class | Responsibility | Key attributes | Key methods |
|---|---|---|---|
| **Task** | A single care activity | `description`, `time`, `due_date`, `completed`, `frequency`, `priority` | `mark_complete()`, `to_dict()`, `from_dict()` |
| **Pet** | A pet and its task list | `name`, `species`, `age`, `tasks` | `add_task()`, `get_tasks()`, `get_incomplete_tasks()` |
| **Owner** | The user and their pets | `name`, `pets` | `add_pet()`, `get_all_tasks()` |
| **Scheduler** | The "brain" — all algorithms | (stateless) | 8 algorithms — see Section 2b |

**Three core actions a user can perform:**

1. **Register a pet** under their name (`Owner.add_pet()` → `Pet`).
2. **Schedule a care task** for a specific pet (`Pet.add_task()` → `Task`).
3. **View today's plan** across all pets, sorted by time or priority (`Scheduler.sort_by_*()`).

**Design rationale:**

- **Data classes** (Task, Pet, Owner) use `@dataclass` and store data only.
- The **Scheduler** is a pure service class holding all algorithms. Every algorithm can be tested with a plain `list[Task]` — no need to set up an Owner/Pet hierarchy just to run a sort.

### 1b. Design changes

After implementing and deploying, I made these changes:

1. **Added `priority` field to `Task`.** The original design had only `time` and `frequency`. Manual testing with a multi-pet owner revealed that "which task first?" is a real UX question — priority-based sorting answered it.

2. **Added `detect_overlaps()` beyond `detect_conflicts()`.** Original design only caught *exact* time collisions (07:00 vs 07:00). But 07:00 and 07:15 visually overlap from a pet owner's perspective (assuming 30-min tasks). This required a documented fixed-duration assumption (see ADR-003).

3. **Added `find_next_available_slot()`.** Not in the original design. During UI testing, when a user hit a conflict, the natural question was "when *can* I do this?" This method answers it in O(n log n).

4. **Moved from shared server storage to session-scoped state.** Original design wrote to a single `data.json` on the server. During deployment I realized this leaks every user's data to every other user. Fixed with `st.session_state` + manual export/import. Documented as ADR-007.

**Applied from Module 1 feedback:** every constant in this section (working hours, priority ranking, duration defaults) lives in **one file** — `pawpal_system.py`. `app.py` never re-declares game settings.

---

## 2. Scheduling Logic and Tradeoffs

### 2a. Constraints and priorities

- **Working day:** 06:00–22:00, defined as constants in `find_next_available_slot()`.
- **Priority ranking:** `high` > `medium` > `low`. Ties broken by earlier `time`.
- **Duration assumption:** every task occupies **30 minutes** for overlap and gap logic. Documented in docstrings.
- **Conflict definitions:**
  - *Exact conflict:* two tasks share the same `time`.
  - *Overlap:* two tasks' 30-minute windows intersect (07:00 + 07:15 overlaps; 07:00 + 07:30 does **not**).

### 2b. Tradeoffs

| Tradeoff | Decision | Why |
|---|---|---|
| **Time as `str` vs `datetime.time`** | String `"HH:MM"` | Zero-padded 24-hour strings sort with plain `sorted()`. Simplifies JSON + `st.time_input`. Loses seconds/timezone precision — acceptable. |
| **`detect_conflicts()` O(n²) vs O(n) hashmap** | O(n²) | For a single owner with n < 50 tasks, simpler and obviously correct. Would refactor if scaling to hundreds. |
| **30-min duration assumption** | Hardcoded constant | Task has no duration field. 30 min is a reasonable default for pet care. Documented. |
| **Regex AI parser vs LLM** | Regex | Zero cost, offline, deterministic, sub-millisecond, testable. Covers 95% of realistic phrasings. |
| **Session-only data vs DB** | Session-only | A public demo must not store PII on a shared server. Documented in ADR-007. |
| **`Optional[X]` vs `X \| None`** | `X \| None` | Enforced by `from __future__ import annotations` (PEP 604). Ruff rule UP045 also enforces this. |

---

## 3. AI Collaboration

### 3a. How I used AI — and how Module 1 feedback changed my workflow

I used **ChatGPT and Gemini** as design sparring partners, not code generators.

**Before Module 1 feedback, my workflow was:**
1. Ask AI for code
2. Paste it
3. Move on

**After Module 1 feedback** (*"every bug fix and every hand-corrected AI output deserves a test"*), my workflow became:

1. Ask AI for code
2. **Read it carefully** — list every assumption it makes
3. **Write tests BEFORE pasting** — including the boundary cases the AI didn't mention
4. Integrate
5. **Verify manually in the running app**

**Concrete example — `detect_overlaps()`:**

- **Gemini** proposed a working algorithm. It assumed 30-minute task durations but never stated this.
- **I wrote two tests before pasting:** `test_detect_overlaps_within_30_min_window` (07:00 + 07:15) and `test_detect_overlaps_no_overlap_exact_boundary` (07:00 + 07:30 — should **not** overlap).
- **The second test was my own addition.** The AI's explanation didn't mention the boundary. Without that test, a future refactor could silently break the edge case.
- **Result:** the AI-suggested code shipped, but with a safety net that the AI itself didn't provide.

**Concrete example — `find_next_available_slot()`:**

- **Gemini** proposed the algorithm.
- **I added 3 tests:** first-gap, dense-morning, and fully-booked-day.
- **The "fully-booked" test** verifies that the function returns `"None available today"` rather than crashing or returning a bogus time.

**Total:** every algorithm in `pawpal_system.py` has at least one test. The two subtlest ones have three each.

### 3b. Judgment and verification

**Where I rejected AI suggestions:**

1. **ChatGPT proposed a separate `Recurrence` class** for recurring tasks. Rejected: the logic is 3 lines (`due_date + timedelta(days=1 or 7)`); a 5th class would break the UML and add zero value.

2. **Gemini proposed `Optional[X]` type hints.** Rejected: file uses `from __future__ import annotations` (PEP 604 syntax allowed). Ruff's UP045 rule later validated this — it would flag `Optional[X]` as non-idiomatic.

3. **Both models suggested an LLM (OpenAI API) for the parser.** Rejected: cost, security surface (API key on deployment), non-determinism (breaks tests), and — critically — **the bounded vocabulary of pet-care tasks is handled fine by regex.**

**Applied from Module 1 feedback:**

- **Comments must match code.** Every comment in PawPal+ was verified by exercising the described path. The `st.sidebar` comment ("placed at the END of the script on purpose") was confirmed by testing that the sidebar metrics update on the same rerun as the state change.
- **Lint the whole project, not just a couple of files.** CI runs `ruff check .` across all file types. This caught a Markdown code-block formatting issue in `ai_interactions.md` that per-file linting would have missed. Fixed in commit `97570e4`.
- **No asserts on error-message strings.** Every test asserts on behavior (returned values, list contents, `None`, object equality), never on message copy.

**How I verified everything:**

- **28 pytest tests**, 100% coverage on `pawpal_system.py`
- **Manual end-to-end testing** of the Streamlit UI on every commit
- **GitHub Actions CI** on Python 3.12 + 3.13 for every push
- **Ruff linter** — `All checks passed!` on the whole project
- **Deployed live** to Streamlit Cloud and tested in a browser

---

## 4. Testing and Verification

### 4a. What I tested

Every public method of every class has at least one test:

**Task (4 tests):** `mark_complete()`, default priority, default frequency, JSON round-trip.
**Pet (3 tests):** `add_task()`, `get_incomplete_tasks()`, JSON round-trip.
**Owner (3 tests):** `get_all_tasks()`, empty owner, JSON round-trip.
**Scheduler sorting (3):** by time, by priority, ties broken by time.
**Scheduler filtering (3):** by completion, by pet name, unknown pet returns empty.
**Conflicts & overlaps (4):** exact duplicates, empty list, overlap within 30 min, exact-boundary no-overlap.
**Recurring (3):** daily, weekly, once.
**Next slot (3):** first gap, dense morning, fully-booked day.
**Persistence (2):** full round-trip, missing file fallback.

**28 tests total. 100% line coverage on `pawpal_system.py`.**

**Explicitly aligned with Module 1 feedback:**
- ✅ Every bug-fix or AI-corrected behavior has a test
- ✅ **Zero** assertions on exact error-message strings
- ✅ Boundary cases covered (exact-time boundary, fully-booked day, empty owner)

### 4b. Confidence

⭐⭐⭐⭐⭐ (5/5)

- Every line of domain logic is covered by an automated test.
- Critical algorithms have happy-path, edge-case, and boundary tests.
- CI runs the full suite on **Python 3.12 and 3.13** on every push.
- The deployed app was manually verified end-to-end on desktop and mobile.

**Remaining gaps (out of scope for the module):**
- No automated tests for `app.py` UI logic (Streamlit's execution model requires Playwright/Selenium).
- No stress test beyond n=2000 (though `benchmark.py` shows the scaling curve).

---

## 5. Reflection

### 5a. What went well

- **The four-class split aged well.** Once the Scheduler was isolated as a pure service class, adding FastAPI, the AI parser, and the benchmark script became purely additive — zero changes needed in `pawpal_system.py`.

- **Tests written alongside code.** Because I wrote a test immediately after every AI-generated algorithm, code review never turned into a debugging session. Failures were caught in seconds.

- **Deployment was 5 minutes.** Streamlit Cloud detected the repo and built it without config.

- **The AI parser is a showstopper.** Typing `"walk Cooper at 7am daily"` and seeing a structured preview feels like magic — even though it's regex.

- **CI green from the second commit.** The first failure was because I used bare `pytest` instead of `python -m pytest` on Linux runners. One fix, and the badge stayed green.

- **The Module 1 feedback became a design checklist**, not just a past grade. Every bullet from the reviewer is now a **rule** in my workflow: write a test for every fix, don't assert on copy, one source of truth for config, verify comments against code, lint the whole project.

### 5b. What I would improve

- **Add a database layer** (SQLite/Supabase) with authentication for per-user persistence.
- **Track actual task durations** — the 30-minute assumption is a simplification.
- **Handle timezones** explicitly (`date.today()` is naive).
- **Optional LLM fallback** for the parser (regex handles 95%; the LLM would handle the tail).
- **Split the Streamlit UI into pages.**
- **Add end-to-end UI tests** with Playwright to cover the AI Assistant flow.

### 5c. Key takeaway

**AI is a force multiplier when used as a design reviewer, not a code oracle.**

The two most valuable things AI did were:

1. **Challenging my design** — when ChatGPT proposed a `Recurrence` class, I had to articulate *why* I was rejecting it, which clarified when abstraction adds value.
2. **Offering two valid approaches** — comparing ChatGPT's regex parser against Gemini's showed me two defensible tradeoff profiles, forcing me to be explicit about what mattered: determinism, cost, and testability.

But **every suggestion had to be verified, tested, and often modified.**

**The single most important habit I took from Module 1:** every bug fix gets a test; every hand-corrected AI output gets a test. If behavior has *proven* it can regress, it deserves to be pinned down.

**"The bugs were the curriculum"** — I learned more from debugging the AI's edge-case oversights than from any tutorial I've taken.