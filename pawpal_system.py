"""Module for managing pets, tasks, owners, and scheduling in PawPal+."""

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import ClassVar, Literal


@dataclass
class Task:
    """Represents a single pet care activity."""

    description: str
    time: str
    due_date: date
    completed: bool = False
    frequency: Literal["once", "daily", "weekly"] = "once"
    priority: Literal["high", "medium", "low"] = "medium"

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def to_dict(self) -> dict:
        """Serialize this Task to a JSON-compatible dict."""
        return {
            "description": self.description,
            "time": self.time,
            "due_date": self.due_date.isoformat(),
            "completed": self.completed,
            "frequency": self.frequency,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Reconstruct a Task from a dict (e.g. loaded from JSON)."""
        return cls(
            description=data["description"],
            time=data["time"],
            due_date=date.fromisoformat(data["due_date"]),
            completed=data.get("completed", False),
            frequency=data.get("frequency", "once"),
            priority=data.get("priority", "medium"),
        )


@dataclass
class Pet:
    """Stores pet details and associated care tasks."""

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a new care task to the pet's task list."""
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Retrieve all tasks associated with this pet."""
        return self.tasks

    def get_incomplete_tasks(self) -> list[Task]:
        """Retrieve pending tasks that are not yet marked as completed."""
        return [t for t in self.tasks if not t.completed]

    def to_dict(self) -> dict:
        """Serialize this Pet (and its tasks) to a JSON-compatible dict."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Reconstruct a Pet (and its tasks) from a dict."""
        tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return cls(
            name=data["name"],
            species=data["species"],
            age=data["age"],
            tasks=tasks,
        )


@dataclass
class Owner:
    """Manages owner information and registered pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Retrieve a combined list of all tasks across all owned pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def to_dict(self) -> dict:
        """Serialize this Owner (and its pets) to a JSON-compatible dict."""
        return {
            "name": self.name,
            "pets": [pet.to_dict() for pet in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Reconstruct an Owner (and its pets) from a dict."""
        pets = [Pet.from_dict(p) for p in data.get("pets", [])]
        return cls(name=data["name"], pets=pets)


class Scheduler:
    """Provides utility methods for sorting, filtering, and checking schedules."""

    # Priority ranking — smaller number = higher priority
    _PRIORITY_ORDER: ClassVar[dict[str, int]] = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted chronologically by their time attribute."""
        return sorted(tasks, key=lambda t: t.time)

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """
        Return tasks sorted by priority (high -> medium -> low).
        Within the same priority, tasks are sorted by time.
        """
        return sorted(
            tasks,
            key=lambda t: (
                self._PRIORITY_ORDER.get(t.priority, 1),
                t.time,
            ),
        )

    def filter_by_completion(
        self, tasks: list[Task], completed: bool = True
    ) -> list[Task]:
        """Filter tasks based on their completion status."""
        return [t for t in tasks if t.completed == completed]

    def filter_by_pet_name(self, owner: Owner, pet_name: str) -> list[Task]:
        """Filter tasks belonging to a specific pet by name."""
        for pet in owner.pets:
            if pet.name == pet_name:
                return pet.get_tasks()
        return []

    def detect_conflicts(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        """Identify and return pairs of tasks scheduled for the same time."""
        conflicts: list[tuple[Task, Task]] = []
        n = len(tasks)
        for i in range(n):
            for j in range(i + 1, n):
                if tasks[i].time == tasks[j].time:
                    conflicts.append((tasks[i], tasks[j]))
        return conflicts

    def handle_recurring(self, task: Task) -> Task | None:
        """Generate the next iteration for recurring daily or weekly tasks."""
        if task.frequency == "daily":
            next_date = task.due_date + timedelta(days=1)
        elif task.frequency == "weekly":
            next_date = task.due_date + timedelta(days=7)
        else:
            return None

        return Task(
            description=task.description,
            time=task.time,
            due_date=next_date,
            completed=False,
            frequency=task.frequency,
            priority=task.priority,
        )

    def find_next_available_slot(
        self, tasks: list[Task], duration_minutes: int = 30
    ) -> str:
        """
        Find the earliest free time slot of the given duration.

        Working hours are 06:00 - 22:00. Assumes each existing task
        occupies 30 minutes (Task has no duration field).

        Args:
            tasks: List of Task objects (uses their .time attribute).
            duration_minutes: Required block of free time in minutes.

        Returns:
            Start time as "HH:MM", or "None available today".
        """
        day_start = 6 * 60
        day_end = 22 * 60

        # Convert "HH:MM" strings to minutes-since-midnight
        task_times: list[int] = []
        for task in tasks:
            hrs, mins = map(int, task.time.split(":"))
            time_in_mins = hrs * 60 + mins
            if day_start <= time_in_mins < day_end:
                task_times.append(time_in_mins)

        task_times.sort()
        current_time = day_start

        for task_start in task_times:
            # If the gap before this task is big enough, use it
            if task_start - current_time >= duration_minutes:
                return f"{current_time // 60:02d}:{current_time % 60:02d}"

            # Advance past the current task (assumes 30-min tasks)
            if task_start >= current_time:
                current_time = task_start + 30

        # Check the final window before day_end
        if day_end - current_time >= duration_minutes:
            return f"{current_time // 60:02d}:{current_time % 60:02d}"

        return "None available today"

    def detect_overlaps(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        """
        Return pairs of tasks whose 30-minute time windows overlap.

        Assumes each task occupies 30 minutes (Task has no duration field).

        Args:
            tasks: List of Task objects with .time in "HH:MM" format.

        Returns:
            List of (task_a, task_b) tuples where task_b starts before
            task_a's window ends.
        """

        def to_minutes(time_str: str) -> int:
            hours, minutes = map(int, time_str.split(":"))
            return hours * 60 + minutes

        sorted_tasks = sorted(tasks, key=lambda t: to_minutes(t.time))
        overlaps: list[tuple[Task, Task]] = []

        for i, task_a in enumerate(sorted_tasks):
            start_a = to_minutes(task_a.time)
            end_a = start_a + 30

            for task_b in sorted_tasks[i + 1 :]:
                start_b = to_minutes(task_b.time)

                # Sorted list -> once we pass task_a's window, no more overlaps
                if start_b >= end_a:
                    break

                overlaps.append((task_a, task_b))

        return overlaps


# ----------------------------------------------------------------------
# JSON Persistence (Stretch Feature)
# ----------------------------------------------------------------------


def save_owner_to_json(owner: Owner, filepath: str) -> None:
    """Serialize an Owner (and all its pets and tasks) to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(owner.to_dict(), f, indent=4, ensure_ascii=False)


def load_owner_from_json(filepath: str) -> Owner:
    """Load an Owner from a JSON file, or return a fresh one if missing."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return Owner.from_dict(data)
    except FileNotFoundError:
        return Owner(name="New User")
