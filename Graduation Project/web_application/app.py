import os
import requests
import mariadb
import hashlib
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'


db_config = {
    'host': 'localhost',
    'user': 'analyst',
    'password': 'pass',
    'database': 'malware_analysis'
}


@app.route('/')
def home():
    # fetch recent samples to allow the UI to enable/disable actions
    try:
        conn = mariadb.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM samples ORDER BY id DESC LIMIT 50")
        samples = cursor.fetchall()
    except Exception:
        samples = []
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    return render_template('index.html', samples=samples)


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)

    # compute saved file size and render confirmation page to allow analysis
    file_size = os.path.getsize(filepath)
    return render_template('submit.html', filename=filename, file_size=file_size)


@app.route('/submit', methods=['POST'])
def submit():
    # Handle submission logic here
    filename = request.form['filename']
    file_size = request.form['file_size']
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Send to analysis server
    # files = {
    #     'file': (filename, open(filepath, 'rb'))
    # }
    # response = requests.post('http://localhost:8000/upload', files=files)

    # Calculate hashes

    def calc_hash(file_path, algo):
        hash_func = hashlib.new(algo)
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    hash_md5 = calc_hash(filepath, 'md5')
    hash_sha1 = calc_hash(filepath, 'sha1')
    hash_sha256 = calc_hash(filepath, 'sha256')

    file_size = os.path.getsize(filepath)
    file_type = os.path.splitext(filename)[1].lstrip('.').lower()

    conn = mariadb.connect(**db_config)
    cursor = conn.cursor()

    sql = """
    INSERT INTO samples
    (file_name, hash_md5, hash_sha1, hash_sha256, file_size, file_type)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (filename, hash_md5, hash_sha1, hash_sha256,
              file_size, file_type)
    cursor.execute(sql, values)
    conn.commit()
    # capture inserted id and redirect to its analysis page
    sample_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return redirect(url_for('analysis', sample_id=sample_id))


@app.route('/analysis/<int:sample_id>')
def analysis(sample_id):
    conn = mariadb.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM samples WHERE id = %s"
    cursor.execute(sql, (sample_id,))
    sample = cursor.fetchone()

    cursor.close()
    conn.close()

    if sample:
        return render_template('analysis.html', sample=sample)
    else:
        return 'Sample not found', 404


@app.route("/test")
def test():
    return render_template('base.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
