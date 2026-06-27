import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path

DB_DIR = Path("database")
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "interview_coach.db"


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT,
            resume_text TEXT,
            job_description TEXT,
            questions_json TEXT,
            answers_json TEXT,
            feedback_json TEXT,
            final_score REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def create_user(name: str, email: str, password: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users(name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name.strip(), email.strip().lower(), hash_password(password), datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
        return True, "Account created successfully. Please login."
    except sqlite3.IntegrityError:
        return False, "Email already exists. Please login or use another email."
    finally:
        conn.close()


def authenticate_user(email: str, password: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email FROM users WHERE email=? AND password_hash=?",
        (email.strip().lower(), hash_password(password)),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "email": row[2]}
    return None


def save_interview(user_id, role, resume_text, job_description, questions, answers, feedback, final_score):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO interviews(user_id, role, resume_text, job_description, questions_json,
        answers_json, feedback_json, final_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            role,
            resume_text,
            job_description,
            json.dumps(questions, ensure_ascii=False),
            json.dumps(answers, ensure_ascii=False),
            json.dumps(feedback, ensure_ascii=False),
            float(final_score or 0),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    interview_id = cur.lastrowid
    conn.close()
    return interview_id


def get_user_interviews(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, role, final_score, created_at, feedback_json FROM interviews WHERE user_id=? ORDER BY created_at DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_interview(interview_id, user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, role, questions_json, answers_json, feedback_json, final_score, created_at
        FROM interviews WHERE id=? AND user_id=?
        """,
        (interview_id, user_id),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0], "role": row[1], "questions": json.loads(row[2] or "[]"),
        "answers": json.loads(row[3] or "[]"), "feedback": json.loads(row[4] or "{}"),
        "final_score": row[5], "created_at": row[6]
    }
