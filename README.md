# 🍼 BabyGrow - Sistem Monitoring Balita

Aplikasi web untuk memantau kesehatan dan perkembangan balita dengan fitur **Time Capsule** - menyimpan kenangan untuk si kecil di masa depan.

![BabyGrow](https://img.shields.io/badge/version-2.0.0-brightgreen)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Flask](https://img.shields.io/badge/flask-2.0+-lightgrey)
![PWA](https://img.shields.io/badge/PWA-enabled-orange)

## ✨ Fitur Lengkap

### 📊 Monitoring Kesehatan

| Fitur                 | Deskripsi                                               |
| --------------------- | ------------------------------------------------------- |
| **WHO Growth Chart**  | Grafik pertumbuhan dengan zona z-score (normal/warning) |
| **Milestone Tracker** | Track perkembangan motorik, bahasa, sosial              |
| **Imunisasi**         | Jadwal vaksinasi + ekspor ke Google Calendar            |
| **Health Insights**   | Analisis tren & saran nutrisi otomatis                  |

### 💌 Time Capsule (Fitur Unggulan)

- ✍️ Tulis surat cinta untuk anak di masa depan
- 📸 Upload foto & rekam audio kenangan
- 🔒 Segel kapsul dengan tanggal buka
- ⏳ Countdown timer hingga pembukaan
- 🎉 Animasi celebrasi saat dibuka

### 🆕 Fitur Baru v2.0

| Fitur                        | Icon | Deskripsi                            |
| ---------------------------- | ---- | ------------------------------------ |
| **Milestone Card Generator** | 🎨   | Buat kartu shareable untuk milestone |
| **Audio Recorder**           | 🎙️   | Rekam suara bayi dengan waveform     |
| **Calendar Sync**            | 📅   | Ekspor jadwal imunisasi ke .ics      |
| **Multi-Parent Access**      | 👨‍👩‍👧   | Undang keluarga (viewer/editor)      |
| **Scheduled Letters**        | 💌   | Surat terjadwal untuk masa depan     |
| **Health Insights**          | 🧠   | Analisis pertumbuhan otomatis        |
| **PWA Support**              | 📱   | Install ke homescreen + offline      |
| **Celebrations**             | 🎊   | Confetti saat milestone/capsule      |

### 🎨 Desain Premium

- Tema warna pastel (Peach, Pink, Lavender, Mint)
- UI/UX soft, warm, dan memorable
- Animasi halus dan micro-interactions
- Fully responsive untuk mobile

## 🚀 Cara Menjalankan

### Prerequisites

- Python 3.8+
- pip

### Instalasi

```bash
# Clone repository
git clone https://github.com/farrel0109/Time-Capsule-Memory.git
cd Time-Capsule-Memory

# Buat virtual environment
python -m venv .venv

# Aktifkan virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install flask python-dotenv werkzeug pillow

# Jalankan seed untuk data dummy
python seed.py

# Jalankan aplikasi
python app.py
```

Aplikasi berjalan di `http://127.0.0.1:5001`

### 🔐 Akun Demo

| Field    | Value         |
| -------- | ------------- |
| Username | `ibu_sarah`   |
| Password | `password123` |

## 📁 Struktur Folder

```
sistem-monitoring-balita/
├── app.py                 # Aplikasi Flask utama
├── db.py                  # Database connection & schema
├── seed.py                # Script data dummy (updated!)
├── database/
│   └── balita.db
├── static/
│   ├── css/style.css      # Design system
│   ├── js/
│   │   ├── celebrations.js    # Confetti & badges
│   │   ├── milestone-card.js  # Card generator
│   │   ├── audio-recorder.js  # Audio recorder
│   │   └── sw.js              # Service Worker
│   ├── manifest.json      # PWA manifest
│   └── icons/             # PWA icons
├── templates/
│   ├── base.html
│   ├── landing.html       # Landing page (new!)
│   ├── family_access.html # Multi-parent (new!)
│   ├── scheduled_letters.html # Letters (new!)
│   ├── health_insights.html   # Insights (new!)
│   ├── audio_recorder.html    # Audio (new!)
│   └── ... (other templates)
└── requirements.txt
```

## 🎨 Color Palette

| Color          | Hex       | Usage              |
| -------------- | --------- | ------------------ |
| 🍑 Soft Peach  | `#FFECD2` | Primary background |
| 🌸 Blush Pink  | `#FCB9B2` | Accent, buttons    |
| 💜 Lavender    | `#B8B8DC` | Secondary accent   |
| 🌿 Soft Mint   | `#B5EAD7` | Success states     |
| ☁️ Cloud White | `#FEFEFE` | Cards              |
| 🎀 Warm Brown  | `#5D4E37` | Text primary       |

## 📝 API Routes

### Core Routes

| Route        | Method    | Deskripsi                  |
| ------------ | --------- | -------------------------- |
| `/`          | GET       | Landing page               |
| `/dashboard` | GET       | Dashboard (login required) |
| `/login`     | GET, POST | Login                      |
| `/register`  | GET, POST | Registrasi                 |

### Child Management

| Route                         | Method | Deskripsi   |
| ----------------------------- | ------ | ----------- |
| `/children`                   | GET    | Daftar anak |
| `/children/<id>/growth`       | GET    | Pertumbuhan |
| `/children/<id>/milestone`    | GET    | Milestone   |
| `/children/<id>/immunization` | GET    | Imunisasi   |

### Time Capsule

| Route                 | Method    | Deskripsi     |
| --------------------- | --------- | ------------- |
| `/capsule`            | GET       | Daftar kapsul |
| `/capsule/<id>/audio` | GET, POST | Rekam audio   |
| `/capsule/<id>/seal`  | POST      | Segel kapsul  |

### Phase 3 Features

| Route                           | Method | Deskripsi             |
| ------------------------------- | ------ | --------------------- |
| `/child/<id>/family`            | GET    | Kelola akses keluarga |
| `/child/<id>/invite`            | POST   | Kirim undangan        |
| `/child/<id>/letters`           | GET    | Surat terjadwal       |
| `/child/<id>/insights`          | GET    | Health insights       |
| `/immunization/<id>/export.ics` | GET    | Ekspor kalender       |

## 🔧 Konfigurasi

Buat file `.env`:

```env
FLASK_SECRET=your-secret-key-here
DB_TYPE=sqlite
```

## 📜 License

MIT License - Bebas digunakan.

## 🤝 Kontribusi

Kontribusi welcome! Buat Pull Request atau open Issue.

---

Made with 💕 for Indonesian parents

**Features Implemented:**

- ✅ Phase 1: Growth Charts, Celebrations, PWA
- ✅ Phase 2: Milestone Cards, Audio Recorder, Calendar
- ✅ Phase 3: Family Access, Scheduled Letters, Health Insights
