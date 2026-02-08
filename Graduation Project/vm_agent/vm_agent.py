import argparse
import subprocess
import os
from multiprocessing import Process
from fastapi import FastAPI, UploadFile, File
import uvicorn
from dataclasses import dataclass

app = FastAPI()

UPLOAD_FOLDER = 'uploads'

HOST = "0.0.0.0"
PORT = 5003


# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--host",
        default=HOST,
        help="Host for the FastAPI server"
    )
    parser.add_argument(
        "--port",
        type=int,        
        default=PORT,
        help="Port for the FastAPI server"
    )

    return parser.parse_args()

args = parse_args()
HOST = args.host
PORT = args.port

@app.get("/status")
def status():
    return {"status": "ready"}


@app.post("/execute")
async def execute(data: dict):
    subprocess.Popen(data["path"])
    return {"result": "started"}


@app.post("/shutdown")
async def shutdown():
    import signal
    os.kill(os.getpid(), signal.SIGTERM)
    return {"message": "Server shutting down..."}


@app.post('/upload')
async def upload(file: UploadFile = File(...)):
    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, 'wb') as f:
        f.write(await file.read())
    print(f"Received file: {file.filename}")

    return {"message": "File uploaded successfully"}

# Run GUI
if __name__ == "__main__":
    print(f"VM Agent server running on port {PORT}")
    uvicorn.run(app, host=HOST, port=PORT)