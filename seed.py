"""
Seed script untuk menambahkan data dummy ke database BabyGrow.
Membuat 1 user dengan 3 anak beserta data kesehatan lengkap.
"""
import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
import random

# Path database - sama dengan db.py
DATABASE_DIR = os.path.join(os.path.dirname(__file__), 'database')
DATABASE = os.path.join(DATABASE_DIR, 'balita.db')

def init_tables(cur):
    """Create tables if not exist."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            dob TEXT,
            gender TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS growth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            record_date TEXT,
            weight REAL,
            height REAL,
            head_circ REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS development (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            milestone TEXT,
            status TEXT DEFAULT 'pending',
            noted TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS immunization (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            vaccine TEXT,
            date_given TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)

def seed_database():
    """Insert dummy data into database."""
    os.makedirs(DATABASE_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Create tables first
    init_tables(cur)
    conn.commit()
    
    print("🌱 Seeding database...")
    
    # ======== 1. Create Parent User ========
    username = "ibu_sarah"
    password = hashlib.sha256("password123".encode()).hexdigest()
    
    # Check if user exists
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    
    if not user:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        user_id = cur.lastrowid
        print(f"✅ Created user: {username} (password: password123)")
    else:
        user_id = user['id']
        print(f"ℹ️ User already exists: {username}")
    
    # ======== 2. Create 3 Children ========
    children_data = [
        {
            "name": "Aisha Putri",
            "dob": "2023-03-15",
            "gender": "Perempuan"
        },
        {
            "name": "Ahmad Khalil",
            "dob": "2021-08-22",
            "gender": "Laki-laki"
        },
        {
            "name": "Zara Amelia",
            "dob": "2024-01-10",
            "gender": "Perempuan"
        }
    ]
    
    child_ids = []
    for child in children_data:
        # Check if child exists
        cur.execute("SELECT id FROM children WHERE name = ? AND user_id = ?", (child['name'], user_id))
        existing = cur.fetchone()
        
        if not existing:
            cur.execute(
                "INSERT INTO children (user_id, name, dob, gender) VALUES (?, ?, ?, ?)",
                (user_id, child['name'], child['dob'], child['gender'])
            )
            child_id = cur.lastrowid
            child_ids.append(child_id)
            print(f"✅ Created child: {child['name']} ({child['gender']}, DOB: {child['dob']})")
        else:
            child_ids.append(existing['id'])
            print(f"ℹ️ Child already exists: {child['name']}")
    
    # ======== 3. Add Growth Data ========
    growth_templates = [
        # Aisha (1.5 tahun) - 6 records
        [
            {"months": 0, "weight": 3.2, "height": 50, "head": 35},
            {"months": 3, "weight": 5.5, "height": 60, "head": 40},
            {"months": 6, "weight": 7.0, "height": 66, "head": 43},
            {"months": 9, "weight": 8.2, "height": 71, "head": 45},
            {"months": 12, "weight": 9.0, "height": 75, "head": 46},
            {"months": 18, "weight": 10.5, "height": 82, "head": 47},
        ],
        # Ahmad (3+ tahun) - 8 records
        [
            {"months": 0, "weight": 3.5, "height": 52, "head": 36},
            {"months": 3, "weight": 6.0, "height": 62, "head": 41},
            {"months": 6, "weight": 7.8, "height": 68, "head": 44},
            {"months": 12, "weight": 9.5, "height": 76, "head": 46},
            {"months": 18, "weight": 11.0, "height": 83, "head": 47},
            {"months": 24, "weight": 12.5, "height": 88, "head": 48},
            {"months": 30, "weight": 13.8, "height": 93, "head": 49},
            {"months": 36, "weight": 15.0, "height": 98, "head": 50},
        ],
        # Zara (11 bulan) - 4 records
        [
            {"months": 0, "weight": 3.0, "height": 49, "head": 34},
            {"months": 3, "weight": 5.2, "height": 58, "head": 39},
            {"months": 6, "weight": 6.8, "height": 65, "head": 42},
            {"months": 9, "weight": 8.0, "height": 70, "head": 44},
        ],
    ]
    
    for i, child_id in enumerate(child_ids):
        dob = datetime.strptime(children_data[i]['dob'], "%Y-%m-%d")
        for growth in growth_templates[i]:
            record_date = dob + timedelta(days=growth['months'] * 30)
            cur.execute(
                "INSERT INTO growth (child_id, record_date, weight, height, head_circ) VALUES (?, ?, ?, ?, ?)",
                (child_id, record_date.strftime("%Y-%m-%d"), growth['weight'], growth['height'], growth['head'])
            )
    print(f"✅ Added growth records for all children")
    
    # ======== 4. Add Milestone Data ========
    milestones_by_age = {
        # Aisha - toddler milestones
        0: [
            ("Bisa tengkurap", "done"),
            ("Bisa duduk sendiri", "done"),
            ("Bisa merangkak", "done"),
            ("Bisa berdiri berpegangan", "done"),
            ("Bisa berjalan", "done"),
            ("Mengucapkan 'mama'", "done"),
            ("Minum dari gelas", "done"),
            ("Berlari", "pending"),
            ("Naik tangga", "pending"),
        ],
        # Ahmad - preschooler milestones  
        1: [
            ("Bisa tengkurap", "done"),
            ("Bisa duduk sendiri", "done"),
            ("Bisa merangkak", "done"),
            ("Bisa berjalan", "done"),
            ("Berlari stabil", "done"),
            ("Naik turun tangga", "done"),
            ("Berbicara 2-3 kata", "done"),
            ("Makan sendiri dengan sendok", "done"),
            ("Toilet training", "done"),
            ("Menggambar garis", "done"),
            ("Menyebutkan warna", "pending"),
            ("Menghitung 1-10", "pending"),
        ],
        # Zara - infant milestones
        2: [
            ("Mengangkat kepala", "done"),
            ("Tersenyum sosial", "done"),
            ("Bisa tengkurap", "done"),
            ("Tertawa", "done"),
            ("Meraih benda", "done"),
            ("Duduk dengan bantuan", "pending"),
            ("Merangkak", "pending"),
        ],
    }
    
    for i, child_id in enumerate(child_ids):
        for milestone, status in milestones_by_age[i]:
            cur.execute(
                "INSERT INTO development (child_id, milestone, status) VALUES (?, ?, ?)",
                (child_id, milestone, status)
            )
    print(f"✅ Added milestones for all children")
    
    # ======== 5. Add Immunization Data ========
    vaccines = [
        ("Hepatitis B (HB-0)", 0),
        ("BCG", 1),
        ("Polio 1", 2),
        ("DPT-HB-Hib 1", 2),
        ("Polio 2", 3),
        ("DPT-HB-Hib 2", 3),
        ("Polio 3", 4),
        ("DPT-HB-Hib 3", 4),
        ("Polio 4 (IPV)", 4),
        ("Campak/MR 1", 9),
    ]
    
    for i, child_id in enumerate(child_ids):
        dob = datetime.strptime(children_data[i]['dob'], "%Y-%m-%d")
        child_age_months = (datetime.now() - dob).days // 30
        
        for vaccine_name, vaccine_month in vaccines:
            if vaccine_month <= child_age_months:
                date_given = (dob + timedelta(days=vaccine_month * 30)).strftime("%Y-%m-%d")
                status = "done"
            else:
                date_given = None
                status = "pending"
            
            cur.execute(
                "INSERT INTO immunization (child_id, vaccine, date_given, status) VALUES (?, ?, ?, ?)",
                (child_id, vaccine_name, date_given, status)
            )
    print(f"✅ Added immunization records for all children")
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("\n" + "="*50)
    print("🎉 Seeding completed!")
    print("="*50)
    print(f"\n📝 Login credentials:")
    print(f"   Username: ibu_sarah")
    print(f"   Password: password123")
    print(f"\n👶 Children created:")
    for child in children_data:
        print(f"   - {child['name']} ({child['gender']}, {child['dob']})")
    print()

if __name__ == "__main__":
    seed_database()
