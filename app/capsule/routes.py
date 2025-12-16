# Time Capsule Routes
from flask import render_template, request, redirect, url_for, session, flash, current_app
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename
from ..extensions import get_db
from ..auth.routes import login_required
from ..children.routes import get_child_or_404
from . import capsule_bp


UNLOCK_OCCASIONS = [
    ('birthday_17', 'Ulang Tahun ke-17'),
    ('birthday_18', 'Ulang Tahun ke-18'),
    ('birthday_21', 'Ulang Tahun ke-21'),
    ('graduation_sma', 'Kelulusan SMA'),
    ('graduation_kuliah', 'Kelulusan Kuliah'),
    ('wedding', 'Hari Pernikahan'),
    ('custom', 'Tanggal Kustom')
]


def allowed_file(filename):
    """Check if file extension is allowed."""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'mp4'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


@capsule_bp.route('/')
@login_required
def list_capsules():
    """List all time capsules for current user's children."""
    db = get_db()
    user_id = session.get('user_id')
    
    cur = db.execute('''
        SELECT tc.*, c.name as child_name, c.photo_url as child_photo
        FROM time_capsules tc
        JOIN children c ON tc.child_id = c.id
        WHERE c.user_id = ?
        ORDER BY tc.created_at DESC
    ''', (user_id,))
    capsules = cur.fetchall()
    
    # Categorize capsules
    sealed = []
    draft = []
    opened = []
    ready_to_open = []
    today = date.today().isoformat()
    
    for cap in capsules:
        try:
            is_sealed = cap['is_sealed']
            unlock_date = cap['unlock_date']
            opened_at = cap['opened_at']
        except (TypeError, KeyError):
            is_sealed = cap[6]
            unlock_date = cap[4]
            opened_at = cap[8]
        
        if opened_at:
            opened.append(cap)
        elif is_sealed:
            if unlock_date and unlock_date <= today:
                ready_to_open.append(cap)
            else:
                sealed.append(cap)
        else:
            draft.append(cap)
    
    return render_template('capsule/list.html',
                         sealed=sealed,
                         draft=draft,
                         opened=opened,
                         ready_to_open=ready_to_open)


@capsule_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_capsule():
    """Create a new time capsule."""
    db = get_db()
    user_id = session.get('user_id')
    
    # Get user's children
    cur = db.execute('SELECT id, name FROM children WHERE user_id = ?', (user_id,))
    children = cur.fetchall()
    
    if not children:
        flash('Tambahkan data anak terlebih dahulu sebelum membuat kapsul waktu.', 'warning')
        return redirect(url_for('children.add_child'))
    
    if request.method == 'POST':
        child_id = request.form.get('child_id')
        title = request.form.get('title', '').strip()
        letter_content = request.form.get('letter_content', '')
        unlock_occasion = request.form.get('unlock_occasion', 'custom')
        unlock_date = request.form.get('unlock_date', '')
        
        if not child_id or not title:
            flash('Pilih anak dan judul kapsul wajib diisi.', 'error')
            return render_template('capsule/create.html', 
                                 children=children, 
                                 occasions=UNLOCK_OCCASIONS)
        
        # Verify child ownership
        child = get_child_or_404(int(child_id))
        if not child:
            flash('Data anak tidak ditemukan.', 'error')
            return redirect(url_for('capsule.list_capsules'))
        
        db.execute('''
            INSERT INTO time_capsules 
            (child_id, title, letter_content, unlock_date, unlock_occasion) 
            VALUES (?, ?, ?, ?, ?)
        ''', (child_id, title, letter_content, unlock_date, unlock_occasion))
        db.commit()
        
        # Get the new capsule ID
        cur = db.execute('SELECT last_insert_rowid()')
        row = cur.fetchone()
        try:
            capsule_id = row[0]
        except:
            capsule_id = row['last_insert_rowid()']
        
        flash('Kapsul waktu berhasil dibuat! Tambahkan foto dan pesan. 💌', 'success')
        return redirect(url_for('capsule.edit_capsule', capsule_id=capsule_id))
    
    return render_template('capsule/create.html', 
                         children=children, 
                         occasions=UNLOCK_OCCASIONS)


