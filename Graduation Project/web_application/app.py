from dataclasses import Field
import datetime
import os
import json as pyjson
from urllib import response
import requests
from flask import Flask, json, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO
from pydantic import BaseModel, Field


app = Flask(__name__)

DATA_ACCESS_SERVICE_URL = 'http://localhost:5001'
SAMPLES_API_URL = f'{DATA_ACCESS_SERVICE_URL}/samples/'
SAMPLE_UPLOAD_API_URL = f'{DATA_ACCESS_SERVICE_URL}/samples/upload/'


class SampleSchema(BaseModel):
    id: int
    hash_md5: str = Field(..., min_length=32, max_length=32)
    hash_sha1: str = Field(None, min_length=40, max_length=40)
    hash_sha256: str = Field(None, min_length=64, max_length=64)
    file_name: str = Field(..., max_length=255)
    file_size: int
    file_type: str = Field(None, max_length=100)
    upload_date: datetime.datetime
    static_analysis: bool
    dynamic_analysis: bool

    class Config:
        arbitrary_types_allowed = True


@app.route('/')
def home():

    response = requests.get(SAMPLES_API_URL)
    response.raise_for_status()

    samples = [SampleSchema.model_validate(item) for item in response.json()]

    return render_template('index.html', samples=samples)


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']

    filename = secure_filename(file.filename)

    files = {"file": (filename, file.stream, file.content_type)}
    response = requests.post(SAMPLE_UPLOAD_API_URL, files=files)

    return render_template('submit.html', filename=filename)


@app.route('/analysis/<int:sample_id>')
def analysis(sample_id):
    # sample = db.session.get(Sample, sample_id)

    response = requests.get(f'{SAMPLES_API_URL}{sample_id}')
    if response.status_code == 200:
        try:
            sample = SampleSchema.model_validate(response.json())
        except Exception as e:
            print(f"Sample validation error: {e}")
            sample = None
    else:
        sample = None

    print(f"Fetched sample data for sample_id {sample_id}: {sample}")

    if sample:
        # Fetch static and dynamic analysis JSON from the data access service (per-sample)
        static_analysis = None
        dynamic_analysis = None

        sha256 = getattr(sample, 'hash_sha256', None)
        print(
            f"Fetching analysis for sample {sample_id} with SHA256: {sha256}")

        if sha256:
            # Fetch static analysis from API
            try:
                sa_url = f"{DATA_ACCESS_SERVICE_URL}/json/{sha256}_static.json"
                resp = requests.get(sa_url, timeout=5)
                if resp.status_code == 200:
                    static_analysis = resp.json()
                    static_analysis = json.loads(static_analysis["content"])

            except Exception as e:
                print(f"Static analysis fetch error: {e}")
                static_analysis = None

            # Fetch dynamic analysis from API
            try:
                da_url = f"{DATA_ACCESS_SERVICE_URL}/json/{sha256}_dynamic.json"
                resp = requests.get(da_url, timeout=5)
                if resp.status_code == 200:
                    dynamic_analysis = resp.json()
                    dynamic_analysis = json.loads(dynamic_analysis["content"])
            except Exception as e:
                print(f"Dynamic analysis fetch error: {e}")
                dynamic_analysis = None

        return render_template('analysis.html', sample=sample, static_analysis=static_analysis, dynamic_analysis=dynamic_analysis)
    else:
        return 'Sample not found', 404


@app.route('/submit', methods=['POST'])
def submit():

    return redirect(url_for('home'))


@app.route("/settings")
def settings():
    return render_template('settings.html')


@app.route("/history")
def history():
    samples = Sample.query.order_by(Sample.id.desc()).limit(50).all()
    return render_template('history.html', samples=samples)


@app.route('/search', methods=['POST'])
def search():
    search_query = ''
    # Get the value from the form input
    search_query = request.form.get('search', '')

    samples = Sample.query.filter(
        (Sample.file_name.ilike(f"%{search_query}%")) |
        (Sample.hash_md5 == search_query) |
        (Sample.hash_sha1 == search_query) |
        (Sample.hash_sha256 == search_query)
    ).order_by(Sample.id.desc()).limit(50).all()

    return render_template('history.html', samples=samples, search_query=search_query)


if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0', port=5000)
