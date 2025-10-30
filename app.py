from flask import Flask, request, render_template, redirect, url_for, session, send_file, send_from_directory
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'insecure-secret-key'  # intentionally insecure

DB = 'vuln.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize DB (simple)
def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    password TEXT,
                    role TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT,
                    content TEXT
                )""")
    # predictable default user (insecure auth)
    c.execute("INSERT OR IGNORE INTO users (id, username, password, role) VALUES (1, 'admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db()
    c = conn.cursor()
    msgs = c.execute("SELECT * FROM messages ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('index.html', messages=msgs)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        # NO validation or hashing -> insecure authentication
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, role) VALUES ('%s','%s','user')" % (u, p))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u = request.form.get('username')
        p = request.form.get('password')
        # SQL injection vulnerability: query built by string concatenation
        conn = get_db()
        c = conn.cursor()
        q = "SELECT * FROM users WHERE username = '%s' AND password = '%s'" % (u, p)
        row = c.execute(q).fetchone()
        conn.close()
        if row:
            session['user'] = row['username']
            session['role'] = row['role']
            return redirect(url_for('index'))
        else:
            return "Login failed"
    return render_template('login.html')

@app.route('/post', methods=['POST'])
def post():
    if 'user' not in session:
        return redirect(url_for('login'))
    content = request.form.get('content')
    # Stored XSS: content stored and later rendered without escaping
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO messages (user, content) VALUES ('%s','%s')" % (session['user'], content))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/search')
def search():
    # Reflected XSS example: parameter is reflected in the page without proper escaping
    q = request.args.get('q','')
    results = []
    if q:
        conn = get_db()
        c = conn.cursor()
        # SQL injection vulnerability (search)
        sql = "SELECT username FROM users WHERE username LIKE '%%%s%%'" % (q)
        for r in c.execute(sql):
            results.append(r['username'])
        conn.close()
    return render_template('search.html', q=q, results=results)

@app.route('/logout')
def logout():
    # Cierra la sesión del usuario y redirige a la página principal
    session.pop('user', None)
    session.pop('role', None)
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method=='POST':
        f = request.files.get('file')
        if not f:
            return "No file"
        # insecure file handling: we use the filename directly (and also secure it but still permit dangerous content)
        filename = secure_filename(f.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        f.save(path)
        return "Uploaded: %s" % filename
    return render_template('upload.html')

@app.route('/download')
def download():
    filename = request.args.get('file','').strip()
    # Si no hay fichero solicitado, devuelve el formulario (download.html)
    if not filename:
        return render_template('download.html')
    # comportamiento existente (intencionadamente vulnerable)
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    else:
        return "File not found: %s" % filename

@app.route('/uploads/<path:filename>')
def uploads_public(filename):
    # Sirve archivos desde UPLOAD_FOLDER sin autenticación
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
