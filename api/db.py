"""Data layer -- Detailed Design Document Section 7, simplified.

# ponytail: SQLite, not Postgres -- the System Design Document calls for
# Postgres in production (concurrent writers, proper types); SQLite is the
# already-installed stdlib option that proves the schema and queries end to
# end on one machine. Swap the connection layer, keep the schema and the
# functions below unchanged.
"""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('verifier', 'admin')),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS signatures (
    id TEXT PRIMARY KEY,
    signer_id TEXT NOT NULL,
    embedding TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    doc_type TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    uploaded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS verifications (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id),
    signature_sub_score INTEGER,
    tamper_sub_score INTEGER,
    ocr_sub_score INTEGER,
    final_score INTEGER,
    label TEXT NOT NULL,
    reason_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    verification_id TEXT,
    detail_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(path: str = "forgeguard.db") -> sqlite3.Connection:
    # check_same_thread=False: FastAPI runs sync route dependencies in a worker
    # thread but the async route body on the event-loop thread; one connection
    # per request (never shared across concurrent requests) makes this safe.
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def session(path: str = "forgeguard.db"):
    conn = connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def add_user(conn: sqlite3.Connection, email: str, password_hash: str, role: str = "verifier") -> str:
    row_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users (id, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
        (row_id, email, password_hash, role, _now()),
    )
    return row_id


def get_user_by_email(conn: sqlite3.Connection, email: str):
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def add_session(conn: sqlite3.Connection, user_id: str, token: str) -> None:
    conn.execute("INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)", (token, user_id, _now()))


def list_audit_log(conn: sqlite3.Connection, limit: int = 100):
    rows = conn.execute("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def add_signature(conn: sqlite3.Connection, signer_id: str, embedding) -> str:
    row_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO signatures (id, signer_id, embedding, created_at) VALUES (?, ?, ?, ?)",
        (row_id, signer_id, json.dumps(embedding.tolist()), _now()),
    )
    return row_id


def get_references(conn: sqlite3.Connection, signer_id: str):
    import numpy as np

    rows = conn.execute("SELECT embedding FROM signatures WHERE signer_id = ?", (signer_id,)).fetchall()
    return [np.array(json.loads(r["embedding"]), dtype=np.float32) for r in rows]


def add_document(conn: sqlite3.Connection, doc_type: str, sha256_hash: str) -> str:
    row_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO documents (id, doc_type, sha256_hash, uploaded_at) VALUES (?, ?, ?, ?)",
        (row_id, doc_type, sha256_hash, _now()),
    )
    return row_id


def add_verification(conn: sqlite3.Connection, document_id: str, fused: dict) -> str:
    row_id = str(uuid.uuid4())
    subs = fused["sub_scores"]
    conn.execute(
        """INSERT INTO verifications
           (id, document_id, signature_sub_score, tamper_sub_score, ocr_sub_score,
            final_score, label, reason_text, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (row_id, document_id, subs.get("signature"), subs.get("tamper"), subs.get("ocr"),
         fused.get("score"), fused["label"], fused["reason"], _now()),
    )
    return row_id


def add_audit(conn: sqlite3.Connection, action: str, verification_id: str | None, detail: dict) -> None:
    conn.execute(
        "INSERT INTO audit_log (id, action, verification_id, detail_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), action, verification_id, json.dumps(detail), _now()),
    )


def get_verification(conn: sqlite3.Connection, document_id: str):
    row = conn.execute(
        "SELECT * FROM verifications WHERE document_id = ? ORDER BY created_at DESC LIMIT 1", (document_id,)
    ).fetchone()
    return dict(row) if row else None
