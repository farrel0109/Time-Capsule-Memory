# Health Routes (Growth, Milestone, Immunization)
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from ..extensions import get_db
from ..auth.routes import login_required
from ..children.routes import get_child_or_404
from . import health_bp


# ============== GROWTH TRACKING ==============

@health_bp.route('/children/<int:child_id>/growth')
@login_required
def growth_list(child_id):
    """List growth records for a child."""
    child = get_child_or_404(child_id)
    if not child:
        flash('Data anak tidak ditemukan.', 'error')
        return redirect(url_for('children.list_children'))
    
    db = get_db()
    cur = db.execute('''
        SELECT id, record_date, weight, height, head_circ, notes 
        FROM growth 
        WHERE child_id = ? 
        ORDER BY record_date DESC
    ''', (child_id,))
    records = cur.fetchall()
    
    # Prepare chart data
    chart_data = {
        'labels': [],
        'weight': [],
        'height': [],
        'head_circ': []
    }
    
    for record in reversed(records):
        try:
            chart_data['labels'].append(record['record_date'])
            chart_data['weight'].append(record['weight'])
            chart_data['height'].append(record['height'])
            chart_data['head_circ'].append(record['head_circ'])
        except (TypeError, KeyError):
            chart_data['labels'].append(record[1])
            chart_data['weight'].append(record[2])
            chart_data['height'].append(record[3])
            chart_data['head_circ'].append(record[4])
    
    return render_template('health/growth_list.html', 
                         child=child, 
                         records=records,
                         chart_data=chart_data)


@health_bp.route('/children/<int:child_id>/growth/add', methods=['GET', 'POST'])
@login_required
def add_growth(child_id):
    """Add a growth record."""
    child = get_child_or_404(child_id)
    if not child:
        flash('Data anak tidak ditemukan.', 'error')
        return redirect(url_for('children.list_children'))
    
    if request.method == 'POST':
        record_date = request.form.get('record_date', '')
        weight = request.form.get('weight', '')
        height = request.form.get('height', '')
        head_circ = request.form.get('head_circ', '') or None
        notes = request.form.get('notes', '') or None
        
        if not record_date:
            flash('Tanggal pemeriksaan wajib diisi.', 'error')
            return render_template('health/add_growth.html', child=child)
        
        db = get_db()
        db.execute('''
            INSERT INTO growth (child_id, record_date, weight, height, head_circ, notes) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (child_id, record_date, weight or None, height or None, head_circ, notes))
        db.commit()
        
        flash('Data pertumbuhan berhasil ditambahkan! 📊', 'success')
        return redirect(url_for('health.growth_list', child_id=child_id))
    
    return render_template('health/add_growth.html', child=child)


@health_bp.route('/children/<int:child_id>/growth/<int:record_id>/delete', methods=['POST'])
@login_required
def delete_growth(child_id, record_id):
    """Delete a growth record."""
    child = get_child_or_404(child_id)
    if not child:
        flash('Data anak tidak ditemukan.', 'error')
        return redirect(url_for('children.list_children'))
    
    db = get_db()
    db.execute('DELETE FROM growth WHERE id = ? AND child_id = ?', (record_id, child_id))
    db.commit()
    
    flash('Data pertumbuhan dihapus.', 'info')
    return redirect(url_for('health.growth_list', child_id=child_id))


# ============== MILESTONE TRACKING ==============

MILESTONE_CATEGORIES = {
    'motorik_kasar': 'Motorik Kasar',
    'motorik_halus': 'Motorik Halus',
    'bahasa': 'Bahasa & Komunikasi',
    'sosial': 'Sosial & Emosional',
    'kognitif': 'Kognitif',
    'general': 'Umum'
}


@health_bp.route('/children/<int:child_id>/milestone')
@login_required
def milestone_list(child_id):
    """List milestones for a child."""
    child = get_child_or_404(child_id)
    if not child:
        flash('Data anak tidak ditemukan.', 'error')
        return redirect(url_for('children.list_children'))
    
    db = get_db()
    cur = db.execute('''
        SELECT id, category, milestone, status, achieved_date, noted 
        FROM development 
        WHERE child_id = ? 
        ORDER BY 
            CASE WHEN status = 'done' THEN 1 ELSE 0 END,
            id DESC
    ''', (child_id,))
    milestones = cur.fetchall()
    
    # Calculate progress per category
    progress = {}
    for cat_key in MILESTONE_CATEGORIES:
        progress[cat_key] = {'total': 0, 'done': 0}
    
    for m in milestones:
        try:
            cat = m['category'] or 'general'
            status = m['status']
        except (TypeError, KeyError):
            cat = m[1] or 'general'
            status = m[3]
        
        if cat not in progress:
            cat = 'general'
        
        progress[cat]['total'] += 1
        if status == 'done':
            progress[cat]['done'] += 1
    
    # Overall progress
    total = sum(p['total'] for p in progress.values())
    done = sum(p['done'] for p in progress.values())
    overall_progress = int((done / total * 100)) if total > 0 else 0
    
    return render_template('health/milestone_list.html',
                         child=child,
                         milestones=milestones,
                         categories=MILESTONE_CATEGORIES,
                         progress=progress,
                         overall_progress=overall_progress)


@health_bp.route('/children/<int:child_id>/milestone/add', methods=['GET', 'POST'])
@login_required
def add_milestone(child_id):
    """Add a milestone."""
    child = get_child_or_404(child_id)
    if not child:
        flash('Data anak tidak ditemukan.', 'error')
        return redirect(url_for('children.list_children'))
    
    if request.method == 'POST':
        milestone = request.form.get('milestone', '').strip()
        category = request.form.get('category', 'general')
        status = request.form.get('status', 'pending')
        achieved_date = request.form.get('achieved_date', '') or None
        noted = request.form.get('noted', '') or None
        
        if not milestone:
            flash('Nama milestone wajib diisi.', 'error')
            return render_template('health/add_milestone.html', child=child, categories=MILESTONE_CATEGORIES)
        
        db = get_db()
        db.execute('''
            INSERT INTO development (child_id, category, milestone, status, achieved_date, noted) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (child_id, category, milestone, status, achieved_date, noted))
        db.commit()
        
        flash('Milestone berhasil ditambahkan! 🌟', 'success')
        return redirect(url_for('health.milestone_list', child_id=child_id))
    
    return render_template('health/add_milestone.html', child=child, categories=MILESTONE_CATEGORIES)


