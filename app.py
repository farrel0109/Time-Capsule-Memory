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
    cur = db.execute('SELECT COUNT(*) FROM children WHERE user_id=?', (user_id,))
    total = cur.fetchone()[0]
    return render_template('index.html', total_children=total)

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
            session['user_id'] = row[0]
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

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
