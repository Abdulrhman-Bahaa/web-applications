from dataclasses import Field
import datetime
import os
import sys
import threading
import PIL.Image  # Change this
from pystray import Icon, Menu, MenuItem
import webbrowser
import requests
from flask import Flask, json, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(base_dir, 'templates'),
    static_folder=os.path.join(base_dir, 'static')
)

DATA_ACCESS_SERVICE_URL = f"http://{os.getenv('DATA_ACCESS_SERVICE_IP')}:{os.getenv('DATA_ACCESS_SERVICE_PORT')}"
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

    try:
        response = requests.get(SAMPLES_API_URL)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching samples: {e}")
        samples = []
    else:
        samples = [SampleSchema.model_validate(item) for item in response.json()]

    # Calculate insights
    last_upload = None
    if samples:
        samples_sorted = sorted(
            samples, key=lambda x: x.upload_date, reverse=True)
        last_upload = samples_sorted[0].upload_date.strftime('%Y-%m-%d %H:%M')

    # Group samples by date for upload timeline
    from collections import defaultdict
    upload_by_date = defaultdict(int)
    for sample in samples:
        date_str = sample.upload_date.strftime('%Y-%m-%d')
        upload_by_date[date_str] += 1

    # Sort by date
    upload_timeline = sorted(upload_by_date.items())

    # Fetch connected clients from data access service
    connected_clients = 0
    core_running = False
    try:
        core_response = requests.get(
            f'{DATA_ACCESS_SERVICE_URL}/core', timeout=5)
        if core_response.status_code == 200:
            core_data = core_response.json()
            if core_data.get('status') != 'failed':

                if core_data.get("clients")[0] == '':
                    connected_clients = 0
                else:
                    connected_clients = len(core_data.get('clients', []))
                core_running = True
            else:
                core_running = False
        else:
            core_running = False
    except Exception as e:
        print(f"Core clients fetch error: {e}")
        core_running = False

    return render_template('index.html', samples=samples, last_upload=last_upload, upload_timeline=upload_timeline, connected_clients=connected_clients, core_running=core_running)


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']

    filename = secure_filename(file.filename)

    files = {"file": (filename, file.stream, file.content_type)}

    try:
        response = requests.post(SAMPLE_UPLOAD_API_URL, files=files)
    except requests.RequestException as e:
        print(f"Error uploading file: {e}")
        return render_template('submit.html', filename=filename, error=True)

    return render_template('submit.html', filename=filename)


@app.route('/analysis/<int:sample_id>')
def analysis(sample_id):

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


@app.route("/history")
def history():

    response = requests.get(SAMPLES_API_URL)
    response.raise_for_status()

    samples = [SampleSchema.model_validate(item) for item in response.json()]

    return render_template('history.html', samples=samples)


@app.route("/admin")
def admin():
    import time
    
    # Get all samples for stats
    total_samples = 0
    last_activity = None
    try:
        response = requests.get(SAMPLES_API_URL, timeout=5)
        if response.status_code == 200:
            samples = response.json()
            total_samples = len(samples)
            if samples:
                samples_sorted = sorted(
                    samples, key=lambda x: x.get('upload_date', ''), reverse=True)
                last_activity = samples_sorted[0].get('upload_date')
    except Exception as e:
        print(f"Error fetching samples for admin: {e}")
    
    # Check Data Access Service status
    data_access_running = False
    data_access_response_time = None
    data_access_status = "Unknown"
    try:
        start_time = time.time()
        response = requests.get(f'{DATA_ACCESS_SERVICE_URL}/samples/', timeout=5)
        data_access_response_time = f"{(time.time() - start_time) * 1000:.2f}ms"
        if response.status_code == 200:
            data_access_running = True
            data_access_status = "Connected"
        else:
            data_access_status = f"HTTP {response.status_code}"
    except requests.Timeout:
        data_access_status = "Timeout"
    except Exception as e:
        data_access_status = str(e)
        print(f"Data access service error: {e}")
    
    # Check Core status
    core_running = False
    connected_clients = 0
    clients = []
    try:
        response = requests.get(f'{DATA_ACCESS_SERVICE_URL}/core', timeout=5)
        if response.status_code == 200:
            core_data = response.json()
            if core_data.get('status') != 'failed':
                core_running = True
                clients_list = core_data.get("clients", [])
                if clients_list and clients_list[0] != '':
                    connected_clients = len(clients_list)
                    clients = clients_list
                else:
                    connected_clients = 0
            else:
                core_running = False
    except Exception as e:
        print(f"Core status fetch error: {e}")
        core_running = False
    
    # Get current timestamp
    last_check_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template('admin.html',
                          total_samples=total_samples,
                          connected_clients=connected_clients,
                          core_running=core_running,
                          data_access_running=data_access_running,
                          data_access_url=DATA_ACCESS_SERVICE_URL,
                          data_access_response_time=data_access_response_time,
                          data_access_status=data_access_status,
                          last_check_time=last_check_time,
                          clients=clients,
                          last_activity=last_activity,
                          uptime="N/A")


@app.route('/search', methods=['POST'])
def search():

    identifier = request.form.get("search")

    response = requests.get(f"{SAMPLES_API_URL}{identifier}")
    if response.status_code == 200:
        try:
            sample = SampleSchema.model_validate(response.json())
        except Exception as e:
            print(f"Sample validation error: {e}")
            sample = None
    else:
        sample = None

    return render_template('history.html', samples=[sample] if sample else [], search_query=identifier)


def quit_app(icon, item):
    icon.stop()
    os._exit(0)  # Ensures the Flask thread kills immediately

def open_dashboard(icon, item):
    webbrowser.open("http://127.0.0.1:5000")

def run_tray():
    # Use PIL.Image.open instead of just Image.open
    icon_path = os.path.join(app.static_folder, 'favicon.png')
    img = PIL.Image.open(icon_path) 
    
    menu = Menu(
        MenuItem('Open Dashboard', open_dashboard),
        MenuItem('Exit', quit_app)
    )
    
    icon = Icon("FlaskService", img, "Malware Analysis UI", menu)
    icon.run()

if __name__ == '__main__':
    # 1. Start Flask in background
    # debug=False is mandatory when using threads/system tray
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()

    # 2. Open browser automatically
    webbrowser.open("http://127.0.0.1:5000")

    # 3. Start System Tray (Main Thread)
    run_tray()
