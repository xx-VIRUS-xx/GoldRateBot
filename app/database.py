import sqlite3
from datetime import datetime
from threading import Lock
from contextlib import contextmanager

DB_PATH = 'db.sqlite3'
_lock = Lock()
_connection = None

def get_db_connection():
    """Get a reusable database connection with proper timeout settings."""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(DB_PATH, timeout=5.0, check_same_thread=False)
        _connection.isolation_level = None  # Autocommit mode
    return _connection

@contextmanager
def get_cursor():
    """Context manager for database cursor operations."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()

def init_db():
    """Initialize database schema."""
    with _lock:
        with get_cursor() as cur:
            cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        phone TEXT PRIMARY KEY,
                        last_seen TEXT
                        )''')

def save_user_activity(phone: str):
    """Save user activity with proper connection management."""
    with _lock:
        with get_cursor() as cur:
            cur.execute('''INSERT OR REPLACE INTO users (phone, last_seen)
                        VALUES (?, ?)''', (phone, datetime.utcnow().isoformat()))

# Initialize database on import
init_db()