@capsule_bp.route('/<int:capsule_id>')
@login_required
def view_capsule(capsule_id):
    """View a time capsule."""
    capsule = get_capsule_or_404(capsule_id)
    if not capsule:
        flash('Kapsul waktu tidak ditemukan.', 'error')
        return redirect(url_for('capsule.list_capsules'))
    
    db = get_db()
    
    # Get capsule media
    cur = db.execute('''
        SELECT id, media_type, file_url, thumbnail_url, caption 
        FROM capsule_media 
        WHERE capsule_id = ? 
        ORDER BY created_at
    ''', (capsule_id,))
    media = cur.fetchall()
    
    # Get child info
    try:
        child_id = capsule['child_id']
    except (TypeError, KeyError):
        child_id = capsule[1]
    
    cur = db.execute('SELECT name, photo_url FROM children WHERE id = ?', (child_id,))
    child = cur.fetchone()
    
    # Check if can be opened
    try:
        is_sealed = capsule['is_sealed']
        unlock_date = capsule['unlock_date']
        opened_at = capsule['opened_at']
    except (TypeError, KeyError):
        is_sealed = capsule[6]
        unlock_date = capsule[4]
        opened_at = capsule[8]
    
    can_open = is_sealed and not opened_at and unlock_date and unlock_date <= date.today().isoformat()
    
    return render_template('capsule/view.html',
                         capsule=capsule,
                         media=media,
                         child=child,
                         can_open=can_open)


