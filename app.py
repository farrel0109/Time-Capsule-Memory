from flask import Flask, render_template, request, redirect, url_for, session, g, flash
import os
from db import get_db, init_db, close_connection

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')
app.teardown_appcontext(close_connection)

# Initialize the database inside an application context
with app.app_context():
    init_db()

@app.route('/')
def index():
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Total children
    cur = db.execute('SELECT COUNT(*) as total FROM children WHERE user_id=?', (user_id,))
    row = cur.fetchone()
    total_children = 0
    if row:
        try:
            total_children = row['total']
        except Exception:
            total_children = row[0]
    
    # Get latest growth records
    cur = db.execute('''
        SELECT c.id, c.name, g.weight, g.height, g.record_date 
        FROM children c 
        LEFT JOIN growth g ON c.id = g.child_id 
        WHERE c.user_id = ? 
        ORDER BY g.record_date DESC LIMIT 5
    ''', (user_id,))
    latest_growth = cur.fetchall()
    
    # Get milestone progress
    cur = db.execute('''
        SELECT c.id, c.name, COUNT(d.id) as total, 
               SUM(CASE WHEN d.status='done' THEN 1 ELSE 0 END) as done 
        FROM children c 
        LEFT JOIN development d ON c.id = d.child_id 
        WHERE c.user_id = ? 
        GROUP BY c.id, c.name
    ''', (user_id,))
    milestone_data = cur.fetchall()
    
    # Get immunization status
    cur = db.execute('''
        SELECT c.id, c.name, COUNT(i.id) as total, 
               SUM(CASE WHEN i.status='done' THEN 1 ELSE 0 END) as done 
        FROM children c 
        LEFT JOIN immunization i ON c.id = i.child_id 
        WHERE c.user_id = ? 
        GROUP BY c.id, c.name
    ''', (user_id,))
    immunization_data = cur.fetchall()
    
    return render_template('index.html', 
                         total_children=total_children,
                         latest_growth=latest_growth,
                         milestone_data=milestone_data,
                         immunization_data=immunization_data)

@app.route('/register', methods=['GET','POST'])
def register():
    db = get_db()
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        import hashlib
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            db.execute('INSERT INTO users (username,password) VALUES (?,?)', (username, pw_hash))
            db.commit()
            flash('Registrasi berhasil. Silakan login.')
            return redirect(url_for('login'))
        except Exception:
            flash('Username mungkin sudah ada.')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    db = get_db()
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        import hashlib
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        cur = db.execute('SELECT id FROM users WHERE username=? AND password=?', (username, pw_hash))
        row = cur.fetchone()
        if row:
            # mysql cursor with dictionary=True returns a dict, sqlite3.Row supports mapping access
            try:
                user_id = row['id']
            except Exception:
                user_id = row[0]
            session['user_id'] = user_id
            return redirect(url_for('index'))
        else:
            flash('Login gagal. Periksa username/password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/children')
def children():
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    cur = db.execute('SELECT id,name,dob,gender FROM children WHERE user_id=?', (user_id,))
    children = cur.fetchall()
    return render_template('children.html', children=children)

@app.route('/children/add', methods=['GET','POST'])
def add_child():
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    if request.method=='POST':
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        db.execute('INSERT INTO children (user_id,name,dob,gender) VALUES (?,?,?,?)',
                   (user_id,name,dob,gender))
        db.commit()
        return redirect(url_for('children'))
    return render_template('add_child.html')

@app.route('/children/<int:child_id>/edit', methods=['GET','POST'])
def edit_child(child_id):
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT id,name,dob,gender FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    if request.method=='POST':
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        db.execute('UPDATE children SET name=?,dob=?,gender=? WHERE id=? AND user_id=?',
                   (name, dob, gender, child_id, user_id))
        db.commit()
        flash('Data anak berhasil diupdate.')
        return redirect(url_for('children'))
    
    return render_template('edit_child.html', child=child)

