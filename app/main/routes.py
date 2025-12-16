# Main Routes (Dashboard, Landing Page)
from flask import render_template, redirect, url_for, session
from ..extensions import get_db
from ..auth.routes import login_required, get_current_user
from . import main_bp


@main_bp.route('/')
def index():
    """Landing page or redirect to dashboard."""
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with overview of all children."""
    db = get_db()
    user_id = session.get('user_id')
    user = get_current_user()
    
    # Get user's children
    cur = db.execute('''
        SELECT id, name, dob, gender, photo_url 
        FROM children 
        WHERE user_id = ? 
        ORDER BY name
    ''', (user_id,))
    children = cur.fetchall()
    
    # Get stats for each child
    children_with_stats = []
    for child in children:
        try:
            child_id = child['id']
            child_name = child['name']
            child_dob = child['dob']
            child_gender = child['gender']
            child_photo = child['photo_url']
        except (TypeError, KeyError):
            child_id = child[0]
            child_name = child[1]
            child_dob = child[2]
            child_gender = child[3]
            child_photo = child[4]
        
        # Latest growth
        cur = db.execute('''
            SELECT weight, height, record_date 
            FROM growth 
            WHERE child_id = ? 
            ORDER BY record_date DESC 
            LIMIT 1
        ''', (child_id,))
        latest_growth = cur.fetchone()
        
        # Milestone progress
        cur = db.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done
            FROM development 
            WHERE child_id = ?
        ''', (child_id,))
        milestone_stats = cur.fetchone()
        
        # Vaccination progress
        cur = db.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done
            FROM immunization 
            WHERE child_id = ?
        ''', (child_id,))
        vaccine_stats = cur.fetchone()
        
        # Time capsules count
        cur = db.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN is_sealed = 1 THEN 1 ELSE 0 END) as sealed
            FROM time_capsules 
            WHERE child_id = ?
        ''', (child_id,))
        capsule_stats = cur.fetchone()
        
        children_with_stats.append({
            'id': child_id,
            'name': child_name,
            'dob': child_dob,
            'gender': child_gender,
            'photo_url': child_photo,
            'latest_growth': latest_growth,
            'milestone_stats': milestone_stats,
            'vaccine_stats': vaccine_stats,
            'capsule_stats': capsule_stats
        })
    
    # Get upcoming vaccinations
    cur = db.execute('''
        SELECT i.vaccine, i.scheduled_date, c.name as child_name
        FROM immunization i
        JOIN children c ON i.child_id = c.id
        WHERE c.user_id = ? AND i.status = 'pending' AND i.scheduled_date IS NOT NULL
        ORDER BY i.scheduled_date ASC
        LIMIT 5
    ''', (user_id,))
    upcoming_vaccines = cur.fetchall()
    
    # Get recent milestones achieved
    cur = db.execute('''
        SELECT d.milestone, d.achieved_date, c.name as child_name
        FROM development d
        JOIN children c ON d.child_id = c.id
        WHERE c.user_id = ? AND d.status = 'done' AND d.achieved_date IS NOT NULL
        ORDER BY d.achieved_date DESC
        LIMIT 5
    ''', (user_id,))
    recent_milestones = cur.fetchall()
    
    return render_template('dashboard.html',
                         user=user,
                         children=children_with_stats,
                         upcoming_vaccines=upcoming_vaccines,
                         recent_milestones=recent_milestones)


@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page."""
    from flask import request, flash
    
    user = get_current_user()
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip() or None
        preferred_theme = request.form.get('preferred_theme', 'peach')
        
        db = get_db()
        user_id = session.get('user_id')
        
        db.execute('''
            UPDATE users 
            SET full_name = ?, email = ?, preferred_theme = ?
            WHERE id = ?
        ''', (full_name, email, preferred_theme, user_id))
        db.commit()
        
        flash('Pengaturan berhasil disimpan! ✨', 'success')
        return redirect(url_for('main.settings'))
    
    return render_template('settings.html', user=user)
