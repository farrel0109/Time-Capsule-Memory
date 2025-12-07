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
        WHERE g.user_id = ? 
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
    cur = db.execute('SELECT id,name,dob FROM children WHERE user_id=?', (user_id,))
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

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
