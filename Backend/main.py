from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uuid
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tasks = []

class TaskCreate(BaseModel):
    name: str
    priority: Optional[str] = "medium"   # low | medium | high | critical
    due_date: Optional[str] = None
    category: Optional[str] = "general"

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    category: Optional[str] = None

@app.get("/")
def root():
    return {"message": "Task Manager API v2.0"}

@app.get("/tasks")
def get_tasks(filter: Optional[str] = None, category: Optional[str] = None):
    result = tasks
    if filter == "active":
        result = [t for t in tasks if not t["completed"]]
    elif filter == "completed":
        result = [t for t in tasks if t["completed"]]
    if category and category != "all":
        result = [t for t in result if t["category"] == category]
    return {"tasks": result, "total": len(tasks), "completed": sum(1 for t in tasks if t["completed"])}

@app.post("/tasks")
def create_task(task: TaskCreate):
    new_task = {
        "id": str(uuid.uuid4()),
        "name": task.name,
        "priority": task.priority,
        "due_date": task.due_date,
        "category": task.category,
        "completed": False,
        "created_at": datetime.now().isoformat(),
    }
    tasks.append(new_task)
    return {"message": "Task created", "task": new_task}

@app.patch("/tasks/{task_id}")
def update_task(task_id: str, update: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            if update.name is not None:
                task["name"] = update.name
            if update.completed is not None:
                task["completed"] = update.completed
            if update.priority is not None:
                task["priority"] = update.priority
            if update.due_date is not None:
                task["due_date"] = update.due_date
            if update.category is not None:
                task["category"] = update.category
            return {"message": "Task updated", "task": task}
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            deleted = tasks.pop(i)
            return {"message": "Task deleted", "task": deleted}
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks")
def clear_completed():
    global tasks
    removed = [t for t in tasks if t["completed"]]
    tasks = [t for t in tasks if not t["completed"]]
    return {"message": f"Cleared {len(removed)} completed tasks"}

@app.get("/stats")
def get_stats():
    total = len(tasks)
    completed = sum(1 for t in tasks if t["completed"])
    by_priority = {p: sum(1 for t in tasks if t["priority"] == p) for p in ["low", "medium", "high", "critical"]}
    by_category = {}
    for t in tasks:
        by_category[t["category"]] = by_category.get(t["category"], 0) + 1
    return {
        "total": total,
        "completed": completed,
        "active": total - completed,
        "completion_rate": round((completed / total * 100) if total else 0, 1),
        "by_priority": by_priority,
        "by_category": by_category,
    }
