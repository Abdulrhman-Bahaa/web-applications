import os
import requests
import hashlib
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from models import db, Samples


app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://analyst:pass@localhost:3306/malware_analysis'
# optional, avoids warnings
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

# Create tables if they don't exist
with app.app_context():
    db.create_all()


@app.route('/')
def home():
    try:
        # Fetch the 50 most recent samples, ordered by id descending
        samples = Samples.query.order_by(Samples.id.desc()).limit(50).all()
    except Exception as e:
        print(f"Error fetching samples: {e}")
        samples = []

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


@app.route('/analysis/<int:sample_id>')
def analysis(sample_id):
    sample = db.session.get(Samples, sample_id)

    if sample:
        return render_template('analysis.html', sample=sample)
    else:
        return 'Sample not found', 404


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

    new_sample = Samples(
        file_name=filename,
        hash_md5=hash_md5,
        hash_sha1=hash_sha1,
        hash_sha256=hash_sha256,
        file_size=file_size,
        file_type=file_type
    )

    db.session.add(new_sample)
    db.session.commit()

    return redirect(url_for('analysis', sample_id=new_sample.id))


@app.route("/settings")
def settings():
    return render_template('settings.html')


@app.route("/history")
def history():
    samples = Samples.query.order_by(Samples.id.desc()).limit(50).all()
    return render_template('history.html', samples=samples)


@app.route('/search', methods=['POST'])
def search():
    search_query = ''
    # Get the value from the form input
    search_query = request.form.get('search', '')

    samples = Samples.query.filter(
        (Samples.file_name.ilike(f"%{search_query}%")) |
        (Samples.hash_md5 == search_query) |
        (Samples.hash_sha1 == search_query) |
        (Samples.hash_sha256 == search_query)
    ).order_by(Samples.id.desc()).limit(50).all()

    return render_template('history.html', samples=samples, search_query=search_query)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
