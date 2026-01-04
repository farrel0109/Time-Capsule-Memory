import os
import sqlite3
from flask import g
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.dirname(__file__)

# Support Render persistent disk via DATABASE_PATH env var
# Defaults to local database/ directory for development
DATABASE_DIR = os.environ.get('DATABASE_DIR', os.path.join(BASE_DIR, 'database'))
DATABASE = os.path.join(DATABASE_DIR, 'balita.db')

# Environment-driven DB selection. Set DB_TYPE=mysql to use MySQL.
DB_TYPE = os.environ.get('DB_TYPE', 'sqlite').lower()


class MySQLDBWrapper:
    """A thin wrapper to provide a sqlite-like `execute` interface over
    mysql-connector so the rest of the app can call `db.execute(...)`.
    """
    def __init__(self, conn):
        self.conn = conn

    def _query(self, query):
        # convert sqlite-style ? placeholders to MySQL %s
        return query.replace('?', '%s')

    def execute(self, query, params=()):
        cur = self.conn.cursor(dictionary=True)
        q = self._query(query)
        cur.execute(q, params)
        return cur

    def commit(self):
        return self.conn.commit()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


def get_db():
    """Return a DB connection/wrapper stored on flask.g."""
    db = getattr(g, '_database', None)
    if db is None:
        if DB_TYPE == 'mysql':
            # lazy import so mysql dependency is optional for sqlite users
            import mysql.connector
            host = os.environ.get('MYSQL_HOST', 'localhost')
            port = int(os.environ.get('MYSQL_PORT', '3306'))
            user = os.environ.get('MYSQL_USER', 'root')
            password = os.environ.get('MYSQL_PASSWORD', '')
            database = os.environ.get('MYSQL_DB', 'balita_db')
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            db = MySQLDBWrapper(conn)
        else:
            os.makedirs(DATABASE_DIR, exist_ok=True)
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            db = conn
        g._database = db
    return db


def close_connection(exception):
    """Close the DB connection at the end of each request."""
    db = getattr(g, '_database', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass


def init_db():
    """Create the database tables if they don't already exist."""
    db = get_db()

    # MySQL uses different AUTO_INCREMENT syntax
    if DB_TYPE == 'mysql':
        pk = 'INT AUTO_INCREMENT PRIMARY KEY'
    else:
        pk = 'INTEGER PRIMARY KEY AUTOINCREMENT'

    def exec_sql(sql):
        try:
            db.execute(sql)
        except Exception:
            pass

    # Users table
    exec_sql(f"""
        CREATE TABLE IF NOT EXISTS users (
            id {pk},
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            avatar_url TEXT,
            preferred_theme TEXT DEFAULT 'peach',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)

    # Children table
    exec_sql(f"""
        CREATE TABLE IF NOT EXISTS children (
            id {pk},
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            dob TEXT,
            gender TEXT,
            photo_url TEXT,
            blood_type TEXT,
            allergies TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Growth records
    exec_sql(f"""
        CREATE TABLE IF NOT EXISTS growth (
            id {pk},
            child_id INTEGER NOT NULL,
            record_date TEXT,
            weight REAL,
            height REAL,
            head_circ REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Development/Milestone records
    exec_sql(f"""
        CREATE TABLE IF NOT EXISTS development (
            id {pk},
            child_id INTEGER NOT NULL,
            category TEXT DEFAULT 'general',
            milestone TEXT,
            status TEXT DEFAULT 'pending',
            achieved_date TEXT,
            noted TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Immunization records
    exec_sql(f"""
        CREATE TABLE IF NOT EXISTS immunization (
            id {pk},
            child_id INTEGER NOT NULL,
            vaccine TEXT,
            scheduled_date TEXT,
            date_given TEXT,
            status TEXT DEFAULT 'pending',
            location TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Time Capsule table
    exec_sql(f"""
        CREATE TABLE IF NOT EXISTS time_capsules (
            id {pk},
            child_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            letter_content TEXT,
            unlock_date TEXT NOT NULL,
            unlock_occasion TEXT,
            is_sealed INTEGER DEFAULT 0,
            sealed_at TIMESTAMP,
            opened_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Capsule Media (photos, audio, video)
    exec_sql(f"""
        CREATE TABLE IF NOT EXISTS capsule_media (
            id {pk},
            capsule_id INTEGER NOT NULL,
            media_type TEXT NOT NULL,
            file_url TEXT NOT NULL,
            thumbnail_url TEXT,
            caption TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Family Access - Multi-parent sharing
    exec_sql(f"""
        CREATE TABLE IF NOT EXISTS family_access (
            id {pk},
            child_id INTEGER NOT NULL,
            user_id INTEGER,
            invite_code TEXT UNIQUE,
            invite_email TEXT,
            role TEXT DEFAULT 'viewer',
            status TEXT DEFAULT 'pending',
            invited_by INTEGER NOT NULL,
            accepted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Scheduled Letters - Time Capsule upgrade
    exec_sql(f"""
        CREATE TABLE IF NOT EXISTS scheduled_letters (
            id {pk},
            child_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            unlock_date TEXT NOT NULL,
            unlock_occasion TEXT,
            is_sent INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Health Insights Cache
    exec_sql(f"""
        CREATE TABLE IF NOT EXISTS health_insights (
            id {pk},
            child_id INTEGER NOT NULL,
            insight_type TEXT NOT NULL,
            insight_data TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    try:
        db.commit()
    except Exception:
        pass
