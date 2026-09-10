from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from functools import wraps
import sqlite3
import os
import threading
from datetime import datetime, timedelta
import screener

app = Flask(__name__)
app.secret_key = 'nijubiju_secret_2026'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'screener_results.db')

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'): return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == 'nijubiju123':
            session['logged_in'] = True
            return redirect(url_for('index'))
        return '<h2 style="color:red;text-align:center;margin-top:50px;">Wrong Password</h2><p style="text-align:center;"><a href="/login">Try Again</a></p>'
    return '''<html><body style="background:linear-gradient(135deg,#667eea,#764ba2);height:100vh;display:flex;justify-content:center;align-items:center;font-family:sans-serif;margin:0;">
    <div style="background:white;padding:40px;border-radius:15px;box-shadow:0 10px 25px rgba(0,0,0,0.2);text-align:center;">
    <h2 style="color:#2c3e50;">🔒 HOLY GRAIL ACCESS</h2>
    <form method="post"><input type="password" name="password" placeholder="Password" style="padding:12px;width:200px;border:1px solid #ddd;border-radius:5px;margin-bottom:15px;" required>
    <br><button type="submit" style="padding:12px 30px;background:#667eea;color:white;border:none;border-radius:5px;cursor:pointer;">Unlock</button></form></div></body></html>'''

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/run_scan', methods=['POST'])
@login_required
def run_scan():
    threading.Thread(target=screener.run_screener).start()
    return jsonify({"status": "Scan started! Refresh page in 2 minutes."})

@app.route('/api/data')
@login_required
def get_data():
    conn = get_db()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    c.execute("SELECT COUNT(*) FROM results WHERE scan_date = ?", (today,))
    today_count = c.fetchone()[0]
    
    c.execute("SELECT stock_symbol, stock_price, daily_rsi, scan_time FROM results WHERE scan_date = ? ORDER BY scan_time DESC", (today,))
    today_results = [dict(row) for row in c.fetchall()]
    
    c.execute("SELECT scan_date, COUNT(*) as count FROM results GROUP BY scan_date ORDER BY scan_date DESC LIMIT 10")
    history = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return jsonify({"today_count": today_count, "today_results": today_results, "history": history})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
