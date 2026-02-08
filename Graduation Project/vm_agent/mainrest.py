import os
import requests
import hashlib
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

UPLOAD_FOLDER = 'uploads'


@app.get('/')
def home():
    return {"message": "Agent is running"}


@app.post('/upload')
async def upload(file: UploadFile = File(...)):
    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, 'wb') as f:
        f.write(await file.read())
    print(f"Received file: {file.filename}")

    return {"message": "File uploaded successfully"}


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=7000)
