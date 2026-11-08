"""Auth and RBAC -- NFR-9 (Detailed Design Document Section 9).

# ponytail: sha256 password hashing with no salt/pepper rotation, opaque
# bearer tokens with no expiry. Fine to prove role separation end to end;
# swap for passlib/bcrypt + expiring JWTs before this is internet-facing.
"""
import hashlib
import secrets
import sqlite3

from fastapi import Header, HTTPException


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return secrets.compare_digest(hash_password(password), password_hash)


def new_token() -> str:
    return secrets.token_hex(24)


def get_current_user(conn: sqlite3.Connection, authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    token = authorization.removeprefix("Bearer ")
    row = conn.execute(
        """SELECT u.id, u.email, u.role FROM sessions s
           JOIN users u ON u.id = s.user_id WHERE s.token = ?""",
        (token,),
    ).fetchone()
    if row is None:
        raise HTTPException(401, "invalid or expired token")
    return dict(row)


def require_admin(user: dict) -> None:
    if user["role"] != "admin":
        raise HTTPException(403, "admin role required")
