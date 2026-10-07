# 🐾 PawPal+ (Module 2 Project)

[![Live Demo](https://img.shields.io/badge/demo-LIVE-brightgreen?style=for-the-badge&logo=streamlit)](https://pawpal-plus-esqzqdlgrnnjsezv6a7r4f.streamlit.app)
[![Tests](https://img.shields.io/badge/tests-28%20passing-brightgreen)](https://github.com/codewarrior777/ai110-module2show-pawpal-starter/actions)
[![Lint](https://github.com/codewarrior777/ai110-module2show-pawpal-starter/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/codewarrior777/ai110-module2show-pawpal-starter/actions/workflows/lint.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](#-testing-pawpal)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](#getting-started)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

---

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

---

## 📋 Sample Output

Sample of the CLI output from running `python main.py` (also saved in `demo_output.txt`):

```
🐾 WELCOME TO PAWPAL+ DEMO | Owner: Gustavo 🐾
============================================================

📅 TODAY'S SCHEDULE (Sorted by Time)

╒════════╤════════════════╤════════╤══════════╤═══════════╤═════════════╕
│ Time   │ Task           │ Pet    │ Priority │ Frequency │ Status      │
╞════════╪════════════════╪════════╪══════════╪═══════════╪═════════════╡
│ 07:00  │ Morning walk   │ Cooper │ HIGH     │ daily     │ ✅ Done     │
│ 08:00  │ Playtime       │ Cooper │ MEDIUM   │ daily     │ ⏳ Pending  │
│ 08:00  │ Feed breakfast │ Prince │ HIGH     │ daily     │ ⏳ Pending  │
│ 14:00  │ Vet appointment│ Cooper │ LOW      │ once      │ ⏳ Pending  │
╘════════╧════════════════╧════════╧══════════╧═══════════╧═════════════╛

⭐ PRIORITY SCHEDULE (High → Medium → Low, then Time)
╒══════════╤════════╤════════════════╤════════╕
│ Priority │ Time   │ Task           │ Pet    │
╞══════════╪════════╪════════════════╪════════╡
│ HIGH     │ 07:00  │ Morning walk   │ Cooper │
│ HIGH     │ 08:00  │ Feed breakfast │ Prince │
│ MEDIUM   │ 08:00  │ Playtime       │ Cooper │
│ LOW      │ 14:00  │ Vet appointment│ Cooper │
╘══════════╧════════╧════════════════╧════════╛

⚠️  CONFLICTS DETECTED
╒════════╤══════════╤════════╤════════╤════════════════╤════════╤════════╕
│ Time   │ Task A   │ Pet A  │ Pri A  │ Task B         │ Pet B  │ Pri B  │
╞════════╪══════════╪════════╪════════╪════════════════╪════════╪════════╡
│ 08:00  │ Playtime │ Cooper │ MEDIUM │ Feed breakfast │ Prince │ HIGH   │
╘════════╧══════════╧════════╧════════╧════════════════╧════════╧════════╛

🕐 NEXT AVAILABLE SLOT
╒════════════╤═══════════════════════════╕
│ Duration   │ Earliest Available Start  │
╞════════════╪═══════════════════════════╡
│ 30 minutes │ 06:00                     │
│ 60 minutes │ 06:00                     │
╘════════════╧═══════════════════════════╛

🔄 RECURRING TASK GENERATION
╒══════════╤════════════════╤════════════╤══════════╕
│          │ Task           │ Due Date   │ Priority │
╞══════════╪════════════════╪════════════╪══════════╡
│ Original │ Morning walk   │ 2026-10-06 │ high     │
│ Next Due │ Morning walk   │ 2026-10-07 │ high     │
╘══════════╧════════════════╧════════════╧══════════╛
```

### Natural Language Parsing (AI Assistant)

The app also accepts free-form text like **"walk Cooper at 7am daily, high priority"** and turns it into a structured `Task`. This is exposed in three places:

1. **CLI:** `python nl_parser.py` (smoke test with 5 examples)
2. **REST API:** `POST /api/parse-task`
3. **Streamlit UI:** the **"🪄 AI Assistant"** tab

---

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest -v

# Run with coverage:
python -m pytest --cov=pawpal_system --cov-report=term-missing
```

### Sample test output

```
$ python -m pytest --cov=pawpal_system --cov-report=term-missing -v
============================= test session starts =============================
collected 28 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED          [  3%]
tests/test_pawpal.py::test_task_default_priority_is_medium PASSED       [  7%]
tests/test_pawpal.py::test_task_default_frequency_is_once PASSED        [ 10%]
tests/test_pawpal.py::test_task_to_dict_roundtrip PASSED                [ 14%]
tests/test_pawpal.py::test_add_task_increases_count PASSED              [ 17%]
tests/test_pawpal.py::test_get_incomplete_tasks_filters_correctly PASSED [ 21%]
tests/test_pawpal.py::test_pet_to_dict_roundtrip PASSED                 [ 25%]
tests/test_pawpal.py::test_owner_get_all_tasks_combines_pets PASSED     [ 28%]
tests/test_pawpal.py::test_owner_get_all_tasks_empty PASSED             [ 32%]
tests/test_pawpal.py::test_owner_to_dict_roundtrip PASSED               [ 35%]
tests/test_pawpal.py::test_scheduler_sort_by_time PASSED                [ 39%]
tests/test_pawpal.py::test_sort_by_priority_high_before_low PASSED      [ 42%]
tests/test_pawpal.py::test_sort_by_priority_ties_broken_by_time PASSED  [ 46%]
tests/test_pawpal.py::test_filter_by_completion PASSED                  [ 50%]
tests/test_pawpal.py::test_filter_by_pet_name PASSED                    [ 53%]
tests/test_pawpal.py::test_filter_by_pet_name_returns_empty_for_unknown PASSED [ 57%]
tests/test_pawpal.py::test_detect_conflicts_finds_duplicates PASSED     [ 60%]
tests/test_pawpal.py::test_detect_conflicts_empty_list PASSED           [ 64%]
tests/test_pawpal.py::test_detect_overlaps_within_30_min_window PASSED  [ 67%]
tests/test_pawpal.py::test_detect_overlaps_no_overlap_exact_boundary PASSED [ 71%]
tests/test_pawpal.py::test_handle_recurring_daily PASSED                [ 75%]
tests/test_pawpal.py::test_handle_recurring_weekly PASSED               [ 78%]
tests/test_pawpal.py::test_handle_recurring_once_returns_none PASSED    [ 82%]
tests/test_pawpal.py::test_find_next_available_slot_returns_first_gap PASSED [ 85%]
tests/test_pawpal.py::test_find_next_available_slot_after_dense_morning PASSED [ 89%]
tests/test_pawpal.py::test_find_next_available_slot_returns_none_when_full PASSED [ 92%]
tests/test_pawpal.py::test_json_save_and_load_roundtrip PASSED          [ 96%]
tests/test_pawpal.py::test_json_load_missing_file_returns_empty PASSED  [100%]

---------- coverage: platform win32, python 3.14.0-final-0 -----------
Name              Stmts   Miss  Cover   Missing
-----------------------------------------------
pawpal_system.py    116      0   100%
-----------------------------------------------
TOTAL               116      0   100%
============================== 28 passed in 1.40s ==============================
```

**Confidence level:** ⭐⭐⭐⭐⭐ (5/5) — every line of `pawpal_system.py` is covered by an automated test.

---

## 🧠 Smarter Scheduling

| Feature | Method(s) | Notes |
|---|---|---|
| **Task sorting** | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority()` | Two sort modes: chronological (HH:MM string sort) and priority-first (high → medium → low), with time as a tiebreaker. |
| **Filtering** | `Scheduler.filter_by_completion()`, `Scheduler.filter_by_pet_name()` | Filter by completion status, or isolate the tasks belonging to a single pet. |
| **Conflict handling** | `Scheduler.detect_conflicts()`, `Scheduler.detect_overlaps()` | `detect_conflicts()` finds exact same-time collisions; `detect_overlaps()` finds 30-minute-window intersections. |
| **Recurring tasks** | `Scheduler.handle_recurring()` | Daily tasks generate the next day's occurrence; weekly tasks generate +7 days. Returns `None` for `once` tasks. |
| **Next available slot** | `Scheduler.find_next_available_slot()` | Scans the 06:00–22:00 working day for the earliest free window of a given duration (30, 60+ min). |
| **Persistence** | `save_owner_to_json()`, `load_owner_from_json()` | Round-trip JSON serialization using `to_dict()` / `from_dict()` on every class with ISO-8601 dates. |

---

## 🎬 Demo Walkthrough

1. User opens the app. A yellow security banner appears explaining the session-scoped data policy.
2. User is prompted to enter their name (first-run onboarding).
3. User navigates to the **"🐶 Add Pet"** tab, enters `Cooper`, `Dog`, `4`, and clicks **Add Pet**. Cooper appears in the sidebar.
4. User goes to the **"🪄 AI Assistant"** tab and types `"walk Cooper at 7am daily, high priority"`.
5. User clicks **Parse**. The preview shows: Time `07:00`, Priority `HIGH`, Frequency `daily`, Pet `Cooper`, Description `Walk Cooper`.
6. User clicks **Confirm and Add Task**. Balloons fly, and a green success message confirms the add.
7. User switches to the **"📅 Today's Schedule"** tab. The task appears sorted by time, with priority badge and a "Mark Done" button.
8. The **Dashboard** in the sidebar shows the priority distribution bar chart updating in real time.

**Screenshot / video (optional):** see `diagrams/README.md` for the rendered UML. Live demo at https://pawpal-plus-esqzqdlgrnnjsezv6a7r4f.streamlit.app.

---

## 🚀 Bonus Features (Beyond the Module)

### AI Natural Language Parser

`nl_parser.py` converts free-form text into structured tasks using regex-based extraction (no LLM required):

| Field | Patterns recognized |
|---|---|
| **Time** | `7am`, `7:30pm`, `07:00`, `19:30`, `14:00` |
| **Frequency** | `daily`, `every day`, `weekly`, `once` |
| **Priority** | `high`, `urgent`, `medium`, `low`, `minor` |
| **Pet name** | Matches registered pets (case-insensitive) |

**Why regex instead of an LLM?** Zero cost, offline, deterministic, sub-millisecond, and testable. An LLM layer could handle ambiguous inputs, but regex covers 95% of realistic pet-care task phrasing.

### REST API (FastAPI)

`api.py` exposes the Scheduler as 15 REST endpoints with auto-generated Swagger docs:

```bash
uvicorn api:app --reload
# → http://127.0.0.1:8000/docs
```

Full endpoint list is available in the Swagger UI. Includes `POST /api/parse-task` for natural language parsing.

### Security Hardening

Deployed as a public demo with **session-scoped data only** (no server-side storage). Users can export/import their data as JSON. See `ARCHITECTURE.md` (ADR-007) for the full decision record.

---

## 📁 Project Structure

```
ai110-module2show-pawpal-starter/
├── .github/workflows/          # CI (Tests + Lint)
├── .streamlit/config.toml      # Streamlit theme
├── diagrams/
│   ├── README.md               # Rendered UML
│   └── uml.mmd                 # Mermaid source
├── tests/
│   └── test_pawpal.py          # 28 tests, 100% coverage
├── app.py                      # Streamlit UI
├── api.py                      # FastAPI REST API
├── nl_parser.py                # AI Natural Language Parser
├── main.py                     # CLI demo
├── pawpal_system.py            # Core domain logic
├── benchmark.py                # Algorithm benchmark
├── demo_output.txt             # Saved CLI output
├── reflection.md               # Design + AI collaboration
├── ai_interactions.md          # Agent workflow + model comparison
├── ARCHITECTURE.md             # 9 Architecture Decision Records
├── CONTRIBUTING.md
├── LICENSE                     # MIT
├── pyproject.toml
├── requirements.txt
├── ruff.toml
├── .pre-commit-config.yaml
└── README.md
```

---

## 🙏 Credits

Built by **Gustavo Ramos** for *AI 110 — Foundations of AI Engineering*.

> *"Ship code you'd be proud to maintain."*

| | |
|---|---|
| **Role** | Lead architect · Solo developer · Own QA |
| **Architecture** | 4 classes · 9 ADRs · 1 UML diagram |
| **Quality** | 28 tests · 100% coverage · 0 lint warnings |
| **Interfaces** | 1 CLI · 1 Streamlit UI · 1 REST API · 1 AI parser |
| **Deployment** | [Streamlit Cloud](https://pawpal-plus-esqzqdlgrnnjsezv6a7r4f.streamlit.app) (live) |
| **Standards** | PEP 8 · PEP 257 · Conventional Commits · SemVer |
| **Assistants** | ChatGPT & Gemini — sparring partners, not autocomplete |

*The bugs were the curriculum.*