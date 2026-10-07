"""Pytest suite for PawPal+ — 20 tests covering all classes and algorithms."""

from datetime import date, timedelta

import pytest

from pawpal_system import (
    Owner,
    Pet,
    Scheduler,
    Task,
    load_owner_from_json,
    save_owner_to_json,
)


@pytest.fixture
def today() -> date:
    return date.today()


@pytest.fixture
def sample_owner(today: date) -> Owner:
    """Create an owner with 2 pets and 4 tasks for reuse."""
    owner = Owner(name="Alex")
    cooper = Pet(name="Cooper", species="Dog", age=4)
    prince = Pet(name="Prince", species="Cat", age=2)

    cooper.add_task(Task("Walk", "07:00", today, priority="high"))
    cooper.add_task(Task("Playtime", "08:00", today, priority="medium"))
    cooper.add_task(Task("Vet visit", "14:00", today, priority="low"))
    prince.add_task(Task("Feed", "08:00", today, priority="high"))

    owner.add_pet(cooper)
    owner.add_pet(prince)
    return owner


# ----------------------------------------------------------------------
# Task tests
# ----------------------------------------------------------------------


def test_mark_complete_changes_status(today):
    t = Task("Walk", "07:00", today)
    assert not t.completed
    t.mark_complete()
    assert t.completed


def test_task_default_priority_is_medium(today):
    t = Task("Walk", "07:00", today)
    assert t.priority == "medium"


def test_task_default_frequency_is_once(today):
    t = Task("Walk", "07:00", today)
    assert t.frequency == "once"


def test_task_to_dict_roundtrip(today):
    t = Task("Walk", "07:00", today, completed=True, frequency="daily", priority="high")
    d = t.to_dict()
    t2 = Task.from_dict(d)
    assert t2.description == t.description
    assert t2.time == t.time
    assert t2.due_date == t.due_date
    assert t2.completed == t.completed
    assert t2.frequency == t.frequency
    assert t2.priority == t.priority


# ----------------------------------------------------------------------
# Pet tests
# ----------------------------------------------------------------------


def test_add_task_increases_count(today):
    pet = Pet("Cooper", "Dog", 4)
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task("Walk", "07:00", today))
    assert len(pet.get_tasks()) == 1


def test_get_incomplete_tasks_filters_correctly(today):
    pet = Pet("Cooper", "Dog", 4)
    t1 = Task("Walk", "07:00", today)
    t2 = Task("Feed", "08:00", today)
    pet.add_task(t1)
    pet.add_task(t2)
    t1.mark_complete()

    incomplete = pet.get_incomplete_tasks()
    assert len(incomplete) == 1
    assert incomplete[0] == t2


def test_pet_to_dict_roundtrip(today):
    pet = Pet("Cooper", "Dog", 4)
    pet.add_task(Task("Walk", "07:00", today, priority="high"))
    d = pet.to_dict()
    pet2 = Pet.from_dict(d)
    assert pet2.name == "Cooper"
    assert pet2.age == 4
    assert len(pet2.tasks) == 1


# ----------------------------------------------------------------------
# Owner tests
# ----------------------------------------------------------------------


def test_owner_get_all_tasks_combines_pets(sample_owner):
    all_tasks = sample_owner.get_all_tasks()
    assert len(all_tasks) == 4


def test_owner_get_all_tasks_empty():
    owner = Owner("Alex")
    assert owner.get_all_tasks() == []


def test_owner_to_dict_roundtrip(sample_owner):
    d = sample_owner.to_dict()
    owner2 = Owner.from_dict(d)
    assert owner2.name == "Alex"
    assert len(owner2.pets) == 2
    assert len(owner2.get_all_tasks()) == 4


# ----------------------------------------------------------------------
# Scheduler: sorting tests
# ----------------------------------------------------------------------


def test_scheduler_sort_by_time(sample_owner):
    s = Scheduler()
    tasks = sample_owner.get_all_tasks()
    sorted_tasks = s.sort_by_time(tasks)
    times = [t.time for t in sorted_tasks]
    assert times == sorted(times)


def test_sort_by_priority_high_before_low(sample_owner):
    s = Scheduler()
    tasks = sample_owner.get_all_tasks()
    sorted_tasks = s.sort_by_priority(tasks)
    # First 2 should be HIGH priority
    assert sorted_tasks[0].priority == "high"
    assert sorted_tasks[1].priority == "high"
    # Last should be LOW
    assert sorted_tasks[-1].priority == "low"


def test_sort_by_priority_ties_broken_by_time(today):
    s = Scheduler()
    t1 = Task("A", "09:00", today, priority="high")
    t2 = Task("B", "07:00", today, priority="high")
    result = s.sort_by_priority([t1, t2])
    assert result[0].description == "B"  # earlier time wins