@capsule_bp.route('/<int:capsule_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_capsule(capsule_id):
    """Edit a time capsule (only if not sealed)."""
    capsule = get_capsule_or_404(capsule_id)
    if not capsule:
        flash('Kapsul waktu tidak ditemukan.', 'error')
        return redirect(url_for('capsule.list_capsules'))
    
    try:
        is_sealed = capsule['is_sealed']
    except (TypeError, KeyError):
        is_sealed = capsule[6]
    
    if is_sealed:
        flash('Kapsul yang sudah disegel tidak dapat diedit.', 'warning')
        return redirect(url_for('capsule.view_capsule', capsule_id=capsule_id))
    
    db = get_db()
    
    # Get media
    cur = db.execute('''
        SELECT id, media_type, file_url, thumbnail_url, caption 
        FROM capsule_media 
        WHERE capsule_id = ?
    ''', (capsule_id,))
    media = cur.fetchall()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        letter_content = request.form.get('letter_content', '')
        unlock_occasion = request.form.get('unlock_occasion', 'custom')
        unlock_date = request.form.get('unlock_date', '')
        
        db.execute('''
            UPDATE time_capsules 
            SET title = ?, letter_content = ?, unlock_occasion = ?, unlock_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (title, letter_content, unlock_occasion, unlock_date, capsule_id))
        db.commit()
        
        flash('Kapsul waktu berhasil diupdate! ✨', 'success')
        return redirect(url_for('capsule.edit_capsule', capsule_id=capsule_id))
    
    return render_template('capsule/edit.html',
                         capsule=capsule,
                         media=media,
                         occasions=UNLOCK_OCCASIONS)


@capsule_bp.route('/<int:capsule_id>/add-media', methods=['POST'])
@login_required
def add_media(capsule_id):
    """Add media to a time capsule."""
    capsule = get_capsule_or_404(capsule_id)
    if not capsule:
        flash('Kapsul waktu tidak ditemukan.', 'error')
        return redirect(url_for('capsule.list_capsules'))
    
    try:
        is_sealed = capsule['is_sealed']
    except (TypeError, KeyError):
        is_sealed = capsule[6]
    
    if is_sealed:
        flash('Tidak dapat menambah media ke kapsul yang sudah disegel.', 'warning')
        return redirect(url_for('capsule.view_capsule', capsule_id=capsule_id))
    
    if 'file' not in request.files:
        flash('Tidak ada file yang dipilih.', 'error')
        return redirect(url_for('capsule.edit_capsule', capsule_id=capsule_id))
    
    file = request.files['file']
    caption = request.form.get('caption', '')
    
    if file.filename == '':
        flash('Tidak ada file yang dipilih.', 'error')
        return redirect(url_for('capsule.edit_capsule', capsule_id=capsule_id))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to filename
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
        
        # Determine media type
        ext_lower = ext.lower()
        if ext_lower in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            media_type = 'photo'
        elif ext_lower in ['.mp3', '.wav', '.ogg']:
            media_type = 'audio'
        elif ext_lower in ['.mp4', '.webm', '.mov']:
            media_type = 'video'
        else:
            media_type = 'other'
        
        # Save file
        upload_folder = current_app.config['UPLOAD_FOLDER']
        capsule_folder = os.path.join(upload_folder, 'capsules', str(capsule_id))
        os.makedirs(capsule_folder, exist_ok=True)
        
        file_path = os.path.join(capsule_folder, filename)
        file.save(file_path)
        
        # Save to database
        file_url = f"/uploads/capsules/{capsule_id}/{filename}"
        
        db = get_db()
        db.execute('''
            INSERT INTO capsule_media (capsule_id, media_type, file_url, caption)
            VALUES (?, ?, ?, ?)
        ''', (capsule_id, media_type, file_url, caption))
        db.commit()
        
        flash('Media berhasil ditambahkan! 📸', 'success')
    else:
        flash('Tipe file tidak didukung.', 'error')
    
    return redirect(url_for('capsule.edit_capsule', capsule_id=capsule_id))


@capsule_bp.route('/<int:capsule_id>/seal', methods=['POST'])
@login_required
def seal_capsule(capsule_id):
    """Seal a time capsule."""
    capsule = get_capsule_or_404(capsule_id)
    if not capsule:
        flash('Kapsul waktu tidak ditemukan.', 'error')
        return redirect(url_for('capsule.list_capsules'))
    
    try:
        is_sealed = capsule['is_sealed']
        unlock_date = capsule['unlock_date']
    except (TypeError, KeyError):
        is_sealed = capsule[6]
        unlock_date = capsule[4]
    
    if is_sealed:
        flash('Kapsul sudah disegel sebelumnya.', 'info')
        return redirect(url_for('capsule.view_capsule', capsule_id=capsule_id))
    
    if not unlock_date:
        flash('Tentukan tanggal buka kapsul terlebih dahulu.', 'error')
        return redirect(url_for('capsule.edit_capsule', capsule_id=capsule_id))
    
    db = get_db()
    db.execute('''
        UPDATE time_capsules 
        SET is_sealed = 1, sealed_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (capsule_id,))
    db.commit()
    
    flash('Kapsul waktu berhasil disegel! 🔒 Kapsul akan dapat dibuka pada tanggal yang ditentukan.', 'success')
    return redirect(url_for('capsule.view_capsule', capsule_id=capsule_id))


@capsule_bp.route('/<int:capsule_id>/open', methods=['POST'])
@login_required
def open_capsule(capsule_id):
    """Open a sealed time capsule."""
    capsule = get_capsule_or_404(capsule_id)
    if not capsule:
        flash('Kapsul waktu tidak ditemukan.', 'error')
        return redirect(url_for('capsule.list_capsules'))
    
    try:
        is_sealed = capsule['is_sealed']
        unlock_date = capsule['unlock_date']
        opened_at = capsule['opened_at']
    except (TypeError, KeyError):
        is_sealed = capsule[6]
        unlock_date = capsule[4]
        opened_at = capsule[8]
    
    if not is_sealed:
        flash('Kapsul belum disegel.', 'warning')
        return redirect(url_for('capsule.edit_capsule', capsule_id=capsule_id))
    
    if opened_at:
        flash('Kapsul sudah pernah dibuka.', 'info')
        return redirect(url_for('capsule.view_capsule', capsule_id=capsule_id))
    
    today = date.today().isoformat()
    if unlock_date and unlock_date > today:
        flash(f'Kapsul baru dapat dibuka pada {unlock_date}.', 'warning')
        return redirect(url_for('capsule.view_capsule', capsule_id=capsule_id))
    
    db = get_db()
    db.execute('''
        UPDATE time_capsules 
        SET opened_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (capsule_id,))
    db.commit()
    
    flash('🎉 Selamat! Kapsul waktu telah dibuka! Nikmati kenangan indah ini.', 'success')
    return redirect(url_for('capsule.view_capsule', capsule_id=capsule_id))


@capsule_bp.route('/<int:capsule_id>/delete', methods=['POST'])
@login_required
def delete_capsule(capsule_id):
    """Delete a time capsule."""
    capsule = get_capsule_or_404(capsule_id)
    if not capsule:
        flash('Kapsul waktu tidak ditemukan.', 'error')
        return redirect(url_for('capsule.list_capsules'))
    
    db = get_db()
    
    # Delete media files
    cur = db.execute('SELECT file_url FROM capsule_media WHERE capsule_id = ?', (capsule_id,))
    media_files = cur.fetchall()
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    for media in media_files:
        try:
            file_url = media['file_url'] if isinstance(media, dict) else media[0]
            if file_url:
                file_path = os.path.join(upload_folder, file_url.lstrip('/uploads/'))
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception:
            pass
    
    # Delete from database
    db.execute('DELETE FROM capsule_media WHERE capsule_id = ?', (capsule_id,))
    db.execute('DELETE FROM time_capsules WHERE id = ?', (capsule_id,))
    db.commit()
    
    flash('Kapsul waktu telah dihapus.', 'info')
    return redirect(url_for('capsule.list_capsules'))


def get_capsule_or_404(capsule_id):
    """Get capsule if owned by current user."""
    db = get_db()
    user_id = session.get('user_id')
    
    if not user_id:
        return None
    
    cur = db.execute('''
        SELECT tc.* 
        FROM time_capsules tc
        JOIN children c ON tc.child_id = c.id
        WHERE tc.id = ? AND c.user_id = ?
    ''', (capsule_id, user_id))
    return cur.fetchone()
