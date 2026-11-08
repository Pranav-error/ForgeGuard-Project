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
    uploaded_by TEXT NOT NULL REFERENCES users(id),
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
    anomaly_sub_score INTEGER,
    final_score INTEGER,
    label TEXT NOT NULL,
    reason_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ledger_blocks (
    block_index INTEGER PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id),
    verification_id TEXT NOT NULL REFERENCES verifications(id),
    document_hash TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    block_hash TEXT NOT NULL,
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


def add_document(conn: sqlite3.Connection, uploaded_by: str, doc_type: str, sha256_hash: str) -> str:
    row_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO documents (id, uploaded_by, doc_type, sha256_hash, uploaded_at) VALUES (?, ?, ?, ?, ?)",
        (row_id, uploaded_by, doc_type, sha256_hash, _now()),
    )
    return row_id


def list_verifications_for_user(conn: sqlite3.Connection, user_id: str, limit: int = 50):
    rows = conn.execute(
        """SELECT v.*, d.doc_type, d.uploaded_at FROM verifications v
           JOIN documents d ON d.id = v.document_id
           WHERE d.uploaded_by = ? ORDER BY v.created_at DESC LIMIT ?""",
        (user_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def add_verification(conn: sqlite3.Connection, document_id: str, fused: dict) -> str:
    row_id = str(uuid.uuid4())
    subs = fused["sub_scores"]
    conn.execute(
        """INSERT INTO verifications
           (id, document_id, signature_sub_score, tamper_sub_score, ocr_sub_score,
            anomaly_sub_score, final_score, label, reason_text, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (row_id, document_id, subs.get("signature"), subs.get("tamper"), subs.get("ocr"),
         subs.get("anomaly"), fused.get("score"), fused["label"], fused["reason"], _now()),
    )
    return row_id


def add_audit(conn: sqlite3.Connection, action: str, verification_id: str | None, detail: dict) -> None:
    conn.execute(
        "INSERT INTO audit_log (id, action, verification_id, detail_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), action, verification_id, json.dumps(detail), _now()),
    )


def add_block(conn: sqlite3.Connection, document_id: str, verification_id: str, document_hash: str) -> dict:
    """Append the next block to the hash chain (Phase 2 -- Gap 9 / O9)."""
    from ledger import make_block, GENESIS_HASH

    last = conn.execute("SELECT * FROM ledger_blocks ORDER BY block_index DESC LIMIT 1").fetchone()
    index = (last["block_index"] + 1) if last else 0
    prev_hash = last["block_hash"] if last else GENESIS_HASH
    block = make_block(index, document_id, verification_id, document_hash, prev_hash, _now())
    conn.execute(
        """INSERT INTO ledger_blocks
           (block_index, document_id, verification_id, document_hash, prev_hash, block_hash, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (block.index, block.document_id, block.verification_id, block.document_hash,
         block.prev_hash, block.block_hash, block.created_at),
    )
    return block.__dict__


def get_block_for_document(conn: sqlite3.Connection, document_id: str):
    row = conn.execute(
        "SELECT * FROM ledger_blocks WHERE document_id = ? ORDER BY block_index DESC LIMIT 1", (document_id,)
    ).fetchone()
    return dict(row) if row else None


def verify_chain(conn: sqlite3.Connection) -> dict:
    """Re-derive every block's hash and check the linkage (Phase 2 integrity check)."""
    from ledger import Block, verify_links

    rows = conn.execute("SELECT * FROM ledger_blocks ORDER BY block_index ASC").fetchall()
    blocks = [
        Block(r["block_index"], r["document_id"], r["verification_id"], r["document_hash"],
              r["prev_hash"], r["created_at"], r["block_hash"])
        for r in rows
    ]
    valid, broken_at = verify_links(blocks)
    return {"valid": valid, "length": len(blocks), "broken_at": broken_at}


def get_verification(conn: sqlite3.Connection, document_id: str):
    row = conn.execute(
        "SELECT * FROM verifications WHERE document_id = ? ORDER BY created_at DESC LIMIT 1", (document_id,)
    ).fetchone()
    return dict(row) if row else None
