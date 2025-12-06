Project Name: Sistem Monitoring Balita
Goal: Membuat aplikasi web sederhana untuk memonitor pertumbuhan, perkembangan milestone, dan imunisasi anak balita. Orang tua dapat membuat akun, menambahkan anak, dan mengupdate data perkembangan secara berkala.

Tools:
| Bagian   | Tools                         |
| -------- | ----------------------------- |
| Backend  | Python Flask                  |
| Frontend | HTML, CSS, Bootstrap/Tailwind |
| Grafik   | Chart.js                      |
| Database | SQLite/MySQL                  |

-------------------------------------------------------

## Task Breakdown Detail

### 1. Setup Project
- Buat struktur folder project Flask:
  /templates, /static/css, /static/js, /database
- Install dependencies:
  `pip install flask mysql-connector-python`
- Buat file utama `app.py`
- Buat file `db.py` untuk koneksi database

### 2. Database Implementation
- Buat database `balita_db` (MySQL/SQLite)
- Buat tabel:
  users, children, growth, development, immunization
- Implementasikan hubungan:
  users (1) → children (many)
  children (1) → growth/milestone/immunization (many)

### 3. Authentication System (Login & Register)
- Buat page register + login menggunakan HTML/CSS/Bootstrap
- Simpan password menggunakan hash
- Implement session Flask untuk login user
- Setelah login: redirect ke dashboard anak

### 4. Child Management (CRUD Anak)
- Halaman tambah anak
- Halaman daftar anak
- Edit data anak
- Delete anak
- Data ditampilkan berdasarkan `user_id`

### 5. Monitoring Pertumbuhan (Growth Tracking)
- Page input pertumbuhan (weight/height/head circumference)
- Page list pertumbuhan per anak
- Generate grafik Chart.js berdasarkan `record_date`
- Bandingkan dengan standar WHO jika memungkinkan

### 6. Monitoring Perkembangan (Milestone Tracking)
- Checklist milestone per anak
- Tampilkan progress milestone dalam persentase
- Notifikasi milestone yang tertunda

### 7. Imunisasi Management
- Input jadwal & status vaksin
- Tampilkan list vaksin wajib
- Update status “done / pending”
- Reminder tanggal vaksin berikutnya

### 8. Dashboard
- Tampilkan card summary:
  - Total anak
  - Status pertumbuhan terakhir
  - Progress milestone
  - Status imunisasi
- Include mini Chart.js ringkas

### 9. Frontend UI
- Gunakan Bootstrap/Tailwind untuk layout bersih & responsive
- Gunakan warna pastel / biru baby theme
- Navigasi navbar untuk akses modul

### 10. Testing & Deployment
- Test form input, grafik, login, db relation
- Deploy lokal dulu
- Export .zip mini project untuk laporan

-------------------------------------------------------

## Deliverables / Output Akhir
- Website monitoring balita dengan login user
- CRUD anak & form monitoring
- Grafik pertumbuhan via Chart.js
- Checklist milestone & imunisasi
- Dokumentasi + diagram database + laporan

-------------------------------------------------------

## Optional Improvements (if extended)
- Role admin
- Upload foto anak
- Export PDF laporan perkembangan
- Bot WhatsApp reminder imunisasi
- Dark mode UI
