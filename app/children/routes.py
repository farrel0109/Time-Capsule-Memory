# Children Routes
from flask import render_template, request, redirect, url_for, session, flash
from ..extensions import get_db
from ..auth.routes import login_required
from . import children_bp


@children_bp.route('/')
@login_required
def list_children():
    """List all children for current user."""
    db = get_db()
    user_id = session.get('user_id')
    
    cur = db.execute('''
        SELECT id, name, dob, gender, photo_url 
        FROM children 
        WHERE user_id = ? 
        ORDER BY name
    ''', (user_id,))
    children = cur.fetchall()
    
    return render_template('children/list.html', children=children)


@children_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_child():
    """Add a new child."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        dob = request.form.get('dob', '')
        gender = request.form.get('gender', '')
        blood_type = request.form.get('blood_type', '') or None
        notes = request.form.get('notes', '') or None
        
        if not name or not dob:
            flash('Nama dan tanggal lahir wajib diisi.', 'error')
            return render_template('children/add.html')
        
        db = get_db()
        user_id = session.get('user_id')
        
        db.execute('''
            INSERT INTO children (user_id, name, dob, gender, blood_type, notes) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, name, dob, gender, blood_type, notes))
        db.commit()
        
        flash(f'Data {name} berhasil ditambahkan! 🎉', 'success')
        return redirect(url_for('children.list_children'))
    
    return render_template('children/add.html')


@children_bp.route('/<int:child_id>')
@login_required
def view_child(child_id):
    """View child details."""
    db = get_db()
    user_id = session.get('user_id')
    
    cur = db.execute('''
        SELECT id, name, dob, gender, photo_url, blood_type, notes, created_at 
        FROM children 
        WHERE id = ? AND user_id = ?
    ''', (child_id, user_id))
    child = cur.fetchone()
    
    if not child:
        flash('Data anak tidak ditemukan.', 'error')
        return redirect(url_for('children.list_children'))
    
    # Get latest growth data
    cur = db.execute('''
        SELECT weight, height, head_circ, record_date 
        FROM growth 
        WHERE child_id = ? 
        ORDER BY record_date DESC 
        LIMIT 1
    ''', (child_id,))
    latest_growth = cur.fetchone()
    
    # Get milestone progress
    cur = db.execute('''
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done
        FROM development 
        WHERE child_id = ?
    ''', (child_id,))
    milestone_stats = cur.fetchone()
    
    # Get vaccination progress
    cur = db.execute('''
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done
        FROM immunization 
        WHERE child_id = ?
    ''', (child_id,))
    vaccine_stats = cur.fetchone()
    
    return render_template('children/view.html', 
                         child=child, 
                         latest_growth=latest_growth,
                         milestone_stats=milestone_stats,
                         vaccine_stats=vaccine_stats)


@children_bp.route('/<int:child_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_child(child_id):
    """Edit child data."""
    db = get_db()
    user_id = session.get('user_id')
    
    cur = db.execute('SELECT * FROM children WHERE id = ? AND user_id = ?', (child_id, user_id))
    child = cur.fetchone()
    
    if not child:
        flash('Data anak tidak ditemukan.', 'error')
        return redirect(url_for('children.list_children'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        dob = request.form.get('dob', '')
        gender = request.form.get('gender', '')
        blood_type = request.form.get('blood_type', '') or None
        notes = request.form.get('notes', '') or None
        
        if not name or not dob:
            flash('Nama dan tanggal lahir wajib diisi.', 'error')
            return render_template('children/edit.html', child=child)
        
        db.execute('''
            UPDATE children 
            SET name = ?, dob = ?, gender = ?, blood_type = ?, notes = ?
            WHERE id = ? AND user_id = ?
        ''', (name, dob, gender, blood_type, notes, child_id, user_id))
        db.commit()
        
        flash('Data berhasil diupdate! ✨', 'success')
        return redirect(url_for('children.view_child', child_id=child_id))
    
    return render_template('children/edit.html', child=child)


@children_bp.route('/<int:child_id>/delete', methods=['POST'])
@login_required
def delete_child(child_id):
    """Delete a child and all related data."""
    db = get_db()
    user_id = session.get('user_id')
    
    cur = db.execute('SELECT name FROM children WHERE id = ? AND user_id = ?', (child_id, user_id))
    child = cur.fetchone()
    
    if not child:
        flash('Data anak tidak ditemukan.', 'error')
        return redirect(url_for('children.list_children'))
    
    try:
        child_name = child['name']
    except (TypeError, KeyError):
        child_name = child[0]
    
    # Delete all related data
    db.execute('DELETE FROM growth WHERE child_id = ?', (child_id,))
    db.execute('DELETE FROM development WHERE child_id = ?', (child_id,))
    db.execute('DELETE FROM immunization WHERE child_id = ?', (child_id,))
    db.execute('DELETE FROM time_capsules WHERE child_id = ?', (child_id,))
    db.execute('DELETE FROM media WHERE child_id = ?', (child_id,))
    db.execute('DELETE FROM children WHERE id = ?', (child_id,))
    db.commit()
    
    flash(f'Data {child_name} telah dihapus.', 'info')
    return redirect(url_for('children.list_children'))


def get_child_or_404(child_id):
    """Helper to get child data or return None if not found/not owned."""
    db = get_db()
    user_id = session.get('user_id')
    
    if not user_id:
        return None
    
    cur = db.execute('SELECT * FROM children WHERE id = ? AND user_id = ?', (child_id, user_id))
    return cur.fetchone()
