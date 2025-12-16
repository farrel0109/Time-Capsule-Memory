# Auth Routes
from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import get_db
from . import auth_bp


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip() or None
        full_name = request.form.get('full_name', '').strip() or None
        
        if not username or not password:
            flash('Username dan password wajib diisi.', 'error')
            return render_template('auth/register.html')
        
        # Hash password with werkzeug (more secure than SHA256)
        pw_hash = generate_password_hash(password)
        
        db = get_db()
        try:
            db.execute(
                'INSERT INTO users (username, email, password, full_name) VALUES (?, ?, ?, ?)',
                (username, email, pw_hash, full_name)
            )
            db.commit()
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash('Username atau email sudah terdaftar.', 'error')
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username dan password wajib diisi.', 'error')
            return render_template('auth/login.html')
        
        db = get_db()
        cur = db.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        row = cur.fetchone()
        
        if row:
            try:
                user_id = row['id']
                stored_hash = row['password']
            except (TypeError, KeyError):
                user_id = row[0]
                stored_hash = row[1]
            
            # Check password (support both werkzeug and legacy SHA256)
            if check_password_hash(stored_hash, password):
                session['user_id'] = user_id
                session.permanent = True
                
                # Update last login
                db.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
                db.commit()
                
                flash('Selamat datang kembali!', 'success')
                return redirect(url_for('main.dashboard'))
            else:
                # Try legacy SHA256 hash for backwards compatibility
                import hashlib
                legacy_hash = hashlib.sha256(password.encode()).hexdigest()
                if stored_hash == legacy_hash:
                    session['user_id'] = user_id
                    session.permanent = True
                    
                    # Upgrade to werkzeug hash
                    new_hash = generate_password_hash(password)
                    db.execute('UPDATE users SET password = ?, last_login = CURRENT_TIMESTAMP WHERE id = ?', 
                             (new_hash, user_id))
                    db.commit()
                    
                    flash('Selamat datang kembali!', 'success')
                    return redirect(url_for('main.dashboard'))
        
        flash('Login gagal. Periksa username dan password.', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """User logout."""
    session.pop('user_id', None)
    flash('Anda telah keluar.', 'info')
    return redirect(url_for('auth.login'))


def login_required(f):
    """Decorator to require login for a route."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user():
    """Get current logged-in user data."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    db = get_db()
    cur = db.execute('SELECT id, username, email, full_name, avatar_url, preferred_theme FROM users WHERE id = ?', 
                     (user_id,))
    return cur.fetchone()
