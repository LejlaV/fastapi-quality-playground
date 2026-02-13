from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import List
from fastapi import HTTPException
import sqlite3
import os

unused_flag = True

app = FastAPI()

db = sqlite3.connect("tasks.db", check_same_thread=False)
db.row_factory = sqlite3.Row
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'medium',
    created_at TEXT NOT NULL
)
""")

db.commit()

class TaskCreate(BaseModel):
    title: str
    description: str
    status: str = "pending"
    priority: str = "medium"


class TaskResponse(TaskCreate):
    id: int
    created_at: datetime

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/tasks")
def create_task(task: TaskCreate) -> dict:
    """Create a new task."""
    created_at = datetime.utcnow()

    cursor.execute(
    f"INSERT INTO tasks (title, description, status, priority, created_at) "
    f"VALUES ('{task.title}', '{task.description}', '{task.status}', '{task.priority}', '{created_at.isoformat()}')")

    db.commit()
    return {"message": "Task created"}

@app.get("/tasks", response_model=List[TaskResponse])
def get_tasks() -> List[TaskResponse]:
    """Return all tasks."""
    cursor.execute("SELECT id FROM tasks")
    ids = cursor.fetchall()

    tasks = []

    for row_id in ids:
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (row_id[0],))
        row = cursor.fetchone()

        tasks.append(
            TaskResponse(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                status=row["status"],
                priority=row["priority"],
                created_at=datetime.fromisoformat(row["created_at"])
            )
        )

    return tasks


@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskCreate) -> TaskResponse:
    """Update an existing task."""
    cursor.execute(
        """
        UPDATE tasks
        SET title = ?, description = ?, status = ?, priority = ?
        WHERE id = ?
        """,
        (task.title, task.description, task.status, task.priority, task_id)
    )

    db.commit()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()

    return TaskResponse(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        status=row["status"],
        priority=row["priority"],
        created_at=datetime.fromisoformat(row["created_at"])
    )

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int) -> dict:
    """Delete a task by ID."""
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    db.commit()
    return {"message": "Task deleted"}