@health_bp.route('/children/<int:child_id>/milestone/<int:milestone_id>/toggle', methods=['POST'])
@login_required
def toggle_milestone(child_id, milestone_id):
    """Toggle milestone status."""
    child = get_child_or_404(child_id)
    if not child:
        return jsonify({'error': 'Not found'}), 404
    
    db = get_db()
    cur = db.execute('SELECT status FROM development WHERE id = ? AND child_id = ?', (milestone_id, child_id))
    milestone = cur.fetchone()
    
    if not milestone:
        flash('Milestone tidak ditemukan.', 'error')
        return redirect(url_for('health.milestone_list', child_id=child_id))
    
    try:
        current_status = milestone['status']
    except (TypeError, KeyError):
        current_status = milestone[0]
    
    new_status = 'pending' if current_status == 'done' else 'done'
    achieved_date = 'CURRENT_DATE' if new_status == 'done' else None
    
    if new_status == 'done':
        db.execute('''
            UPDATE development 
            SET status = ?, achieved_date = DATE('now') 
            WHERE id = ?
        ''', (new_status, milestone_id))
    else:
        db.execute('UPDATE development SET status = ?, achieved_date = NULL WHERE id = ?', 
                  (new_status, milestone_id))
    db.commit()
    
    return redirect(url_for('health.milestone_list', child_id=child_id))


# ============== IMMUNIZATION TRACKING ==============

