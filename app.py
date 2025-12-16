from flask import Flask, render_template, request, redirect, url_for, session, g, flash
import os
from datetime import datetime
from db import get_db, init_db, close_connection

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')
app.teardown_appcontext(close_connection)

# Custom Jinja filter for calculating days until a date
@app.template_filter('days_until')
def days_until_filter(date_str):
    """Calculate days until a date string."""
    if not date_str:
        return 0
    try:
        if isinstance(date_str, str):
            target = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            target = date_str
        delta = target - datetime.now()
        return max(0, delta.days)
    except:
        return 0

# Initialize the database inside an application context
with app.app_context():
    init_db()

@app.route('/')
def index():
    """Landing page for unauthenticated users, redirect to dashboard for authenticated."""
    user_id = session.get('user_id')
    if user_id:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')


@app.route('/dashboard')
def dashboard():
    """Protected dashboard - requires authentication."""
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
            return redirect(url_for('dashboard'))
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
    rows = cur.fetchall()
    # Convert Row objects to dicts for JSON serialization
    records = [dict(row) if hasattr(row, 'keys') else {'id': row[0], 'record_date': row[1], 'weight': row[2], 'height': row[3], 'head_circ': row[4]} for row in rows]
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


# ==================== AUDIO RECORDING ROUTES ====================

@app.route('/capsule/<int:capsule_id>/audio', methods=['GET', 'POST'])
def capsule_audio(capsule_id):
    """Record audio for a time capsule."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership and not sealed
    cur = db.execute('''
        SELECT tc.id, tc.is_sealed FROM time_capsules tc
        JOIN children c ON tc.child_id = c.id
        WHERE tc.id = ? AND c.user_id = ?
    ''', (capsule_id, user_id))
    capsule = cur.fetchone()
    
    if not capsule:
        flash('Kapsul tidak ditemukan.')
        return redirect(url_for('capsule_list'))
    
    is_sealed = capsule['is_sealed'] if isinstance(capsule, dict) else capsule[1]
    if is_sealed:
        flash('Kapsul sudah disegel, tidak bisa menambah rekaman.')
        return redirect(url_for('capsule_view', capsule_id=capsule_id))
    
    if request.method == 'POST':
        import os
        import base64
        from datetime import datetime
        
        audio_data = request.form.get('audio_data', '')
        audio_title = request.form.get('audio_title', 'Rekaman')
        
        if audio_data and audio_data.startswith('data:audio'):
            # Extract base64 data
            header, encoded = audio_data.split(',', 1)
            audio_bytes = base64.b64decode(encoded)
            
            # Create upload folder
            upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'audio')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate unique filename
            unique_filename = f"audio_{capsule_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.webm"
            filepath = os.path.join(upload_folder, unique_filename)
            
            # Save file
            with open(filepath, 'wb') as f:
                f.write(audio_bytes)
            
            # Save to database
            file_url = f"/static/uploads/audio/{unique_filename}"
            
            db.execute('''
                INSERT INTO capsule_media (capsule_id, media_type, file_url, caption)
                VALUES (?, 'audio', ?, ?)
            ''', (capsule_id, file_url, audio_title))
            db.commit()
            
            flash('🎙️ Rekaman suara berhasil ditambahkan!')
            return redirect(url_for('capsule_view', capsule_id=capsule_id))
        else:
            flash('Tidak ada rekaman yang valid.')
    
    from datetime import date
    return render_template('audio_recorder.html', 
                          capsule_id=capsule_id,
                          today=date.today().isoformat())


# ==================== CALENDAR SYNC ROUTES ====================

@app.route('/immunization/<int:child_id>/export.ics')
def export_immunization_calendar(child_id):
    """Export immunization schedule as iCalendar (.ics) file."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT name, birth_date FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    child_name = child['name'] if isinstance(child, dict) else child[0]
    
    # Get upcoming vaccinations (not completed)
    cur = db.execute('''
        SELECT vaccine_name, scheduled_date 
        FROM vaccinations 
        WHERE child_id = ? AND status != 'completed'
        ORDER BY scheduled_date
    ''', (child_id,))
    vaccinations = cur.fetchall()
    
    # Generate iCalendar content
    from datetime import datetime, timedelta
    
    ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//BabyGrow//Immunization Schedule//ID
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Jadwal Imunisasi - {child_name}
""".format(child_name=child_name)
    
    for vacc in vaccinations:
        vaccine_name = vacc['vaccine_name'] if isinstance(vacc, dict) else vacc[0]
        scheduled_date = vacc['scheduled_date'] if isinstance(vacc, dict) else vacc[1]
        
        # Parse date
        if isinstance(scheduled_date, str):
            date_obj = datetime.strptime(scheduled_date, '%Y-%m-%d')
        else:
            date_obj = scheduled_date
        
        # Create reminder 3 days before
        reminder_date = date_obj - timedelta(days=3)
        
        uid = f"babygrow-vacc-{child_id}-{vaccine_name.replace(' ', '')}"
        dtstart = date_obj.strftime('%Y%m%d')
        dtstamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')
        
        ics_content += f"""BEGIN:VEVENT
