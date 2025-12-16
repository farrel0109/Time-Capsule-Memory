"""
Seed script untuk menambahkan data dummy ke database BabyGrow.
Membuat 1 user dengan 3 anak beserta data kesehatan lengkap.
Termasuk data untuk semua fitur Phase 1-3.
"""
import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
import random
import secrets

# Path database - sama dengan db.py
DATABASE_DIR = os.path.join(os.path.dirname(__file__), 'database')
DATABASE = os.path.join(DATABASE_DIR, 'balita.db')

def init_tables(cur):
    """Create tables if not exist."""
    # Users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT,
            full_name TEXT,
            avatar_url TEXT,
            preferred_theme TEXT DEFAULT 'peach',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Children
    cur.execute("""
        CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            dob TEXT,
            gender TEXT,
            photo_url TEXT,
            blood_type TEXT,
            allergies TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Growth
    cur.execute("""
        CREATE TABLE IF NOT EXISTS growth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            record_date TEXT,
            weight REAL,
            height REAL,
            head_circ REAL,
            notes TEXT
        )
    """)
    
    # Development/Milestones
    cur.execute("""
        CREATE TABLE IF NOT EXISTS development (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            category TEXT DEFAULT 'general',
            milestone TEXT,
            status TEXT DEFAULT 'pending',
            achieved_date TEXT,
            noted TEXT
        )
    """)
    
    # Immunization
    cur.execute("""
        CREATE TABLE IF NOT EXISTS immunization (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            vaccine TEXT,
            scheduled_date TEXT,
            date_given TEXT,
            status TEXT DEFAULT 'pending',
            location TEXT,
            notes TEXT
        )
    """)
    
    # Time Capsules
    cur.execute("""
        CREATE TABLE IF NOT EXISTS time_capsules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    
    # Capsule Media
    cur.execute("""
        CREATE TABLE IF NOT EXISTS capsule_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capsule_id INTEGER NOT NULL,
            media_type TEXT NOT NULL,
            file_url TEXT NOT NULL,
            thumbnail_url TEXT,
            caption TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Family Access (Phase 3)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS family_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    
    # Scheduled Letters (Phase 3)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    
    # Health Insights (Phase 3)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS health_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER NOT NULL,
            insight_type TEXT NOT NULL,
            insight_data TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    print("🌱 Seeding database for BabyGrow...")
    print("=" * 50)
    
    # ======== 1. Create Parent User ========
    username = "ibu_sarah"
    email = "sarah@babygrow.id"
    password = hashlib.sha256("password123".encode()).hexdigest()
    
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    
    if not user:
        cur.execute(
            "INSERT INTO users (username, email, password, full_name, preferred_theme) VALUES (?, ?, ?, ?, ?)",
            (username, email, password, "Sarah Amelia", "peach")
        )
        user_id = cur.lastrowid
        print(f"✅ Created user: {username}")
    else:
        user_id = user['id']
        print(f"ℹ️ User already exists: {username}")
    
    # ======== 2. Create 3 Children ========
    children_data = [
        {"name": "Aisha Putri", "dob": "2023-03-15", "gender": "Perempuan", "blood_type": "A"},
        {"name": "Ahmad Khalil", "dob": "2021-08-22", "gender": "Laki-laki", "blood_type": "O"},
        {"name": "Zara Amelia", "dob": "2024-01-10", "gender": "Perempuan", "blood_type": "B"},
    ]
    
    child_ids = []
    for child in children_data:
        cur.execute("SELECT id FROM children WHERE name = ? AND user_id = ?", (child['name'], user_id))
        existing = cur.fetchone()
        
        if not existing:
            cur.execute(
                "INSERT INTO children (user_id, name, dob, gender, blood_type) VALUES (?, ?, ?, ?, ?)",
                (user_id, child['name'], child['dob'], child['gender'], child['blood_type'])
            )
            child_id = cur.lastrowid
            child_ids.append(child_id)
            print(f"✅ Created child: {child['name']}")
        else:
            child_ids.append(existing['id'])
            print(f"ℹ️ Child already exists: {child['name']}")
    
    # ======== 3. Add Growth Data ========
    growth_templates = [
        # Aisha (1.5 tahun)
        [
            {"months": 0, "weight": 3.2, "height": 50, "head": 35},
            {"months": 3, "weight": 5.5, "height": 60, "head": 40},
            {"months": 6, "weight": 7.0, "height": 66, "head": 43},
            {"months": 9, "weight": 8.2, "height": 71, "head": 45},
            {"months": 12, "weight": 9.0, "height": 75, "head": 46},
            {"months": 18, "weight": 10.5, "height": 82, "head": 47},
        ],
        # Ahmad (3+ tahun)
        [
            {"months": 0, "weight": 3.5, "height": 52, "head": 36},
            {"months": 6, "weight": 7.8, "height": 68, "head": 44},
            {"months": 12, "weight": 9.5, "height": 76, "head": 46},
            {"months": 24, "weight": 12.5, "height": 88, "head": 48},
            {"months": 36, "weight": 15.0, "height": 98, "head": 50},
        ],
        # Zara (11 bulan)
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
    print(f"✅ Added growth records")
    
    # ======== 4. Add Milestones ========
    milestones_by_age = {
        0: [("Bisa tengkurap", "done"), ("Bisa duduk sendiri", "done"), ("Bisa berjalan", "done"), ("Mengucapkan 'mama'", "done"), ("Berlari", "pending")],
        1: [("Bisa berjalan", "done"), ("Berlari stabil", "done"), ("Toilet training", "done"), ("Menyebutkan warna", "pending"), ("Menghitung 1-10", "pending")],
        2: [("Mengangkat kepala", "done"), ("Tersenyum sosial", "done"), ("Bisa tengkurap", "done"), ("Merangkak", "pending")],
    }
    
    for i, child_id in enumerate(child_ids):
        for milestone, status in milestones_by_age[i]:
            cur.execute("INSERT INTO development (child_id, milestone, status) VALUES (?, ?, ?)", (child_id, milestone, status))
    print(f"✅ Added milestones")
    
    # ======== 5. Add Immunization ========
    vaccines = [
        ("Hepatitis B (HB-0)", 0), ("BCG", 1), ("Polio 1", 2), ("DPT-HB-Hib 1", 2),
        ("Polio 2", 3), ("DPT-HB-Hib 2", 3), ("Campak/MR 1", 9),
    ]
    
    for i, child_id in enumerate(child_ids):
        dob = datetime.strptime(children_data[i]['dob'], "%Y-%m-%d")
        child_age_months = (datetime.now() - dob).days // 30
        
        for vaccine_name, vaccine_month in vaccines:
            scheduled_date = (dob + timedelta(days=vaccine_month * 30)).strftime("%Y-%m-%d")
            if vaccine_month <= child_age_months:
                status = "done"
                date_given = scheduled_date
            else:
                status = "pending"
                date_given = None
            
            cur.execute(
                "INSERT INTO immunization (child_id, vaccine, scheduled_date, date_given, status) VALUES (?, ?, ?, ?, ?)",
                (child_id, vaccine_name, scheduled_date, date_given, status)
            )
    print(f"✅ Added immunization records")
    
    # ======== 6. Add Time Capsules ========
    capsules = [
        {
            "child_id": child_ids[0],
            "title": "Untuk Ulang Tahun ke-5 Aisha",
            "letter_content": "Sayang Aisha, ketika kamu membaca ini, kamu sudah berusia 5 tahun! Mama masih ingat tangisan pertamamu...",
            "unlock_date": "2028-03-15",
            "unlock_occasion": "Ulang Tahun ke-5",
            "is_sealed": 1,
        },
        {
            "child_id": child_ids[1],
            "title": "Surat untuk Ahmad saat Masuk SD",
            "letter_content": "Ahmad sayang, hari ini kamu mulai perjalanan barumu di sekolah dasar...",
            "unlock_date": "2028-07-01",
            "unlock_occasion": "Masuk SD",
            "is_sealed": 0,
        },
    ]
    
    for capsule in capsules:
        cur.execute("""
            INSERT INTO time_capsules (child_id, title, letter_content, unlock_date, unlock_occasion, is_sealed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (capsule['child_id'], capsule['title'], capsule['letter_content'], 
              capsule['unlock_date'], capsule['unlock_occasion'], capsule['is_sealed']))
    print(f"✅ Added time capsules")
    
    # ======== 7. Add Scheduled Letters (Phase 3) ========
    letters = [
        {
            "child_id": child_ids[0],
            "user_id": user_id,
            "title": "Untuk Hari Pertama Sekolah",
            "content": "Aisha sayang, hari ini adalah hari bersejarah! Kamu mulai sekolah TK...",
            "unlock_date": "2027-07-15",
            "unlock_occasion": "Hari Pertama Sekolah",
        },
        {
            "child_id": child_ids[1],
            "user_id": user_id,
            "title": "Untuk Ulang Tahun ke-10",
            "content": "Ahmad, sekarang kamu sudah 10 tahun! Mama bangga dengan semua yang sudah kamu capai...",
            "unlock_date": "2031-08-22",
            "unlock_occasion": "Ulang Tahun ke-10",
        },
    ]
    
    for letter in letters:
        cur.execute("""
            INSERT INTO scheduled_letters (child_id, user_id, title, content, unlock_date, unlock_occasion)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (letter['child_id'], letter['user_id'], letter['title'], 
              letter['content'], letter['unlock_date'], letter['unlock_occasion']))
    print(f"✅ Added scheduled letters")
    
    # ======== 8. Add Family Access Invites (Phase 3) ========
    invites = [
        {"child_id": child_ids[0], "invite_email": "nenek@email.com", "role": "viewer"},
        {"child_id": child_ids[0], "invite_email": "kakek@email.com", "role": "viewer"},
    ]
    
    for invite in invites:
        invite_code = secrets.token_urlsafe(16)
        cur.execute("""
            INSERT INTO family_access (child_id, invite_code, invite_email, role, invited_by)
            VALUES (?, ?, ?, ?, ?)
        """, (invite['child_id'], invite_code, invite['invite_email'], invite['role'], user_id))
    print(f"✅ Added family access invites")
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("🎉 Seeding completed!")
    print("=" * 50)
    print(f"\n📝 Login credentials:")
    print(f"   Username: ibu_sarah")
    print(f"   Password: password123")
    print(f"\n👶 Children: {', '.join([c['name'] for c in children_data])}")
    print(f"💌 Time Capsules: 2")
    print(f"📬 Scheduled Letters: 2")
    print(f"👨‍👩‍👧 Family Invites: 2")
    print()

if __name__ == "__main__":
    seed_database()