VACCINES_INDONESIA = [
    'Hepatitis B (HB-0)',
    'BCG',
    'Polio 1 (OPV)',
    'DPT-HB-Hib 1',
    'Polio 2 (OPV)',
    'DPT-HB-Hib 2',
    'Polio 3 (OPV)',
    'DPT-HB-Hib 3',
    'Polio 4 (IPV)',
    'Campak/MR 1',
    'DPT-HB-Hib Lanjutan',
    'Campak/MR Lanjutan',
    'PCV (Pneumokokus)',
    'Rotavirus',
    'Japanese Encephalitis',
    'Varicella (Cacar Air)',
    'Hepatitis A',
    'Tifoid',
    'Influenza',
    'HPV'
]


@health_bp.route('/children/<int:child_id>/immunization')
@login_required
def immunization_list(child_id):
    """List immunization records."""
    child = get_child_or_404(child_id)
    if not child:
        flash('Data anak tidak ditemukan.', 'error')
        return redirect(url_for('children.list_children'))
    
    db = get_db()
    cur = db.execute('''
        SELECT id, vaccine, scheduled_date, date_given, status, batch_number, location, notes 
        FROM immunization 
        WHERE child_id = ? 
        ORDER BY 
            CASE WHEN status = 'pending' THEN 0 ELSE 1 END,
            scheduled_date ASC
    ''', (child_id,))
    vaccinations = cur.fetchall()
    
    # Calculate stats
    total = len(vaccinations)
    done = sum(1 for v in vaccinations if (v['status'] if isinstance(v, dict) else v[4]) == 'done')
    
    return render_template('health/immunization_list.html',
                         child=child,
                         vaccinations=vaccinations,
                         total=total,
                         done=done)


@health_bp.route('/children/<int:child_id>/immunization/add', methods=['GET', 'POST'])
@login_required
def add_immunization(child_id):
    """Add an immunization record."""
    child = get_child_or_404(child_id)
    if not child:
        flash('Data anak tidak ditemukan.', 'error')
        return redirect(url_for('children.list_children'))
    
    if request.method == 'POST':
        vaccine = request.form.get('vaccine', '').strip()
        scheduled_date = request.form.get('scheduled_date', '') or None
        date_given = request.form.get('date_given', '') or None
        status = request.form.get('status', 'pending')
        batch_number = request.form.get('batch_number', '') or None
        location = request.form.get('location', '') or None
        notes = request.form.get('notes', '') or None
        
        if not vaccine:
            flash('Nama vaksin wajib diisi.', 'error')
            return render_template('health/add_immunization.html', child=child, vaccines=VACCINES_INDONESIA)
        
        db = get_db()
        db.execute('''
            INSERT INTO immunization 
            (child_id, vaccine, scheduled_date, date_given, status, batch_number, location, notes) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (child_id, vaccine, scheduled_date, date_given, status, batch_number, location, notes))
        db.commit()
        
        flash('Vaksinasi berhasil ditambahkan! 💉', 'success')
        return redirect(url_for('health.immunization_list', child_id=child_id))
    
    return render_template('health/add_immunization.html', child=child, vaccines=VACCINES_INDONESIA)


@health_bp.route('/children/<int:child_id>/immunization/<int:vacc_id>/toggle', methods=['POST'])
@login_required
def toggle_immunization(child_id, vacc_id):
    """Toggle immunization status."""
    child = get_child_or_404(child_id)
    if not child:
        return redirect(url_for('children.list_children'))
    
    db = get_db()
    cur = db.execute('SELECT status FROM immunization WHERE id = ? AND child_id = ?', (vacc_id, child_id))
    vacc = cur.fetchone()
    
    if not vacc:
        flash('Vaksinasi tidak ditemukan.', 'error')
        return redirect(url_for('health.immunization_list', child_id=child_id))
    
    try:
        current_status = vacc['status']
    except (TypeError, KeyError):
        current_status = vacc[0]
    
    new_status = 'pending' if current_status == 'done' else 'done'
    
    if new_status == 'done':
        db.execute('''
            UPDATE immunization 
            SET status = ?, date_given = DATE('now') 
            WHERE id = ?
        ''', (new_status, vacc_id))
    else:
        db.execute('UPDATE immunization SET status = ? WHERE id = ?', (new_status, vacc_id))
    db.commit()
    
    return redirect(url_for('health.immunization_list', child_id=child_id))
