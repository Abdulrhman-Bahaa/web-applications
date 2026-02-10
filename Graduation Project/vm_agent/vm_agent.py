import argparse
from http.client import HTTPException
import subprocess
import os
from multiprocessing import Process
from fastapi import FastAPI, UploadFile, File, Header, Request
import uvicorn
from dataclasses import dataclass
import aiofiles

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


@app.post("/upload")
async def upload_file(
    request: Request,
    x_filename: str = Header(None),
):
    if not x_filename:
        raise HTTPException(status_code=400, detail="Missing X-Filename header")

    file_path = os.path.join(UPLOAD_FOLDER, x_filename)

    async with aiofiles.open(file_path, "wb") as f:
        async for chunk in request.stream():
            await f.write(chunk)

    return {
        "status": "ok",
        "filename": x_filename,
    }

# Run GUI
if __name__ == "__main__":
    print(f"VM Agent server running on port {PORT}")
    uvicorn.run(app, host=HOST, port=PORT)