"""Persistência SQLite local (stdlib). Todos os dados pessoais ficam neste arquivo."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from app.models.schemas import Analysis, Application, ApplicationSummary, Profile, ResumeContent
from app.seed import initial_profile
from app.telemetry import tracer

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "jobagent.db"


def db_path() -> Path:
    return Path(os.environ.get("JOBAGENT_DB", str(DEFAULT_DB)))


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT '',
                job_description TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                score INTEGER NOT NULL,
                analysis TEXT NOT NULL,
                resume_generated TEXT NOT NULL,
                resume TEXT NOT NULL
            );
            """
        )
        if c.execute("SELECT 1 FROM profile WHERE id = 1").fetchone() is None:
            c.execute(
                "INSERT INTO profile (id, data, updated_at) VALUES (1, ?, ?)",
                (initial_profile().model_dump_json(), _now()),
            )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- Perfil
def get_profile() -> Profile:
    with connect() as c:
        row = c.execute("SELECT data FROM profile WHERE id = 1").fetchone()
    return Profile.model_validate_json(row["data"]) if row else initial_profile()


def save_profile(profile: Profile) -> Profile:
    with connect() as c:
        c.execute(
            "INSERT INTO profile (id, data, updated_at) VALUES (1, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at",
            (profile.model_dump_json(), _now()),
        )
    return profile


def reset_profile() -> Profile:
    return save_profile(initial_profile())


# ---------------------------------------------------------------- Candidaturas
def _row_to_application(row: sqlite3.Row) -> Application:
    return Application(
        id=row["id"],
        company=row["company"],
        role=row["role"],
        job_description=row["job_description"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        score=row["score"],
        analysis=Analysis.model_validate_json(row["analysis"]),
        resume_generated=ResumeContent.model_validate_json(row["resume_generated"]),
        resume=ResumeContent.model_validate_json(row["resume"]),
    )


def create_application(
    company: str, role: str, job_description: str, analysis: Analysis, resume: ResumeContent
) -> Application:
    now = _now()
    with tracer.start_as_current_span("db.create_application"), connect() as c:
        cur = c.execute(
            "INSERT INTO applications (company, role, job_description, created_at, updated_at, score, "
            "analysis, resume_generated, resume) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                company, role, job_description, now, now, analysis.score,
                analysis.model_dump_json(), resume.model_dump_json(), resume.model_dump_json(),
            ),
        )
        new_id = cur.lastrowid
    app = get_application(new_id)
    assert app is not None
    return app


def get_application(app_id: int) -> Optional[Application]:
    with connect() as c:
        row = c.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    return _row_to_application(row) if row else None


def list_applications() -> list[ApplicationSummary]:
    with connect() as c:
        rows = c.execute(
            "SELECT id, company, role, created_at, score, analysis FROM applications ORDER BY id DESC"
        ).fetchall()
    out = []
    for r in rows:
        mode = json.loads(r["analysis"]).get("mode", "rules")
        out.append(
            ApplicationSummary(
                id=r["id"], company=r["company"], role=r["role"], created_at=r["created_at"],
                score=r["score"], mode=mode,
            )
        )
    return out


def update_application(
    app_id: int, company: Optional[str], role: Optional[str], resume: Optional[ResumeContent]
) -> Optional[Application]:
    current = get_application(app_id)
    if current is None:
        return None
    with connect() as c:
        c.execute(
            "UPDATE applications SET company = ?, role = ?, resume = ?, updated_at = ? WHERE id = ?",
            (
                current.company if company is None else company,
                current.role if role is None else role,
                (resume or current.resume).model_dump_json(),
                _now(),
                app_id,
            ),
        )
    return get_application(app_id)


def reset_application_resume(app_id: int) -> Optional[Application]:
    current = get_application(app_id)
    if current is None:
        return None
    return update_application(app_id, None, None, current.resume_generated)


def delete_application(app_id: int) -> bool:
    with connect() as c:
        cur = c.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    return cur.rowcount > 0