@app.route('/children/<int:child_id>/delete', methods=['POST'])
def delete_child(child_id):
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership before deleting
    cur = db.execute('SELECT id FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    # Delete related records (growth, development, immunization)
    db.execute('DELETE FROM growth WHERE child_id=?', (child_id,))
    db.execute('DELETE FROM development WHERE child_id=?', (child_id,))
    db.execute('DELETE FROM immunization WHERE child_id=?', (child_id,))
    # Delete child
    db.execute('DELETE FROM children WHERE id=?', (child_id,))
    db.commit()
    flash('Data anak berhasil dihapus.')
    return redirect(url_for('children'))

@app.route('/children/<int:child_id>/growth')
def growth_list(child_id):
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT id,name FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    # Get growth records
    cur = db.execute('SELECT id,record_date,weight,height,head_circ FROM growth WHERE child_id=? ORDER BY record_date DESC', (child_id,))
    records = cur.fetchall()
    return render_template('growth_list.html', child=child, records=records)

@app.route('/children/<int:child_id>/growth/add', methods=['GET','POST'])
def add_growth(child_id):
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT id,name FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    if request.method=='POST':
        record_date = request.form['record_date']
        weight = request.form['weight']
        height = request.form['height']
        head_circ = request.form.get('head_circ', '')
        
        db.execute('INSERT INTO growth (child_id,record_date,weight,height,head_circ) VALUES (?,?,?,?,?)',
                   (child_id, record_date, weight, height, head_circ if head_circ else None))
        db.commit()
        flash('Data pertumbuhan berhasil ditambahkan.')
        return redirect(url_for('growth_list', child_id=child_id))
    
    return render_template('add_growth.html', child=child)

@app.route('/children/<int:child_id>/milestone')
def milestone_list(child_id):
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT id,name FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    # Get milestone records
    cur = db.execute('SELECT id,milestone,status,noted FROM development WHERE child_id=? ORDER BY id DESC', (child_id,))
    milestones = cur.fetchall()
    
    # Calculate progress
    total = len(milestones)
    done = sum(1 for m in milestones if m['status'] == 'done') if milestones else 0
    progress = int((done / total * 100)) if total > 0 else 0
    
    return render_template('milestone_list.html', child=child, milestones=milestones, progress=progress)

@app.route('/children/<int:child_id>/milestone/add', methods=['GET','POST'])
def add_milestone(child_id):
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT id,name FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    if request.method=='POST':
        milestone = request.form['milestone']
        status = request.form['status']
        noted = request.form.get('noted', '')
        
        db.execute('INSERT INTO development (child_id,milestone,status,noted) VALUES (?,?,?,?)',
                   (child_id, milestone, status, noted if noted else None))
        db.commit()
        flash('Milestone berhasil ditambahkan.')
        return redirect(url_for('milestone_list', child_id=child_id))
    
    return render_template('add_milestone.html', child=child)

@app.route('/children/<int:child_id>/milestone/<int:milestone_id>/toggle', methods=['POST'])
def toggle_milestone(child_id, milestone_id):
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT id FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    # Get current milestone status
    cur = db.execute('SELECT status FROM development WHERE id=? AND child_id=?', (milestone_id, child_id))
    milestone = cur.fetchone()
    if not milestone:
        flash('Milestone tidak ditemukan.')
        return redirect(url_for('milestone_list', child_id=child_id))
    
    # Toggle status
    new_status = 'pending' if milestone['status'] == 'done' else 'done'
    db.execute('UPDATE development SET status=? WHERE id=?', (new_status, milestone_id))
    db.commit()
    
    return redirect(url_for('milestone_list', child_id=child_id))

@app.route('/children/<int:child_id>/immunization')
def immunization_list(child_id):
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT id,name FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    # Get immunization records
    cur = db.execute('SELECT id,vaccine,date_given,status FROM immunization WHERE child_id=? ORDER BY date_given DESC', (child_id,))
    vaccinations = cur.fetchall()
    
    # Calculate status
    total = len(vaccinations)
    done = sum(1 for v in vaccinations if v['status'] == 'done') if vaccinations else 0
    
    return render_template('immunization_list.html', child=child, vaccinations=vaccinations, total=total, done=done)

@app.route('/children/<int:child_id>/immunization/add', methods=['GET','POST'])
def add_immunization(child_id):
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT id,name FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    if request.method=='POST':
        vaccine = request.form['vaccine']
        date_given = request.form['date_given']
        status = request.form['status']
        
        db.execute('INSERT INTO immunization (child_id,vaccine,date_given,status) VALUES (?,?,?,?)',
                   (child_id, vaccine, date_given, status))
        db.commit()
        flash('Vaksinasi berhasil ditambahkan.')
        return redirect(url_for('immunization_list', child_id=child_id))
    
    return render_template('add_immunization.html', child=child)

@app.route('/children/<int:child_id>/immunization/<int:vacc_id>/toggle', methods=['POST'])
def toggle_immunization(child_id, vacc_id):
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT id FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    # Get current vaccination status
    cur = db.execute('SELECT status FROM immunization WHERE id=? AND child_id=?', (vacc_id, child_id))
    vacc = cur.fetchone()
    if not vacc:
        flash('Vaksinasi tidak ditemukan.')
        return redirect(url_for('immunization_list', child_id=child_id))
    
    # Toggle status
    new_status = 'pending' if vacc['status'] == 'done' else 'done'
    db.execute('UPDATE immunization SET status=? WHERE id=?', (new_status, vacc_id))
    db.commit()
    
    return redirect(url_for('immunization_list', child_id=child_id))

# ==================== TIME CAPSULE ROUTES ====================

@app.route('/capsule')
def capsule_list():
    """List all time capsules for the user."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Get all capsules with child info
    cur = db.execute('''
        SELECT tc.*, c.name as child_name 
        FROM time_capsules tc
        JOIN children c ON tc.child_id = c.id
        WHERE c.user_id = ?
        ORDER BY tc.created_at DESC
    ''', (user_id,))
    capsules = cur.fetchall()
    
    return render_template('capsule_list.html', capsules=capsules)


@app.route('/capsule/new', methods=['GET', 'POST'])
def capsule_create():
    """Create a new time capsule."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Get user's children
    cur = db.execute('SELECT id, name FROM children WHERE user_id=?', (user_id,))
    children_list = cur.fetchall()
    
    if not children_list:
        flash('Tambahkan anak terlebih dahulu sebelum membuat kapsul waktu.')
        return redirect(url_for('add_child'))
    
    if request.method == 'POST':
        child_id = request.form['child_id']
        title = request.form['title']
        letter_content = request.form['letter_content']
        unlock_date = request.form['unlock_date']
        unlock_occasion = request.form.get('unlock_occasion', '')
        
        db.execute('''
            INSERT INTO time_capsules (child_id, title, letter_content, unlock_date, unlock_occasion)
            VALUES (?, ?, ?, ?, ?)
        ''', (child_id, title, letter_content, unlock_date, unlock_occasion))
        db.commit()
        
        flash('Kapsul waktu berhasil dibuat! 💌')
        return redirect(url_for('capsule_list'))
    
    return render_template('capsule_create.html', children=children_list)


@app.route('/capsule/<int:capsule_id>')
def capsule_view(capsule_id):
    """View a time capsule."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Get capsule with ownership check
    cur = db.execute('''
        SELECT tc.*, c.name as child_name 
        FROM time_capsules tc
        JOIN children c ON tc.child_id = c.id
        WHERE tc.id = ? AND c.user_id = ?
    ''', (capsule_id, user_id))
    capsule = cur.fetchone()
    
    if not capsule:
        flash('Kapsul tidak ditemukan.')
        return redirect(url_for('capsule_list'))
    
    # Get media attachments
    cur = db.execute('SELECT * FROM capsule_media WHERE capsule_id = ?', (capsule_id,))
    media = cur.fetchall()
    
    # Check if sealed and not yet unlockable
    from datetime import datetime
    is_sealed = capsule['is_sealed'] if isinstance(capsule, dict) else capsule[7]
    unlock_date_str = capsule['unlock_date'] if isinstance(capsule, dict) else capsule[4]
    
    if is_sealed:
        unlock_date = datetime.strptime(unlock_date_str, '%Y-%m-%d')
        can_open = datetime.now() >= unlock_date
        return render_template('capsule_sealed.html', capsule=capsule, media=media, can_open=can_open)
    
    return render_template('capsule_edit.html', capsule=capsule, media=media)


@app.route('/capsule/<int:capsule_id>/edit', methods=['POST'])
def capsule_update(capsule_id):
    """Update capsule content (before sealing)."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership and not sealed
    cur = db.execute('''
        SELECT tc.is_sealed FROM time_capsules tc
        JOIN children c ON tc.child_id = c.id
        WHERE tc.id = ? AND c.user_id = ?
    ''', (capsule_id, user_id))
    capsule = cur.fetchone()
    
    if not capsule:
        flash('Kapsul tidak ditemukan.')
        return redirect(url_for('capsule_list'))
    
    is_sealed = capsule['is_sealed'] if isinstance(capsule, dict) else capsule[0]
    if is_sealed:
        flash('Kapsul sudah disegel, tidak bisa diedit.')
        return redirect(url_for('capsule_view', capsule_id=capsule_id))
    
    title = request.form['title']
    letter_content = request.form['letter_content']
    unlock_date = request.form['unlock_date']
    unlock_occasion = request.form.get('unlock_occasion', '')
    
    db.execute('''
        UPDATE time_capsules 
        SET title=?, letter_content=?, unlock_date=?, unlock_occasion=?
        WHERE id=?
    ''', (title, letter_content, unlock_date, unlock_occasion, capsule_id))
    db.commit()
    
    flash('Kapsul berhasil diperbarui.')
    return redirect(url_for('capsule_view', capsule_id=capsule_id))


@app.route('/capsule/<int:capsule_id>/seal', methods=['POST'])
def capsule_seal(capsule_id):
    """Seal the capsule - no more edits allowed."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('''
        SELECT tc.id FROM time_capsules tc
        JOIN children c ON tc.child_id = c.id
        WHERE tc.id = ? AND c.user_id = ? AND tc.is_sealed = 0
    ''', (capsule_id, user_id))
    capsule = cur.fetchone()
    
    if not capsule:
        flash('Kapsul tidak ditemukan atau sudah disegel.')
        return redirect(url_for('capsule_list'))
    
    from datetime import datetime
    db.execute('''
        UPDATE time_capsules SET is_sealed = 1, sealed_at = ? WHERE id = ?
    ''', (datetime.now().isoformat(), capsule_id))
    db.commit()
    
    flash('🔒 Kapsul waktu berhasil disegel! Akan terbuka pada tanggal yang ditentukan.')
    return redirect(url_for('capsule_view', capsule_id=capsule_id))


@app.route('/capsule/<int:capsule_id>/open', methods=['POST'])
def capsule_open(capsule_id):
    """Open the capsule if unlock date has passed."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership and unlock date
    cur = db.execute('''
        SELECT tc.* FROM time_capsules tc
        JOIN children c ON tc.child_id = c.id
        WHERE tc.id = ? AND c.user_id = ? AND tc.is_sealed = 1
    ''', (capsule_id, user_id))
    capsule = cur.fetchone()
    
    if not capsule:
        flash('Kapsul tidak ditemukan.')
        return redirect(url_for('capsule_list'))
    
    from datetime import datetime
    unlock_date_str = capsule['unlock_date'] if isinstance(capsule, dict) else capsule[4]
    unlock_date = datetime.strptime(unlock_date_str, '%Y-%m-%d')
    
    if datetime.now() < unlock_date:
        flash('Belum waktunya membuka kapsul ini! 🔒')
        return redirect(url_for('capsule_view', capsule_id=capsule_id))
    
    db.execute('''
        UPDATE time_capsules SET opened_at = ? WHERE id = ?
    ''', (datetime.now().isoformat(), capsule_id))
    db.commit()
    
    return redirect(url_for('capsule_opened', capsule_id=capsule_id))


@app.route('/capsule/<int:capsule_id>/opened')
def capsule_opened(capsule_id):
    """View opened capsule content with celebration."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    cur = db.execute('''
        SELECT tc.*, c.name as child_name 
        FROM time_capsules tc
        JOIN children c ON tc.child_id = c.id
        WHERE tc.id = ? AND c.user_id = ? AND tc.opened_at IS NOT NULL
    ''', (capsule_id, user_id))
    capsule = cur.fetchone()
    
    if not capsule:
        flash('Kapsul tidak ditemukan atau belum dibuka.')
        return redirect(url_for('capsule_list'))
    
    cur = db.execute('SELECT * FROM capsule_media WHERE capsule_id = ?', (capsule_id,))
    media = cur.fetchall()
    
    return render_template('capsule_opened.html', capsule=capsule, media=media)


@app.route('/capsule/<int:capsule_id>/delete', methods=['POST'])
def capsule_delete(capsule_id):
    """Delete a capsule (only if not sealed)."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership and not sealed
    cur = db.execute('''
        SELECT tc.is_sealed FROM time_capsules tc
        JOIN children c ON tc.child_id = c.id
        WHERE tc.id = ? AND c.user_id = ?
    ''', (capsule_id, user_id))
    capsule = cur.fetchone()
    
    if not capsule:
        flash('Kapsul tidak ditemukan.')
        return redirect(url_for('capsule_list'))
    
    is_sealed = capsule['is_sealed'] if isinstance(capsule, dict) else capsule[0]
    if is_sealed:
        flash('Kapsul yang sudah disegel tidak bisa dihapus.')
        return redirect(url_for('capsule_list'))
    
    # Delete media first, then capsule
    db.execute('DELETE FROM capsule_media WHERE capsule_id = ?', (capsule_id,))
    db.execute('DELETE FROM time_capsules WHERE id = ?', (capsule_id,))
    db.commit()
    
    flash('Kapsul berhasil dihapus.')
    return redirect(url_for('capsule_list'))


@app.route('/capsule/<int:capsule_id>/upload', methods=['POST'])
def capsule_upload_media(capsule_id):
    """Upload media (photo) to a capsule."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership and not sealed
    cur = db.execute('''
        SELECT tc.is_sealed FROM time_capsules tc
        JOIN children c ON tc.child_id = c.id
        WHERE tc.id = ? AND c.user_id = ?
    ''', (capsule_id, user_id))
    capsule = cur.fetchone()
    
    if not capsule:
        flash('Kapsul tidak ditemukan.')
        return redirect(url_for('capsule_list'))
    
    is_sealed = capsule['is_sealed'] if isinstance(capsule, dict) else capsule[0]
    if is_sealed:
        flash('Kapsul sudah disegel, tidak bisa menambah media.')
        return redirect(url_for('capsule_view', capsule_id=capsule_id))
    
    if 'photo' not in request.files:
        flash('Tidak ada file yang dipilih.')
        return redirect(url_for('capsule_view', capsule_id=capsule_id))
    
    file = request.files['photo']
    if file.filename == '':
        flash('Tidak ada file yang dipilih.')
        return redirect(url_for('capsule_view', capsule_id=capsule_id))
    
    if file:
        import os
        from werkzeug.utils import secure_filename
        from datetime import datetime
        
        # Create upload folder
        upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'capsules')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[-1] if '.' in filename else 'jpg'
        unique_filename = f"capsule_{capsule_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        filepath = os.path.join(upload_folder, unique_filename)
        
        # Save file
        file.save(filepath)
        
        # Save to database
        file_url = f"/static/uploads/capsules/{unique_filename}"
        caption = request.form.get('caption', '')
        
        db.execute('''
            INSERT INTO capsule_media (capsule_id, media_type, file_url, caption)
            VALUES (?, 'photo', ?, ?)
        ''', (capsule_id, file_url, caption))
        db.commit()
        
        flash('📸 Foto berhasil ditambahkan!')
    
    return redirect(url_for('capsule_view', capsule_id=capsule_id))


# ==================== SETTINGS ROUTES ====================

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """User settings page."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Get current user data
    cur = db.execute('SELECT username FROM users WHERE id=?', (user_id,))
    user = cur.fetchone()
    
    # Get stats
    cur = db.execute('SELECT COUNT(*) FROM children WHERE user_id=?', (user_id,))
    total_children = cur.fetchone()[0]
    
    cur = db.execute('''
        SELECT COUNT(*) FROM time_capsules tc
        JOIN children c ON tc.child_id = c.id
        WHERE c.user_id = ?
    ''', (user_id,))
    total_capsules = cur.fetchone()[0]
    
    if request.method == 'POST':
        # Handle theme change
        theme = request.form.get('theme', 'peach')
        session['theme'] = theme
        flash('Pengaturan berhasil disimpan! ✨')
        return redirect(url_for('settings'))
    
    current_theme = session.get('theme', 'peach')
    
    return render_template('settings.html', 
                          user=user,
                          total_children=total_children,
                          total_capsules=total_capsules,
                          current_theme=current_theme)


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)

