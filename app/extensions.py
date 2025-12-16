# Flask Extensions
# Centralized place for Flask extensions initialization

from flask import g
import os
import sqlite3


class MySQLDBWrapper:
    """A thin wrapper to provide sqlite-like interface over mysql-connector."""
    
    def __init__(self, conn):
        self.conn = conn

    def _query(self, query):
        # Convert sqlite-style ? placeholders to MySQL %s
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
    from flask import current_app
    
    db = getattr(g, '_database', None)
    if db is None:
        config = current_app.config
        
        if config.get('DB_TYPE') == 'mysql':
            import mysql.connector
            
            conn = mysql.connector.connect(
                host=config.get('MYSQL_HOST'),
                port=config.get('MYSQL_PORT'),
                user=config.get('MYSQL_USER'),
                password=config.get('MYSQL_PASS'),
                database=config.get('MYSQL_DB')
            )
            db = MySQLDBWrapper(conn)
        else:
            db_path = config.get('DATABASE_PATH')
            db_dir = os.path.dirname(db_path)
            os.makedirs(db_dir, exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            db = conn
        
        g._database = db
    return db


def close_db(exception=None):
    """Close database connection at end of request."""
    db = getattr(g, '_database', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass


def init_db():
    """Create tables if they don't exist."""
    from flask import current_app
    
    db = get_db()
    config = current_app.config
    db_type = config.get('DB_TYPE', 'sqlite')

    def exec_sql(sql):
        if db_type == 'mysql':
            cur = db.execute(sql)
            try:
                cur.close()
            except Exception:
                pass
        else:
            cur = db.cursor()
            cur.execute(sql)
            cur.close()

    # Primary key clause per DB type
    pk = 'INT PRIMARY KEY AUTO_INCREMENT' if db_type == 'mysql' else 'INTEGER PRIMARY KEY AUTOINCREMENT'

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
            dob TEXT NOT NULL,
            gender TEXT,
            photo_url TEXT,
            blood_type TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Growth records
    exec_sql(f"""
        CREATE TABLE IF NOT EXISTS growth (
            id {pk},
            child_id INTEGER NOT NULL,
            record_date TEXT NOT NULL,
            weight REAL,
            height REAL,
            head_circ REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Development milestones
    exec_sql(f"""
        CREATE TABLE IF NOT EXISTS development (
            id {pk},
            child_id INTEGER NOT NULL,
            category TEXT DEFAULT 'general',
            milestone TEXT NOT NULL,
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
            vaccine TEXT NOT NULL,
            scheduled_date TEXT,
            date_given TEXT,
            status TEXT DEFAULT 'pending',
            batch_number TEXT,
            location TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Time Capsules (NEW)
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Capsule Media (NEW)
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

    # General Media (for gallery)
    exec_sql(f"""
        CREATE TABLE IF NOT EXISTS media (
            id {pk},
            child_id INTEGER NOT NULL,
            media_type TEXT NOT NULL,
            file_url TEXT NOT NULL,
            thumbnail_url TEXT,
            caption TEXT,
            taken_date TEXT,
            is_favorite INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    try:
        db.commit()
    except Exception:
        pass
