import os
import time
from datetime import date, timedelta

import mysql.connector
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Habit Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "user": os.getenv("DB_USER", "habit_user"),
    "password": os.getenv("DB_PASSWORD", "habit_pass"),
    "database": os.getenv("DB_NAME", "habit_tracker"),
}


def get_connection():
    last_error = None
    for _ in range(10):
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except mysql.connector.Error as e:
            last_error = e
            time.sleep(2)
    raise last_error


class HabitCreate(BaseModel):
    name: str
    icon: str = "🔥"


def calculate_streak(cursor, habit_id: int) -> int:
    cursor.execute(
        "SELECT log_date FROM habit_logs WHERE habit_id = %s ORDER BY log_date DESC",
        (habit_id,),
    )
    rows = [r[0] for r in cursor.fetchall()]
    if not rows:
        return 0

    today = date.today()
    streak = 0
    expected_day = today

    if rows[0] != today:
        expected_day = today - timedelta(days=1)

    logged_days = set(rows)
    while expected_day in logged_days:
        streak += 1
        expected_day -= timedelta(days=1)

    return streak


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/habits")
def list_habits():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, icon FROM habits ORDER BY id")
    habits = cursor.fetchall()

    result = []
    for habit_id, name, icon in habits:
        streak = calculate_streak(cursor, habit_id)
        cursor.execute(
            "SELECT 1 FROM habit_logs WHERE habit_id = %s AND log_date = %s",
            (habit_id, date.today()),
        )
        done_today = cursor.fetchone() is not None
        result.append(
            {
                "id": habit_id,
                "name": name,
                "icon": icon,
                "streak": streak,
                "done_today": done_today,
            }
        )

    cursor.close()
    conn.close()
    return result


@app.post("/api/habits")
def create_habit(habit: HabitCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO habits (name, icon) VALUES (%s, %s)", (habit.name, habit.icon)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return {"id": new_id, "name": habit.name, "icon": habit.icon, "streak": 0, "done_today": False}


@app.post("/api/habits/{habit_id}/check")
def check_habit(habit_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM habits WHERE id = %s", (habit_id,))
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Habit not found")

    try:
        cursor.execute(
            "INSERT INTO habit_logs (habit_id, log_date) VALUES (%s, %s)",
            (habit_id, date.today()),
        )
        conn.commit()
    except mysql.connector.errors.IntegrityError:
        pass

    streak = calculate_streak(cursor, habit_id)
    cursor.close()
    conn.close()
    return {"habit_id": habit_id, "streak": streak, "done_today": True}


@app.delete("/api/habits/{habit_id}")
def delete_habit(habit_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habits WHERE id = %s", (habit_id,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    if affected == 0:
        raise HTTPException(status_code=404, detail="Habit not found")
    return {"deleted": habit_id}