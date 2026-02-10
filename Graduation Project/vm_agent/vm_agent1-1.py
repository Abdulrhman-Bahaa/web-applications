import argparse
import subprocess
import os
import json
import signal
import zipfile
import time
import aiofiles


from fastapi import FastAPI, UploadFile, File, HTTPException,Header,Request
from fastapi.responses import JSONResponse
import uvicorn
from werkzeug.utils import secure_filename

app = FastAPI()

UPLOAD_FOLDER = "uploads"
JSON_FOLDER = r"C:\covid_rat"

HOST = "0.0.0.0"
PORT = 5003

# Create uploads directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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


@app.get("/execute")
async def execute():
    subprocess.Popen(["python", "static.py"])
    return {"result": "main.py started"}


@app.post("/shutdown")
async def shutdown():
    os.kill(os.getpid(), signal.SIGTERM)
    return {"message": "Server shutting down..."}


SEVEN_ZIP = r"C:\Program Files\7-Zip\7z.exe"
UPLOAD_FOLDER = r"C:\covid_rat\uploads"

import os
import subprocess
from fastapi import UploadFile, File, HTTPException
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = r"C:\covid_rat\uploads"
SEVEN_ZIP = r"C:\Program Files\7-Zip\7z.exe"
ZIP_PASSWORD = "infected"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def rename_to_exe(folder):
    """
    Rename the first extracted file that has no extension (or not .exe)
    into .exe and return its full path
    """
    for name in os.listdir(folder):
        full_path = os.path.join(folder, name)

        # skip directories
        if os.path.isdir(full_path):
            continue

        # skip zip files
        if name.lower().endswith(".zip"):
            continue

        base, ext = os.path.splitext(name)

        if ext == "" or ext.lower() != ".exe":
            new_name = base + ".exe"
            new_path = os.path.join(folder, new_name)

            if not os.path.exists(new_path):
                os.rename(full_path, new_path)
                print(f"[+] Renamed: {name} → {new_name}")
                return new_path

    return None

PYTHON_EXE = r"C:\Users\tester\AppData\Local\Programs\Python\Python310\python.exe"

STATIC_PY = r"C:\covid_rat\static.py"
MAIN_PY   = r"C:\covid_rat\Dynamic.py"
RENAME_PY = r"C:\covid_rat\rename.py"


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

    extract_cmd = [
        SEVEN_ZIP,
        "x",
        file_path,
        f"-p{ZIP_PASSWORD}",
        f"-o{UPLOAD_FOLDER}",
        "-y"
    ]

    result = subprocess.run(extract_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Extraction failed")

    exe_path = rename_to_exe(UPLOAD_FOLDER)

    if not exe_path:
        raise HTTPException(status_code=400, detail="No EXE found")
    
    print("[*] Running static analysis...")
    subprocess.run([PYTHON_EXE, STATIC_PY], check=True)

    print("[*] Waiting 2 seconds...")
    time.sleep(2)

    print("[*] Running Dynamic.py...")
    subprocess.run([PYTHON_EXE, MAIN_PY], check=True)

    print("[*] Running rename...")
    subprocess.run([PYTHON_EXE, RENAME_PY], check=True)

    print("[✓] Pipeline finished successfully")


    return {
        "message": "Upload + extraction completed",
        "exe_ready": os.path.basename(exe_path)
    }

    






# ============================
# JSON ENDPOINTS
# ============================

@app.get("/json")
def get_all_json_files():
    if not os.path.exists(JSON_FOLDER):
        raise HTTPException(status_code=404, detail="JSON folder not found")

    results = {}

    for file in os.listdir(JSON_FOLDER):
        if file.endswith(".json"):
            path = os.path.join(JSON_FOLDER, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    results[file] = json.load(f)
            except Exception:
                results[file] = {"error": "Failed to read file"}

    return results


@app.get("/json/{filename}")
def get_json_file(filename: str):

    if not filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files allowed")

    safe_name = os.path.basename(filename)
    filepath = os.path.join(JSON_FOLDER, safe_name)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read JSON")

    return JSONResponse(content=data)


# ============================
# RUN SERVER
# ============================

if __name__ == "__main__":
    print(f"VM Agent server running on port {PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