UID:{uid}@babygrow.app
DTSTAMP:{dtstamp}
DTSTART;VALUE=DATE:{dtstart}
SUMMARY:💉 Imunisasi {vaccine_name} - {child_name}
DESCRIPTION:Jadwal imunisasi {vaccine_name} untuk {child_name}. Jangan lupa bawa buku KIA!
LOCATION:Puskesmas/Rumah Sakit
BEGIN:VALARM
TRIGGER:-P3D
ACTION:DISPLAY
DESCRIPTION:Pengingat: Imunisasi {vaccine_name} 3 hari lagi!
END:VALARM
END:VEVENT
"""
    
    ics_content += "END:VCALENDAR"
    
    # Return as downloadable file
    from flask import Response
    response = Response(ics_content, mimetype='text/calendar')
    response.headers['Content-Disposition'] = f'attachment; filename=imunisasi-{child_name.replace(" ", "_")}.ics'
    return response


# ==================== FAMILY ACCESS ROUTES ====================

@app.route('/child/<int:child_id>/family', methods=['GET'])
def family_access(child_id):
    """Manage family access for a child."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT id, name FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    # Get access list
    cur = db.execute('''
        SELECT fa.*, u.username 
        FROM family_access fa
        LEFT JOIN users u ON fa.user_id = u.id
        WHERE fa.child_id = ?
        ORDER BY fa.created_at DESC
    ''', (child_id,))
    access_list = cur.fetchall()
    
    # Generate invite URL
    import secrets
    invite_code = secrets.token_urlsafe(16)
    invite_url = request.host_url + f'join/{invite_code}'
    
    return render_template('family_access.html',
                          child={'id': child['id'] if isinstance(child, dict) else child[0],
                                'name': child['name'] if isinstance(child, dict) else child[1]},
                          access_list=access_list,
                          invite_url=invite_url)


@app.route('/child/<int:child_id>/invite', methods=['POST'])
def invite_family(child_id):
    """Send invite to family member."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT id FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    if not cur.fetchone():
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    email = request.form.get('email', '').strip()
    role = request.form.get('role', 'viewer')
    
    if not email:
        flash('Email tidak boleh kosong.')
        return redirect(url_for('family_access', child_id=child_id))
    
    # Generate invite code
    import secrets
    invite_code = secrets.token_urlsafe(16)
    
    # Check if already invited
    cur = db.execute('SELECT id FROM family_access WHERE child_id=? AND invite_email=?', (child_id, email))
    if cur.fetchone():
        flash('Email ini sudah diundang sebelumnya.')
        return redirect(url_for('family_access', child_id=child_id))
    
    # Create invite
    db.execute('''
        INSERT INTO family_access (child_id, invite_code, invite_email, role, invited_by)
        VALUES (?, ?, ?, ?, ?)
    ''', (child_id, invite_code, email, role, user_id))
    db.commit()
    
    flash(f'✉️ Undangan berhasil dikirim ke {email}!')
    return redirect(url_for('family_access', child_id=child_id))


@app.route('/child/<int:child_id>/revoke/<int:access_id>', methods=['POST'])
def revoke_access(child_id, access_id):
    """Revoke family access."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db.execute('DELETE FROM family_access WHERE id=? AND child_id=?', (access_id, child_id))
    db.commit()
    
    flash('Akses berhasil dicabut.')
    return redirect(url_for('family_access', child_id=child_id))


@app.route('/join/<invite_code>')
def join_family(invite_code):
    """Accept family invite."""
    db = get_db()
    user_id = session.get('user_id')
    
    if not user_id:
        flash('Silakan login terlebih dahulu untuk menerima undangan.')
        session['pending_invite'] = invite_code
        return redirect(url_for('login'))
    
    # Find invite
    cur = db.execute('''
        SELECT fa.*, c.name as child_name 
        FROM family_access fa
        JOIN children c ON fa.child_id = c.id
        WHERE fa.invite_code = ? AND fa.status = 'pending'
    ''', (invite_code,))
    invite = cur.fetchone()
    
    if not invite:
        flash('Undangan tidak valid atau sudah digunakan.')
        return redirect(url_for('dashboard'))
    
    # Accept invite
    from datetime import datetime
    db.execute('''
        UPDATE family_access 
        SET user_id = ?, status = 'accepted', accepted_at = ?
        WHERE invite_code = ?
    ''', (user_id, datetime.now().isoformat(), invite_code))
    db.commit()
    
    child_name = invite['child_name'] if isinstance(invite, dict) else invite[-1]
    flash(f'🎉 Selamat! Anda sekarang bisa melihat data {child_name}.')
    return redirect(url_for('dashboard'))


