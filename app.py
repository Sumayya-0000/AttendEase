import os
import sqlite3
from datetime import date, timedelta
from flask import Flask, g, redirect, render_template, request, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-for-production')
DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'attendance.db'))


def get_db():
    if 'db' not in g:
        os.makedirs(os.path.dirname(DATABASE) or '.', exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT NOT NULL UNIQUE,
            course TEXT NOT NULL DEFAULT 'General'
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present','Late','Absent')),
            UNIQUE(student_id, attendance_date),
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
        );
    ''')
    db.commit()


@app.before_request
def ensure_db():
    init_db()


def seed_if_empty():
    db = get_db()
    if db.execute('SELECT COUNT(*) FROM students').fetchone()[0] == 0:
        db.executemany('INSERT INTO students(name, roll_number, course) VALUES (?, ?, ?)', [
            ('Aarav Sharma', 'IT001', 'Information Technology'),
            ('Diya Reddy', 'IT002', 'Information Technology'),
            ('Ishaan Rao', 'IT003', 'Computer Science'),
            ('Meera Patel', 'IT004', 'Computer Science'),
            ('Rohan Kumar', 'IT005', 'Information Technology'),
        ])
        db.commit()


@app.route('/')
def dashboard():
    seed_if_empty()
    db = get_db()
    chosen_date = request.args.get('date', date.today().isoformat())
    counts = {row['status']: row['total'] for row in db.execute(
        'SELECT status, COUNT(*) AS total FROM attendance WHERE attendance_date=? GROUP BY status', (chosen_date,))}
    total = db.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    absent = max(total - sum(counts.values()), 0) + counts.get('Absent', 0)
    low_attendance = db.execute('''
        SELECT s.id, s.name, s.roll_number,
        SUM(CASE WHEN a.status IN ('Present','Late') THEN 1 ELSE 0 END) AS attended,
        COUNT(a.id) AS marked
        FROM students s LEFT JOIN attendance a ON a.student_id=s.id
        GROUP BY s.id HAVING marked > 0
    ''').fetchall()
    low = []
    for row in low_attendance:
        pct = (row['attended'] / row['marked'] * 100) if row['marked'] else 0
        if pct < 75:
            low.append({'name': row['name'], 'roll_number': row['roll_number'], 'percentage': round(pct, 1)})
    return render_template('dashboard.html', chosen_date=chosen_date, total=total,
        present=counts.get('Present', 0), late=counts.get('Late', 0), absent=absent,
        low_attendance=low)


@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    db = get_db()
    chosen_date = request.values.get('date', date.today().isoformat())
    if request.method == 'POST':
        for student in db.execute('SELECT id FROM students').fetchall():
            status = request.form.get(f"status_{student['id']}", 'Absent')
            if status not in ('Present', 'Late', 'Absent'):
                status = 'Absent'
            db.execute('''INSERT INTO attendance(student_id, attendance_date, status) VALUES (?, ?, ?)
                ON CONFLICT(student_id, attendance_date) DO UPDATE SET status=excluded.status''',
                (student['id'], chosen_date, status))
        db.commit()
        flash(f'Attendance saved for {chosen_date}.', 'success')
        return redirect(url_for('attendance', date=chosen_date))
    students = db.execute('''SELECT s.*, a.status FROM students s LEFT JOIN attendance a
        ON a.student_id=s.id AND a.attendance_date=? ORDER BY s.roll_number''', (chosen_date,)).fetchall()
    return render_template('attendance.html', students=students, chosen_date=chosen_date)


@app.route('/students', methods=['GET', 'POST'])
def students_page():
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll = request.form.get('roll_number', '').strip().upper()
        course = request.form.get('course', 'General').strip() or 'General'
        if not name or not roll:
            flash('Name and roll number are required.', 'error')
        else:
            try:
                db.execute('INSERT INTO students(name, roll_number, course) VALUES (?, ?, ?)', (name, roll, course))
                db.commit()
                flash('Student added successfully.', 'success')
            except sqlite3.IntegrityError:
                flash('That roll number already exists.', 'error')
        return redirect(url_for('students_page'))
    students = db.execute('SELECT * FROM students ORDER BY roll_number').fetchall()
    return render_template('students.html', students=students)


@app.route('/students/<int:student_id>/delete', methods=['POST'])
def delete_student(student_id):
    db = get_db()
    db.execute('DELETE FROM attendance WHERE student_id=?', (student_id,))
    db.execute('DELETE FROM students WHERE id=?', (student_id,))
    db.commit()
    flash('Student removed.', 'success')
    return redirect(url_for('students_page'))


@app.route('/report')
def report():
    db = get_db()
    students = db.execute('SELECT * FROM students ORDER BY roll_number').fetchall()
    days = [(date.today() - timedelta(days=i)).isoformat() for i in range(9, -1, -1)]
    records = db.execute('SELECT student_id, attendance_date, status FROM attendance WHERE attendance_date IN (%s)' % ','.join('?' * len(days)), days).fetchall()
    matrix = {(r['student_id'], r['attendance_date']): r['status'] for r in records}
    return render_template('report.html', students=students, days=days, matrix=matrix)


@app.route('/health')
def health():
    return jsonify(status='healthy'), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')), debug=False)
