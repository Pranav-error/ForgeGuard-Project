"""One-off CLI to create an admin user (self-registration only ever creates 'verifier').

    python3 -m api.create_admin admin@example.com somepassword
"""
import sys
from pathlib import Path

from . import auth, db

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = str(ROOT / "forgeguard.db")


def main():
    if len(sys.argv) != 3:
        print("usage: python3 -m api.create_admin <email> <password>")
        raise SystemExit(1)
    email, password = sys.argv[1], sys.argv[2]
    with db.session(DB_PATH) as conn:
        if db.get_user_by_email(conn, email):
            print("email already registered")
            raise SystemExit(1)
        user_id = db.add_user(conn, email, auth.hash_password(password), role="admin")
    print(f"created admin {email} ({user_id})")


if __name__ == "__main__":
    main()