# ==================== SCHEDULED LETTERS ROUTES ====================

@app.route('/child/<int:child_id>/letters', methods=['GET'])
def scheduled_letters(child_id):
    """View scheduled letters for a child."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT id, name FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    # Get letters
    cur = db.execute('''
        SELECT * FROM scheduled_letters 
        WHERE child_id = ? AND user_id = ?
        ORDER BY unlock_date ASC
    ''', (child_id, user_id))
    letters = cur.fetchall()
    
    return render_template('scheduled_letters.html',
                          child={'id': child['id'] if isinstance(child, dict) else child[0],
                                'name': child['name'] if isinstance(child, dict) else child[1]},
                          letters=letters)


@app.route('/child/<int:child_id>/letters/create', methods=['POST'])
def create_scheduled_letter(child_id):
    """Create a new scheduled letter."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    unlock_date = request.form.get('unlock_date', '')
    unlock_occasion = request.form.get('unlock_occasion', '')
    
    if not title or not content or not unlock_date:
        flash('Semua field wajib diisi.')
        return redirect(url_for('scheduled_letters', child_id=child_id))
    
    db.execute('''
        INSERT INTO scheduled_letters (child_id, user_id, title, content, unlock_date, unlock_occasion)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (child_id, user_id, title, content, unlock_date, unlock_occasion))
    db.commit()
    
    flash('💌 Surat berhasil disimpan!')
    return redirect(url_for('scheduled_letters', child_id=child_id))


# ==================== HEALTH INSIGHTS ROUTES ====================

@app.route('/child/<int:child_id>/insights')
def health_insights(child_id):
    """View health insights for a child."""
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Verify ownership
    cur = db.execute('SELECT id, name, dob, gender FROM children WHERE id=? AND user_id=?', (child_id, user_id))
    child = cur.fetchone()
    if not child:
        flash('Anak tidak ditemukan.')
        return redirect(url_for('children'))
    
    # Get growth data for analysis
    cur = db.execute('''
        SELECT record_date, weight, height, head_circ 
        FROM growth 
        WHERE child_id = ? 
        ORDER BY record_date DESC
        LIMIT 10
    ''', (child_id,))
    growth_records = cur.fetchall()
    
    # Generate insights
    insights = []
    
    if len(growth_records) >= 2:
        latest = growth_records[0]
        previous = growth_records[1]
        
        latest_weight = float(latest['weight'] if isinstance(latest, dict) else latest[1])
        prev_weight = float(previous['weight'] if isinstance(previous, dict) else previous[1])
        weight_change = latest_weight - prev_weight
        
        if weight_change > 0:
            insights.append({
                'type': 'positive',
                'icon': '📈',
                'title': 'Berat Badan Naik',
                'message': f'Berat badan naik {weight_change:.1f} kg dari pengukuran sebelumnya.',
                'suggestion': 'Pertahankan pola makan dan aktivitas saat ini.'
            })
        elif weight_change < 0:
            insights.append({
                'type': 'warning',
                'icon': '📉',
                'title': 'Berat Badan Turun',
                'message': f'Berat badan turun {abs(weight_change):.1f} kg dari pengukuran sebelumnya.',
                'suggestion': 'Pastikan asupan nutrisi mencukupi. Konsultasi dengan dokter jika berlanjut.'
            })
        
        latest_height = float(latest['height'] if isinstance(latest, dict) else latest[2])
        prev_height = float(previous['height'] if isinstance(previous, dict) else previous[2])
        height_change = latest_height - prev_height
        
        if height_change > 0:
            insights.append({
                'type': 'positive',
                'icon': '📏',
                'title': 'Tinggi Badan Bertambah',
                'message': f'Tinggi badan bertambah {height_change:.1f} cm.',
                'suggestion': 'Pertumbuhan sesuai harapan!'
            })
    
    # Add general tips
    insights.append({
        'type': 'info',
        'icon': '💡',
        'title': 'Tips Nutrisi',
        'message': 'Berikan makanan bergizi seimbang dengan karbohidrat, protein, dan sayuran.',
        'suggestion': 'ASI eksklusif hingga 6 bulan, lanjutkan MPASI yang bervariasi.'
    })
    
    return render_template('health_insights.html',
                          child={'id': child['id'] if isinstance(child, dict) else child[0],
                                'name': child['name'] if isinstance(child, dict) else child[1]},
                          insights=insights,
                          growth_records=growth_records)


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
