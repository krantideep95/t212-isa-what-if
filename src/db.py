import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "portfolio.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()


if __name__ == "__main__":
    with connect() as conn:
        init_schema(conn)
        print(f"DB initialized at {DB_PATH}")
