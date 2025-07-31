from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime, timedelta
import os
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')  # Use env variable
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Session timeout

# Database configuration
DATABASE = 'parking_app.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables, admin user, and sample parking lots"""
    conn = get_db_connection()
    
    # Create tables
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS parking_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prime_location_name TEXT NOT NULL,
            price REAL NOT NULL,
            address TEXT NOT NULL,
            pin_code TEXT NOT NULL,
            maximum_number_of_spots INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS parking_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER NOT NULL,
            spot_number INTEGER NOT NULL,
            status TEXT DEFAULT 'A',  -- A: Available, O: Occupied
            FOREIGN KEY (lot_id) REFERENCES parking_lots (id),
            UNIQUE(lot_id, spot_number)
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            parking_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            leaving_timestamp TIMESTAMP,
            parking_cost REAL,
            status TEXT DEFAULT 'active',  -- active, completed
            FOREIGN KEY (spot_id) REFERENCES parking_spots (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create admin user if not exists
    admin_exists = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin_exists:
        admin_password = generate_password_hash('admin123')
        conn.execute('INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)',
                     ('admin', admin_password, 'admin@parking.com', 1))
    
    # Add sample parking lots if none exist
    lots_exist = conn.execute('SELECT id FROM parking_lots').fetchone()
    if not lots_exist:
        lots = [
            ('City Mall', 25.0, '123 Main St', '123456', 10),
            ('Shopping Center', 20.0, '456 Oak Ave', '654321', 15),
            ('Office Complex', 30.0, '789 Pine Rd', '789012', 8)
        ]
        for name, price, address, pin_code, max_spots in lots:
            cursor = conn.execute('INSERT INTO parking_lots (prime_location_name, price, address, pin_code, maximum_number_of_spots) VALUES (?, ?, ?, ?, ?)',
                                 (name, price, address, pin_code, max_spots))
            lot_id = cursor.lastrowid
            for i in range(1, max_spots + 1):
                conn.execute('INSERT INTO parking_spots (lot_id, spot_number) VALUES (?, ?)',
                             (lot_id, i))
    
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            session.permanent = True  # Enable session timeout
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard' if user['is_admin'] else 'user_dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        
        # Validate inputs
        if not re.match(r'^[a-zA-Z0-9]{3,20}$', username):
            flash('Username must be 3-20 characters, letters and numbers only!', 'danger')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'danger')
            return render_template('register.html')
        if phone and not re.match(r'^\d{10}$', phone):
            flash('Phone number must be a 10-digit number!', 'danger')
            return render_template('register.html')
        
        conn = get_db_connection()
        existing_user = conn.execute('SELECT id FROM users WHERE username = ? OR email = ?', 
                                    (username, email)).fetchone()
        if existing_user:
            flash('Username or email already exists!', 'danger')
            conn.close()
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)',
                     (username, hashed_password, email, phone))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Admin access required!', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    lots = conn.execute('''
        SELECT pl.*, 
               COUNT(ps.id) as total_spots,
               SUM(CASE WHEN ps.status = 'A' THEN 1 ELSE 0 END) as available_spots,
               SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) as occupied_spots
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        GROUP BY pl.id
    ''').fetchall()
    
    total_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = 0').fetchone()['count']
    active_reservations = conn.execute('SELECT COUNT(*) as count FROM reservations WHERE status = "active"').fetchone()['count']
    
    conn.close()
    return render_template('admin_dashboard.html', 
                          lots=lots, 
                          total_users=total_users, 
                          active_reservations=active_reservations)

@app.route('/user_dashboard')
def user_dashboard():
    if not session.get('user_id') or session.get('is_admin'):
        flash('Please log in as a user!', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get available parking lots
    lots = conn.execute('''
        SELECT pl.*, 
               COUNT(ps.id) as total_spots,
               SUM(CASE WHEN ps.status = 'A' THEN 1 ELSE 0 END) as available_spots
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        GROUP BY pl.id
        HAVING available_spots > 0
    ''').fetchall()
    
    # Get user's current reservations
    reservations = conn.execute('''
        SELECT r.*, ps.spot_number, pl.prime_location_name, pl.price
        FROM reservations r
        JOIN parking_spots ps ON r.spot_id = ps.id
        JOIN parking_lots pl ON ps.lot_id = pl.id
        WHERE r.user_id = ? AND r.status = 'active'
    ''', (session['user_id'],)).fetchall()
    
    # Get user's parking history with duration
    history = conn.execute('''
        SELECT r.*, ps.spot_number, pl.prime_location_name, pl.price,
               (julianday(r.leaving_timestamp) - julianday(r.parking_timestamp)) * 24 AS duration_hours
        FROM reservations r
        JOIN parking_spots ps ON r.spot_id = ps.id
        JOIN parking_lots pl ON ps.lot_id = pl.id
        WHERE r.user_id = ? AND r.status = 'completed'
        ORDER BY r.leaving_timestamp DESC
        LIMIT 10
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    return render_template('user_dashboard.html', lots=lots, reservations=reservations, history=history)
@app.route('/create_lot', methods=['GET', 'POST'])
def create_lot():
    if not session.get('is_admin'):
        flash('Admin access required!', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        address = request.form['address']
        pin_code = request.form['pin_code']
        max_spots = int(request.form['max_spots'])
        
        if price <= 0 or max_spots <= 0:
            flash('Price and number of spots must be positive!', 'danger')
            return render_template('create_lot.html')
        
        conn = get_db_connection()
        cursor = conn.execute('INSERT INTO parking_lots (prime_location_name, price, address, pin_code, maximum_number_of_spots) VALUES (?, ?, ?, ?, ?)',
                             (name, price, address, pin_code, max_spots))
        lot_id = cursor.lastrowid
        
        for i in range(1, max_spots + 1):
            conn.execute('INSERT INTO parking_spots (lot_id, spot_number) VALUES (?, ?)',
                         (lot_id, i))
        
        conn.commit()
        conn.close()
        flash('Parking lot created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('create_lot.html')

@app.route('/book_spot/<int:lot_id>')
def book_spot(lot_id):
    if not session.get('user_id') or session.get('is_admin'):
        flash('Please log in as a user!', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('BEGIN EXCLUSIVE')  # Prevent race conditions
    
    spot = conn.execute('''
        SELECT * FROM parking_spots 
        WHERE lot_id = ? AND status = 'A' 
        ORDER BY spot_number LIMIT 1
    ''', (lot_id,)).fetchone()
    
    if not spot:
        conn.rollback()
        conn.close()
        flash('No available spots in this parking lot!', 'danger')
        return redirect(url_for('user_dashboard'))
    
    conn.execute('UPDATE parking_spots SET status = "O" WHERE id = ?', (spot['id'],))
    conn.execute('INSERT INTO reservations (spot_id, user_id) VALUES (?, ?)',
                 (spot['id'], session['user_id']))
    
    conn.commit()
    conn.close()
    flash(f'Successfully booked spot #{spot["spot_number"]}!', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/release_spot/<int:reservation_id>')
def release_spot(reservation_id):
    if not session.get('user_id'):
        flash('Please log in!', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    reservation = conn.execute('''
        SELECT r.*, ps.id as spot_id, pl.price
        FROM reservations r
        JOIN parking_spots ps ON r.spot_id = ps.id
        JOIN parking_lots pl ON ps.lot_id = pl.id
        WHERE r.id = ? AND r.user_id = ? AND r.status = 'active'
    ''', (reservation_id, session['user_id'])).fetchone()
    
    if not reservation:
        conn.close()
        flash('Reservation not found or already completed!', 'danger')
        return redirect(url_for('user_dashboard'))
    
    parking_time = datetime.now() - datetime.fromisoformat(reservation['parking_timestamp'])
    hours = max(1, int(parking_time.total_seconds() / 3600))  # Minimum 1 hour
    cost = hours * reservation['price']
    
    conn.execute('''
        UPDATE reservations 
        SET leaving_timestamp = CURRENT_TIMESTAMP, parking_cost = ?, status = 'completed'
        WHERE id = ?
    ''', (cost, reservation_id))
    
    conn.execute('UPDATE parking_spots SET status = "A" WHERE id = ?', (reservation['spot_id'],))
    
    conn.commit()
    conn.close()
    flash(f'Spot released successfully! Total cost: ₹{cost:.2f}', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/api/reservations')
def api_reservations():
    if not session.get('user_id') or session.get('is_admin'):
        return jsonify([]), 401
    conn = get_db_connection()
    reservations = conn.execute('''
        SELECT r.*, ps.spot_number, pl.prime_location_name, pl.price
        FROM reservations r
        JOIN parking_spots ps ON r.spot_id = ps.id
        JOIN parking_lots pl ON ps.lot_id = pl.id
        WHERE r.user_id = ? AND r.status = 'active'
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return jsonify([dict(res) for res in reservations])

@app.route('/api/lots')
def api_lots():
    conn = get_db_connection()
    lots = conn.execute('''
        SELECT pl.*, 
               COUNT(ps.id) as total_spots,
               SUM(CASE WHEN ps.status = 'A' THEN 1 ELSE 0 END) as available_spots
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        GROUP BY pl.id
    ''').fetchall()
    conn.close()
    return jsonify([dict(lot) for lot in lots])

if __name__ == '__main__':
    init_db()
    app.run(debug=True)