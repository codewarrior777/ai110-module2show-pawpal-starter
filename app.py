"""Streamlit UI for PawPal+ — the smart pet care management system.

SECURITY NOTE:
    This is a public demo. User data is scoped to the browser session
    only and is NOT stored on the server. Users can export/import their
    data manually via the download/upload buttons.

AI FEATURE:
    The "🪄 AI Assistant" tab accepts free-form text like
    "walk Cooper at 7am daily, high priority" and uses the regex-based
    parser in nl_parser.py to extract a structured Task.
"""

import json
from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task


def _is_onboarded(owner: Owner) -> bool:
    """Return True if the owner has completed onboarding (name is set)."""
    return bool(owner.name and owner.name.strip() and owner.name != "New User")


def _init_session() -> None:
    """Initialize session-scoped state (NOT persisted to server)."""
    if "owner" not in st.session_state:
        st.session_state.owner = Owner(name="New User")
    if "scheduler" not in st.session_state:
        st.session_state.scheduler = Scheduler()
    if "ai_parsed" not in st.session_state:
        st.session_state.ai_parsed = None


def main() -> None:
    st.set_page_config(page_title="PawPal+", page_icon="🐾")

    _init_session()
    owner: Owner = st.session_state.owner
    scheduler: Scheduler = st.session_state.scheduler

    # ------------------------------------------------------------------
    # SECURITY DISCLAIMER
    # ------------------------------------------------------------------
    st.warning(
        "⚠️ **Public demo** — Your data lives in this browser session only "
        "and is **NOT stored on the server**. You can download it manually. "
        "Do not enter personal information.",
        icon="🔒",
    )

    # ------------------------------------------------------------------
    # First-run onboarding
    # ------------------------------------------------------------------
    if not _is_onboarded(owner):
        st.title("🐾 Welcome to PawPal+")
        st.caption("Smart Pet Care Management System")
        st.write("Let's get you set up. What should we call you?")

        with st.form("onboarding_form"):
            name = st.text_input("Your name", placeholder="e.g. Gustavo")
            submitted = st.form_submit_button("Start using PawPal+ 🐾")

            if submitted:
                if name.strip():
                    owner.name = name.strip()
                    st.rerun()
                else:
                    st.error("Please enter your name.")

        st.stop()

    # ------------------------------------------------------------------
    # Main app
    # ------------------------------------------------------------------
    st.title(f"🐾 PawPal+ — Welcome, {owner.name}!")
    st.caption("Smart Pet Care Management System")

    # ---- Sidebar ----
    st.sidebar.header(f"👤 {owner.name}")

    with st.sidebar.expander("✏️ Edit name"):
        new_name = st.text_input("New name", value=owner.name, key="edit_name_input")
        if st.button("Save name") and new_name.strip():
            owner.name = new_name.strip()
            st.success(f"Name changed to {owner.name}")
            st.rerun()

    if st.sidebar.button("🔄 Reset session"):
        st.session_state.owner = Owner(name="New User")
        st.session_state.scheduler = Scheduler()
        st.session_state.ai_parsed = None
        st.rerun()

    # ---- Session-scoped persistence ----
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Your Data (session-only)")

    st.sidebar.download_button(
        label="⬇️ Download my data",
        data=json.dumps(owner.to_dict(), indent=2, ensure_ascii=False),
        file_name=f"pawpal_{owner.name.replace(' ', '_').lower()}.json",
        mime="application/json",
        help="Save your pets & tasks to a JSON file on YOUR device.",
    )

    uploaded = st.sidebar.file_uploader(
        "⬆️ Restore from file",
        type=["json"],
        help="Load a previously downloaded PawPal+ JSON file.",
    )
    if uploaded is not None:
        try:
            data = json.loads(uploaded.read().decode("utf-8"))
            st.session_state.owner = Owner.from_dict(data)
            st.sidebar.success(f"Restored {len(data.get('pets', []))} pet(s)")
            st.rerun()
        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as e:
            st.sidebar.error(f"Could not read file: {e}")

    # ---- Dashboard stats ----
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Dashboard")

    all_tasks_for_stats = owner.get_all_tasks()
    if all_tasks_for_stats:
        priority_counts = {"high": 0, "medium": 0, "low": 0}
        for t in all_tasks_for_stats:
            priority_counts[t.priority] += 1

        st.sidebar.metric("Total Tasks", len(all_tasks_for_stats))

        st.sidebar.write("**Tasks by Priority**")
        st.sidebar.bar_chart(
            {
                "Priority": list(priority_counts.keys()),
                "Count": list(priority_counts.values()),
            },
            x="Priority",
            y="Count",
        )

        st.sidebar.write("**Tasks per Pet**")
        pet_task_counts = {p.name: len(p.tasks) for p in owner.pets}
        st.sidebar.bar_chart(
            {
                "Pet": list(pet_task_counts.keys()),
                "Tasks": list(pet_task_counts.values()),
            },
            x="Pet",
            y="Tasks",
        )
    else:
        st.sidebar.info("Add tasks to see stats.")

    # ---- Registered pets list ----
    st.sidebar.markdown("---")
    st.sidebar.subheader("Registered Pets")
    if owner.pets:
        for p in owner.pets:
            st.sidebar.write(f"• **{p.name}** ({p.species}, {p.age} yrs)")
    else:
        st.sidebar.info("No pets registered yet.")

    # ------------------------------------------------------------------
    # Main UI Tabs
    # ------------------------------------------------------------------
    tab_pet, tab_task, tab_ai, tab_schedule = st.tabs(
        ["🐶 Add Pet", "📝 Add Task", "🪄 AI Assistant", "📅 Today's Schedule"]
    )

    # ------------------------------------------------------------------
    # TAB 1: Add Pet
    # ------------------------------------------------------------------
    with tab_pet:
        st.subheader("Add a New Pet")
        with st.form("add_pet_form", clear_on_submit=True):
            pet_name = st.text_input("Pet Name")
            species = st.selectbox(
                "Species", ["Dog", "Cat", "Bird", "Fish", "Reptile", "Other"]
            )
            age = st.number_input("Age", min_value=0, max_value=30, value=1)
            submitted_pet = st.form_submit_button("Add Pet")

            if submitted_pet:
                if pet_name.strip():
                    new_pet = Pet(name=pet_name.strip(), species=species, age=int(age))
                    owner.add_pet(new_pet)
                    st.success(f"Added **{new_pet.name}** to your pets!")
                    st.rerun()
                else:
                    st.error("Please enter a valid pet name.")

        st.markdown("---")
        st.subheader("Current Pets")
        if owner.pets:
            for pet in owner.pets:
                st.write(
                    f"🐾 **{pet.name}** — {pet.species}, {pet.age} years old "
                    f"({len(pet.tasks)} tasks)"
                )
        else:
            st.info("No pets added yet. Use the form above to add your first pet!")

    # ------------------------------------------------------------------
    # TAB 2: Add Task (manual)
    # ------------------------------------------------------------------
    with tab_task:
        st.subheader("Add a Task for a Pet")
        if not owner.pets:
            st.warning("Please add at least one pet before creating tasks.")
        else:
            pet_names = [pet.name for pet in owner.pets]
            selected_pet_name = st.selectbox("Select Pet", pet_names)

            with st.form("add_task_form", clear_on_submit=True):
                description = st.text_input("Task Description")
                task_time = st.time_input("Task Time")
                frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
                priority = st.selectbox("Priority", ["high", "medium", "low"], index=1)
                submitted_task = st.form_submit_button("Add Task")

                if submitted_task:
                    if description.strip():
                        formatted_time = task_time.strftime("%H:%M")
                        new_task = Task(
                            description=description.strip(),
                            time=formatted_time,
                            due_date=date.today(),
                            frequency=frequency,
                            priority=priority,
                        )

                        target_pet = next(
                            (p for p in owner.pets if p.name == selected_pet_name),
                            None,
                        )
                        if target_pet:
                            target_pet.add_task(new_task)
                            st.success(
                                f"Task **'{new_task.description}'** added for "
                                f"**{target_pet.name}** at {new_task.time} "
                                f"({new_task.priority} priority)!"
                            )
                            st.rerun()
                    else:
                        st.error("Please enter a task description.")

    # ------------------------------------------------------------------
    # TAB 3: AI Assistant — Natural Language Parsing
    # ------------------------------------------------------------------
    with tab_ai:
        st.subheader("🪄 AI Task Assistant")
        st.write(
            "Describe a task in natural language and let the parser "
            "extract the details."
        )

        st.code(
            'Examples:  "walk Cooper at 7am daily, high priority"  ·  '
            '"feed the cat at 18:30"  ·  "vet visit tomorrow at 2pm"',
            language="text",
        )

        if "ai_parsed" not in st.session_state:
            st.session_state.ai_parsed = None

        nl_text = st.text_input(
            "Describe your task:",
            placeholder="walk Cooper at 7am daily, high priority",
            key="ai_nl_input",
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            parse_btn = st.button("🪄 Parse", type="primary")
        with col2:
            if st.button("✖ Clear"):
                st.session_state.ai_parsed = None
                st.rerun()

        if parse_btn:
            if not nl_text.strip():
                st.error("Please enter some text first.")
            else:
                try:
                    from nl_parser import parse_task as _parse

                    known_pets = [p.name for p in owner.pets]
                    parsed = _parse(nl_text, known_pets)
                    st.session_state.ai_parsed = parsed
                except ValueError as e:
                    st.session_state.ai_parsed = None
                    st.error(f"Could not parse: {e}")

        parsed = st.session_state.ai_parsed
        if parsed is not None:
            st.markdown("---")
            st.subheader("📋 Preview")

            col_a, col_b = st.columns(2)
            col_a.metric("Time", parsed.time)
            col_b.metric("Priority", parsed.priority.upper())

            col_c, col_d = st.columns(2)
            col_c.metric("Frequency", parsed.frequency)
            col_d.metric("Pet", parsed.pet_name or "—")

            st.info(f"**Description:** {parsed.description}")

            if owner.pets:
                pet_names = [p.name for p in owner.pets]
                default_idx = 0
                if parsed.pet_name and parsed.pet_name in pet_names:
                    default_idx = pet_names.index(parsed.pet_name)

                target_pet_name = st.selectbox(
                    "Add to which pet?",
                    pet_names,
                    index=default_idx,
                    key="ai_target_pet",
                )

                if st.button("✅ Confirm and Add Task", type="primary"):
                    target_pet = next(
                        (p for p in owner.pets if p.name == target_pet_name),
                        None,
                    )
                    if target_pet:
                        new_task = Task(
                            description=parsed.description,
                            time=parsed.time,
                            due_date=date.today(),
                            frequency=parsed.frequency,
                            priority=parsed.priority,
                        )
                        target_pet.add_task(new_task)
                        st.success(
                            f"✅ Added **'{parsed.description}'** to "
                            f"**{target_pet.name}** at {parsed.time} "
                            f"({parsed.priority} priority, {parsed.frequency})"
                        )
                        st.session_state.ai_parsed = None
                        st.balloons()
            else:
                st.warning(
                    "You need at least one pet before adding tasks. "
                    "Go to the '🐶 Add Pet' tab first."
                )

    # ------------------------------------------------------------------
    # TAB 4: Today's Schedule
    # ------------------------------------------------------------------
    with tab_schedule:
        st.subheader("Today's Care Schedule")
        all_tasks = owner.get_all_tasks()

        if not all_tasks:
            st.info("No tasks scheduled for today!")
        else:
            incomplete_tasks = scheduler.filter_by_completion(
                all_tasks, completed=False
            )
            completed_tasks = scheduler.filter_by_completion(all_tasks, completed=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Tasks", len(all_tasks))
            col2.metric("Incomplete", len(incomplete_tasks))
            col3.metric("Completed", len(completed_tasks))

            st.markdown("---")

            conflicts = scheduler.detect_conflicts(all_tasks)
            if conflicts:
                st.warning("⚠️ **Schedule Conflicts Detected!**")
                for t1, t2 in conflicts:
                    st.write(
                        f"• Collision at **{t1.time}**: "
                        f"*'{t1.description}'* and *'{t2.description}'*"
                    )
                st.markdown("---")

            overlaps = scheduler.detect_overlaps(all_tasks)
            if overlaps:
                st.warning("⚠️ **30-Minute Window Overlaps Detected!**")
                for t1, t2 in overlaps:
                    st.write(
                        f"• Overlap between **{t1.time}** "
                        f"(*{t1.description}*) and **{t2.time}** "
                        f"(*{t2.description}*)"
                    )
                st.markdown("---")

            st.subheader("📋 Scheduled Tasks")
            sorted_tasks = scheduler.sort_by_time(all_tasks)

            for i, task in enumerate(sorted_tasks):
                pet_owner = next(
                    (p.name for p in owner.pets if task in p.tasks),
                    "Unknown",
                )

                cols = st.columns([1, 3, 2, 2, 2])
                cols[0].write(f"**{task.time}**")
                cols[1].write(f"{task.description} (*{pet_owner}*)")
                cols[2].write(f"Priority: `{task.priority}`")
                cols[3].write(f"Freq: `{task.frequency}`")

                if task.completed:
                    cols[4].success("✅ Done")
                else:
                    if cols[4].button(
                        "Mark Done", key=f"complete_{i}_{task.description}"
                    ):
                        task.mark_complete()
                        st.rerun()


if __name__ == "__main__":
    main()
