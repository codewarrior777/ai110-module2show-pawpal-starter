# Architecture Decision Records (ADRs) — PawPal+

This document captures the key architectural decisions made during the design and implementation of PawPal+.

---

## ADR-001: Four-class design with dataclasses

**Status:** Accepted

**Context:**
The system needs to model pets, tasks, owners, and scheduling logic. The Mermaid UML from Phase 1 specified four classes: `Task`, `Pet`, `Owner`, `Scheduler`.

**Decision:**
- Use `@dataclass` for `Task`, `Pet`, `Owner`.
- Use a plain class for `Scheduler`.

**Rationale:**
- Dataclasses give us `__init__`, `__repr__`, and `__eq__` for free.
- The `Scheduler` class contains algorithms, not data.
- The four-class split keeps data separate from behavior.

**Consequences:**
- ✅ Tests can pass plain `list[Task]` without an `Owner`/`Pet` hierarchy.
- ⚠️ Methods like `filter_by_pet_name` take an `Owner`.

---

## ADR-002: `st.session_state` for state persistence in Streamlit

**Status:** Accepted

**Context:**
Streamlit re-executes the entire script on every user interaction.

**Decision:**
Store the `Owner` and `Scheduler` instances in `st.session_state`.

**Rationale:**
- `session_state` is the official Streamlit mechanism for cross-rerun persistence.

**Consequences:**
- ✅ Adding pets / tasks persists across UI interactions.
- ⚠️ The "Reset" button must explicitly reset `session_state.owner`.

---

## ADR-003: JSON over CSV for persistence

**Status:** Accepted

**Context:**
The stretch feature requires persistent storage.

**Decision:**
Use JSON with `indent=4` and `ensure_ascii=False`.

**Rationale:**
- JSON natively handles nested structures.
- Emojis render correctly with `ensure_ascii=False`.

**Consequences:**
- ✅ Simple `to_dict()` / `from_dict()` round-trip.
- ⚠️ No atomic writes.

---

## ADR-004: Priority-based sort as a tuple sort key

**Status:** Accepted

**Context:**
Tasks have a `priority` field.

**Decision:**
Use a priority-to-integer mapping and a tuple sort key.

**Rationale:**
- Python's `sorted()` is stable and fast.
- Tuple key naturally encodes "priority first, then time".

**Consequences:**
- ✅ Adding a new priority level requires only updating the mapping.

---

## ADR-005: GitHub Actions CI with Python 3.12 + 3.13 matrix

**Status:** Accepted

**Context:**
We need automated verification on every push.

**Decision:**
Run the test suite on two Python versions with `fail-fast: false`.

**Rationale:**
- Catching version-specific regressions early is valuable.
- `python -m pytest` ensures CWD is added to `sys.path` on Linux.

**Consequences:**
- ✅ CI catches issues local testing might miss.
- ⚠️ Doubles CI minutes.

---

## ADR-006: First-run onboarding for the owner name

**Status:** Accepted

**Context:**
Initially the `Owner` name was hardcoded.

**Decision:**
Show a minimal onboarding form when name is `"New User"`.

**Rationale:**
- Auto-saving during onboarding would overwrite existing data.
- Manual save gives the user explicit control.

**Consequences:**
- ✅ Onboarding feels like a real product.
- ⚠️ Unsaved names are lost on reset — by design.

---

## ADR-007: Per-session state instead of shared server storage

**Status:** Accepted

**Context:**
When deployed to Streamlit Community Cloud, the initial design saved data to a `data.json` file on the server. All users of the public URL would see and modify the same data.

**Decision:**
- Remove server-side `data.json` writes from the deployed web UI.
- Keep all state inside `st.session_state`.
- Offer manual export/import via download/upload buttons.
- Display a disclaimer warning users not to enter personal information.

**Rationale:**
- Eliminates cross-user data leakage without adding an auth layer.
- Preserves the JSON persistence feature for CLI use.

**Consequences:**
- ✅ Users only ever see their own data.
- ✅ No server-side PII storage.
- ⚠️ Users must download/upload data manually.
- ⚠️ Production version would need authentication.

**Roadmap for production:**
1. User authentication (Supabase Auth, Auth0).
2. Per-user storage with row-level security.
3. Encryption at rest.
4. Rate limiting per IP.
5. Audit logging.

---

## ADR-008: FastAPI REST API layer (planned)

**Status:** Proposed

**Context:**
An HTTP API would let any frontend interact with the same domain logic.

**Decision (proposed):**
Add a FastAPI app in `api.py` exposing the Scheduler as REST endpoints.

**Consequences:**
- ✅ Enables third-party integrations.
- ⚠️ Adds dependency on FastAPI + Uvicorn.

---

## ADR-009: Docker containerization (planned)

**Status:** Proposed

**Context:**
A containerized version would be portable to any cloud provider.

**Decision (proposed):**
Add a `Dockerfile` and `docker-compose.yml`.

**Consequences:**
- ✅ Identical environment across dev / staging / production.
- ⚠️ Adds complexity for local development.
