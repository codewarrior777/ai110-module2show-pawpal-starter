"""FastAPI REST API for PawPal+.

Exposes the Scheduler class as REST endpoints with auto-generated
Swagger documentation at /docs.

Run with:
    uvicorn api:app --reload
Or:
    python api.py
"""

from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from pawpal_system import (
    Owner,
    Pet,
    Scheduler,
    Task,
    load_owner_from_json,
    save_owner_to_json,
)

# ----------------------------------------------------------------------
# Global in-memory state (per-process; for demo purposes)
# ----------------------------------------------------------------------
_state: dict = {"owner": Owner(name="New User"), "scheduler": Scheduler()}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load existing data on startup; save on shutdown."""
    _state["owner"] = load_owner_from_json("data.json")
    yield
    save_owner_to_json(_state["owner"], "data.json")


# ----------------------------------------------------------------------
# FastAPI app
# ----------------------------------------------------------------------
app = FastAPI(
    title="PawPal+ API",
    description=(
        "REST API for the PawPal+ smart pet care management system. "
        "Manage pets, tasks, and schedules programmatically."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ----------------------------------------------------------------------
# Pydantic schemas
# ----------------------------------------------------------------------
class TaskCreate(BaseModel):
    """Payload to create a new task."""

    description: str = Field(..., min_length=1, examples=["Morning walk"])
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$", examples=["07:00"])
    frequency: str = Field("once", pattern=r"^(once|daily|weekly)$")
    priority: str = Field("medium", pattern=r"^(high|medium|low)$")


class PetCreate(BaseModel):
    """Payload to create a new pet."""

    name: str = Field(..., min_length=1, examples=["Cooper"])
    species: str = Field(..., min_length=1, examples=["Dog"])
    age: int = Field(..., ge=0, le=100, examples=[4])


class OwnerCreate(BaseModel):
    """Payload to set the owner's name."""

    name: str = Field(..., min_length=1, examples=["Gustavo"])


class ParseTaskRequest(BaseModel):
    """Payload to parse natural language into a task."""

    text: str = Field(
        ...,
        min_length=1,
        examples=["walk Cooper at 7am daily, high priority"],
    )


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _task_to_dict(task: Task) -> dict:
    """Serialize a Task to a JSON-compatible dict."""
    return {
        "description": task.description,
        "time": task.time,
        "due_date": task.due_date.isoformat(),
        "completed": task.completed,
        "frequency": task.frequency,
        "priority": task.priority,
    }


# ----------------------------------------------------------------------
# Health
# ----------------------------------------------------------------------
@app.get("/", tags=["Health"])
def root():
    """Health check + link to interactive docs."""
    return {
        "app": "PawPal+ API",
        "status": "ok",
        "version": "1.0.0",
        "docs": "/docs",
    }


# ----------------------------------------------------------------------
# Owner
# ----------------------------------------------------------------------
@app.get("/api/owner", tags=["Owner"])
def get_owner():
    """Return the current owner info."""
    owner = _state["owner"]
    return {"name": owner.name, "pet_count": len(owner.pets)}


@app.post("/api/owner", tags=["Owner"])
def set_owner(payload: OwnerCreate):
    """Set or change the owner's name."""
    _state["owner"].name = payload.name
    return {"name": payload.name, "status": "updated"}


# ----------------------------------------------------------------------
# Pets
# ----------------------------------------------------------------------
@app.get("/api/pets", tags=["Pets"])
def list_pets():
    """List all registered pets."""
    owner = _state["owner"]
    return [
        {
            "name": p.name,
            "species": p.species,
            "age": p.age,
            "task_count": len(p.tasks),
        }
        for p in owner.pets
    ]


@app.post("/api/pets", status_code=201, tags=["Pets"])
def create_pet(payload: PetCreate):
    """Add a new pet."""
    owner = _state["owner"]
    if any(p.name == payload.name for p in owner.pets):
        raise HTTPException(400, f"Pet '{payload.name}' already exists")
    pet = Pet(name=payload.name, species=payload.species, age=payload.age)
    owner.add_pet(pet)
    return {"status": "created", "pet": payload.name}


# ----------------------------------------------------------------------
# Tasks
# ----------------------------------------------------------------------
@app.get("/api/tasks", tags=["Tasks"])
def list_tasks(completed: bool | None = None):
    """List all tasks, optionally filtered by completion status."""
    owner = _state["owner"]
    scheduler = _state["scheduler"]
    tasks = owner.get_all_tasks()
    if completed is not None:
        tasks = scheduler.filter_by_completion(tasks, completed=completed)
    return [_task_to_dict(t) for t in tasks]


