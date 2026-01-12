import sys
import subprocess
import os
from multiprocessing import Process
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'


@app.route("/status")
def status():
    return jsonify(status="ready")


@app.route("/execute", methods=["POST"])
def execute():
    data = request.json
    subprocess.Popen(data["path"])
    return jsonify(result="started")


@app.route("/shutdown", methods=["POST"])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)
    print(f"Received file: {file.filename}")

    return "File uploaded successfully"


def run_flask(port):
    app.run(host="0.0.0.0", port=port)
    print(f"Flask server running on port {port}")


class FlaskGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flask Server GUI")

        self.flask_process = None

        # Widgets
        self.label = QLabel("Enter port:")
        self.port_input = QLineEdit()
        self.port_input.setText("8000")  # default port
        self.start_button = QPushButton("Start Server")
        self.stop_button = QPushButton("Stop Server")
        self.status_label = QLabel("Server not running")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.port_input)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        # Button click
        self.start_button.clicked.connect(self.start_server)
        self.stop_button.clicked.connect(self.stop_server)

    def start_server(self):
        port_text = self.port_input.text()
        if not port_text.isdigit():
            self.status_label.setText("Invalid port!")
            return

        port = int(port_text)
        self.status_label.setText(f"Starting server on port {port}...")

        # Run Flask in a separate process
        self.flask_process = Process(target=run_flask, args=(port,))
        self.flask_process.start()
        self.status_label.setText(f"Server running on port {port}")

    def stop_server(self):
        if self.flask_process is not None:
            self.flask_process.terminate()
            self.status_label.setText("Server stopped")


# Run GUI
if __name__ == "__main__":
    app_gui = QApplication(sys.argv)
    window = FlaskGUI()
    window.show()
    sys.exit(app_gui.exec())
