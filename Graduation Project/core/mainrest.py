import os
import requests
import hashlib
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename


app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'


@app.route('/')
def home():
    return 'core is running'


def upload():
    file_name = 'sample1.zip'
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(file_name))
    filename = secure_filename(file_name)
    # Send to analysis server
    files = {
        'file': (filename, open(filepath, 'rb'))
    }
    response = requests.post('http://localhost:7000/upload', files=files)


if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=6000, debug=True)
    upload()