# ----------------------------------------------------------------------
# Scheduler: filtering tests
# ----------------------------------------------------------------------


def test_filter_by_completion(sample_owner):
    s = Scheduler()
    tasks = sample_owner.get_all_tasks()
    tasks[0].mark_complete()
    complete = s.filter_by_completion(tasks, completed=True)
    incomplete = s.filter_by_completion(tasks, completed=False)
    assert len(complete) == 1
    assert len(incomplete) == 3


def test_filter_by_pet_name(sample_owner):
    s = Scheduler()
    coopers = s.filter_by_pet_name(sample_owner, "Cooper")
    assert len(coopers) == 3
    assert all(t.description != "Feed" for t in coopers)


def test_filter_by_pet_name_returns_empty_for_unknown(sample_owner):
    s = Scheduler()
    assert s.filter_by_pet_name(sample_owner, "Nonexistent") == []


# ----------------------------------------------------------------------
# Scheduler: conflict & overlap tests
# ----------------------------------------------------------------------


def test_detect_conflicts_finds_duplicates(sample_owner):
    s = Scheduler()
    conflicts = s.detect_conflicts(sample_owner.get_all_tasks())
    # Playtime (08:00) and Feed (08:00) share a slot
    assert len(conflicts) == 1


def test_detect_conflicts_empty_list():
    s = Scheduler()
    assert s.detect_conflicts([]) == []


def test_detect_overlaps_within_30_min_window(today):
    s = Scheduler()
    tasks = [
        Task("A", "07:00", today),
        Task("B", "07:15", today),
        Task("C", "09:00", today),
    ]
    overlaps = s.detect_overlaps(tasks)
    assert len(overlaps) == 1


def test_detect_overlaps_no_overlap_exact_boundary(today):
    s = Scheduler()
    tasks = [Task("A", "07:00", today), Task("B", "07:30", today)]
    # 07:30 is exactly when A ends — should NOT overlap
    assert s.detect_overlaps(tasks) == []


# ----------------------------------------------------------------------
# Scheduler: recurring & next slot tests
# ----------------------------------------------------------------------


def test_handle_recurring_daily(today):
    s = Scheduler()
    t = Task("Walk", "07:00", today, frequency="daily")
    nxt = s.handle_recurring(t)
    assert nxt is not None
    assert nxt.due_date == today + timedelta(days=1)


def test_handle_recurring_weekly(today):
    s = Scheduler()
    t = Task("Groom", "10:00", today, frequency="weekly")
    nxt = s.handle_recurring(t)
    assert nxt is not None
    assert nxt.due_date == today + timedelta(days=7)


def test_handle_recurring_once_returns_none(today):
    s = Scheduler()
    t = Task("Vet", "14:00", today, frequency="once")
    assert s.handle_recurring(t) is None


def test_find_next_available_slot_returns_first_gap(today):
    s = Scheduler()
    tasks = [Task("A", "07:00", today), Task("B", "08:00", today)]
    assert s.find_next_available_slot(tasks, 30) == "06:00"


def test_find_next_available_slot_after_dense_morning(today):
    s = Scheduler()
    # Dense tasks from 06:00 to 10:00 (30-min blocks back to back)
    tasks = [
        Task(f"t{i}", f"{6 + i // 2:02d}:{(i % 2) * 30:02d}", today) for i in range(8)
    ]
    # First free 30-min gap should be 10:00
    assert s.find_next_available_slot(tasks, 30) == "10:00"


def test_find_next_available_slot_returns_none_when_full(today):
    s = Scheduler()
    # Tasks every 30 min from 06:00 to 21:30 → no 60-min gap
    tasks = []
    for h in range(6, 22):
        tasks.append(Task(f"a{h}", f"{h:02d}:00", today))
        tasks.append(Task(f"b{h}", f"{h:02d}:30", today))
    assert s.find_next_available_slot(tasks, 60) == "None available today"


# ----------------------------------------------------------------------
# JSON persistence tests
# ----------------------------------------------------------------------


def test_json_save_and_load_roundtrip(sample_owner, tmp_path):
    filepath = tmp_path / "test_data.json"
    save_owner_to_json(sample_owner, str(filepath))
    loaded = load_owner_from_json(str(filepath))
    assert loaded.name == "Alex"
    assert len(loaded.pets) == 2
    assert len(loaded.get_all_tasks()) == 4


def test_json_load_missing_file_returns_empty():
    owner = load_owner_from_json("nonexistent_file_xyz.json")
    assert owner.name == "New User"
    assert owner.pets == []
