import os
import sqlite3
from flask import g
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.dirname(__file__)
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
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
    db = getattr(g, '_database', None)
    if db is None:
        if DB_TYPE == 'mysql':
            # lazy import to avoid requiring mysql lib when not used
            import mysql.connector

            host = os.environ.get('MYSQL_HOST', 'localhost')
            port = int(os.environ.get('MYSQL_PORT', '3306'))
            user = os.environ.get('MYSQL_USER', 'root')
            password = os.environ.get('MYSQL_PASS', '')
            database = os.environ.get('MYSQL_DB', 'balita_db')
            conn = mysql.connector.connect(
                host=host, port=port, user=user, password=password, database=database
            )
            db = MySQLDBWrapper(conn)
        else:
            os.makedirs(DATABASE_DIR, exist_ok=True)
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            db = conn

        g._database = db
    return db


def init_db():
    db = get_db()

    # Use the wrapper/cursor semantics depending on DB type
    def exec_sql(sql):
        if DB_TYPE == 'mysql':
            cur = db.execute(sql)
            try:
                cur.close()
            except Exception:
                pass
        else:
            cur = db.cursor()
            cur.execute(sql)
            cur.close()

    # Create tables (SQL works for both SQLite and MySQL)
    exec_sql('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    exec_sql('''
        CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            user_id INTEGER,
            name TEXT,
            dob TEXT,
            gender TEXT
        )
    ''')
    exec_sql('''
        CREATE TABLE IF NOT EXISTS growth (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            child_id INTEGER,
            record_date TEXT,
            weight REAL,
            height REAL,
            head_circ REAL
        )
    ''')
    exec_sql('''
        CREATE TABLE IF NOT EXISTS development (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            child_id INTEGER,
            milestone TEXT,
            status TEXT,
            noted TEXT
        )
    ''')
    exec_sql('''
        CREATE TABLE IF NOT EXISTS immunization (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            child_id INTEGER,
            vaccine TEXT,
            date_given TEXT,
            status TEXT
        )
    ''')

    # Commit when using sqlite connection or wrapper
    try:
        if DB_TYPE == 'mysql':
            db.commit()
        else:
            db.commit()
    except Exception:
        pass


def close_connection(exception=None):
    db = getattr(g, '_database', None)
    if db is not None:
        try:
            if DB_TYPE == 'mysql':
                db.close()
            else:
                db.close()
        except Exception:
            pass
