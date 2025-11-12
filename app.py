from flask import Flask, request, render_template, redirect, url_for, session, send_file, send_from_directory
import sqlite3, os
import subprocess, tempfile

app = Flask(__name__)
app.secret_key = 'insecure-secret-key' 

DB = 'vuln.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

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
    return render_template('index.html')

@app.route('/notes')
def notes():
    conn = get_db()
    c = conn.cursor()
    msgs = c.execute("SELECT * FROM messages ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('messages.html', messages=msgs)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
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
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO messages (user, content) VALUES ('%s','%s')" % (session['user'], content))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        f = request.files.get('file')
        if not f:
            return "No file"
        
        filename = f.filename
        path = os.path.join(UPLOAD_FOLDER, filename)
        
        f.save(path)
        
        return f"Uploaded and backed up: {filename}"
    
    return render_template('upload.html')

@app.route('/size')
def size():
    filename = request.args.get('file','').strip()
    if not filename:
        return "No file specified"
    
    path = os.path.join(UPLOAD_FOLDER, filename)
    tf = tempfile.NamedTemporaryFile(delete=False)
    tmp = tf.name
    tf.close()
    command = f"stat -c%s {path}"
    print(f"Executing command: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(f"Command output: {result.stdout}, Error: {result.stderr}")
    output = result.stdout
    
    return f"{output}"

@app.route('/download')
def download():
    filename = request.args.get('file','').strip()
    if not filename:
        files = []
        for fn in os.listdir(UPLOAD_FOLDER):
            fp = os.path.join(UPLOAD_FOLDER, fn)
            if os.path.isfile(fp):
                files.append(fn)
        return render_template('download.html', files=files)

    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    else:
        return "File not found: %s" % filename

@app.route('/uploads/<path:filename>')
def uploads_public(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