@app.get("/api/pets/{pet_name}/tasks", tags=["Tasks"])
def get_pet_tasks(pet_name: str):
    """List all tasks for a specific pet."""
    owner = _state["owner"]
    scheduler = _state["scheduler"]
    if not any(p.name == pet_name for p in owner.pets):
        raise HTTPException(404, f"Pet '{pet_name}' not found")
    tasks = scheduler.filter_by_pet_name(owner, pet_name)
    return [_task_to_dict(t) for t in tasks]


@app.post("/api/pets/{pet_name}/tasks", status_code=201, tags=["Tasks"])
def create_task(pet_name: str, payload: TaskCreate):
    """Add a task to a specific pet."""
    owner = _state["owner"]
    pet = next((p for p in owner.pets if p.name == pet_name), None)
    if not pet:
        raise HTTPException(404, f"Pet '{pet_name}' not found")

    task = Task(
        description=payload.description,
        time=payload.time,
        due_date=date.today(),
        frequency=payload.frequency,
        priority=payload.priority,
    )
    pet.add_task(task)
    return {
        "status": "created",
        "pet": pet_name,
        "task": _task_to_dict(task),
    }


# ----------------------------------------------------------------------
# Schedule
# ----------------------------------------------------------------------
@app.get("/api/schedule", tags=["Schedule"])
def get_schedule(sort: str = "time"):
    """Return the full schedule, sorted by 'time' or 'priority'."""
    owner = _state["owner"]
    scheduler = _state["scheduler"]
    tasks = owner.get_all_tasks()

    if sort == "priority":
        sorted_tasks = scheduler.sort_by_priority(tasks)
    elif sort == "time":
        sorted_tasks = scheduler.sort_by_time(tasks)
    else:
        raise HTTPException(400, "sort must be 'time' or 'priority'")

    return [_task_to_dict(t) for t in sorted_tasks]


@app.get("/api/conflicts", tags=["Schedule"])
def get_conflicts():
    """Detect scheduling conflicts (tasks with identical start times)."""
    owner = _state["owner"]
    scheduler = _state["scheduler"]
    conflicts = scheduler.detect_conflicts(owner.get_all_tasks())
    return [
        {"time": t1.time, "task_a": t1.description, "task_b": t2.description}
        for t1, t2 in conflicts
    ]


@app.get("/api/overlaps", tags=["Schedule"])
def get_overlaps():
    """Detect overlapping 30-minute task windows."""
    owner = _state["owner"]
    scheduler = _state["scheduler"]
    overlaps = scheduler.detect_overlaps(owner.get_all_tasks())
    return [
        {
            "task_a": t1.description,
            "time_a": t1.time,
            "task_b": t2.description,
            "time_b": t2.time,
        }
        for t1, t2 in overlaps
    ]


@app.get("/api/next-slot", tags=["Schedule"])
def get_next_slot(duration: int = 30):
    """Find the earliest free slot of the given duration (minutes)."""
    owner = _state["owner"]
    scheduler = _state["scheduler"]
    slot = scheduler.find_next_available_slot(
        owner.get_all_tasks(), duration_minutes=duration
    )
    return {"duration_minutes": duration, "next_available_slot": slot}


# ----------------------------------------------------------------------
# Natural Language Parsing (AI)
# ----------------------------------------------------------------------
@app.post("/api/parse-task", tags=["AI"])
def parse_task_endpoint(payload: ParseTaskRequest):
    """
    Convert natural language into a structured task.

    Example:
        Input: "walk Cooper at 7am daily, high priority"
        Output: {description: "Walk Cooper", time: "07:00",
                 frequency: "daily", priority: "high", pet_name: "Cooper"}
    """
    from nl_parser import parse_task as _parse

    owner = _state["owner"]
    known_pets = [p.name for p in owner.pets]

    try:
        parsed = _parse(payload.text, known_pets)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return parsed.to_dict()


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------
@app.post("/api/save", tags=["Persistence"])
def save_data():
    """Persist the current state to data.json."""
    save_owner_to_json(_state["owner"], "data.json")
    return {"status": "saved", "file": "data.json"}


@app.post("/api/load", tags=["Persistence"])
def load_data():
    """Load state from data.json."""
    _state["owner"] = load_owner_from_json("data.json")
    return {
        "status": "loaded",
        "owner": _state["owner"].name,
        "pet_count": len(_state["owner"].pets),
    }


# ----------------------------------------------------------------------
# Entry point for `python api.py`
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
