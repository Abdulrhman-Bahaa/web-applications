import hashlib
import subprocess
import os
import json
import time
import aiofiles
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse, FileResponse
import pyzipper
import uvicorn


UPLOAD_FOLDER = r"C:\covid_rat\uploads"
OUTPUT_FOLDER = r"C:\covid_rat"
ZIP_PASSWORD = "infected"
PYTHON_EXE = r"C:\Users\tester\AppData\Local\Programs\Python\Python310\python.exe"
STATIC_PY = r"C:\covid_rat\static.py"
MAIN_PY = r"C:\covid_rat\main.py"
RENAME_PY = r"C:\covid_rat\rename.py"
HOST = "0.0.0.0"
PORT = 5003

# Store the hashes of the reports to prevent duplicates
json_hashes = {}  # key: filename, value: hash
report_hashes = {}  # key: filename, value: hash

# Create uploads directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = FastAPI()


def calculate_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    # Read the file in chunks to handle large files efficiently
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


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


@app.post("/upload")
async def upload_file(
    request: Request,
    x_filename: str = Header(None),
):
    if not x_filename:
        raise HTTPException(
            status_code=400, detail="Missing X-Filename header")

    file_path = os.path.join(UPLOAD_FOLDER, x_filename)

    async with aiofiles.open(file_path, "wb") as f:
        async for chunk in request.stream():
            await f.write(chunk)

    # Extract the AES-encrypted ZIP
    try:
        with pyzipper.AESZipFile(file_path, 'r') as zipf:
            zipf.setpassword(ZIP_PASSWORD.encode())
            zipf.extractall(path=UPLOAD_FOLDER)
    except (pyzipper.BadZipFile, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")

    exe_path = rename_to_exe(UPLOAD_FOLDER)

    if not exe_path:
        raise HTTPException(status_code=400, detail="No EXE found")

    print("[*] Running static analysis...")
    subprocess.run([PYTHON_EXE, STATIC_PY], check=True)

    # Store the hash of "Sha256_static.json", "analysis_report_static.txt", to ensure integrity
    static_json_path = os.path.join(OUTPUT_FOLDER, "Sha256_static.json")
    static_txt_path = os.path.join(OUTPUT_FOLDER, "analysis_report_static.txt")
    if os.path.exists(static_json_path):
        static_hash = calculate_sha256(static_json_path)
        json_hashes["_static.json"] = static_hash
        print(f"[+] Stored hash of Sha256_static.json: {static_hash}")

    if os.path.exists(static_txt_path):
        static_txt_hash = calculate_sha256(static_txt_path)
        report_hashes["static.txt"] = static_txt_hash
        print(
            f"[+] Stored hash of analysis_report_static.txt: {static_txt_hash}")

    print("[*] Waiting 2 seconds...")
    time.sleep(2)

    print("[*] Running main.py...")
    subprocess.run([PYTHON_EXE, MAIN_PY], check=True)

    # Store the hash of Sha256_dynamic.json, analysis_report.txt, sha256_net.json, analysis_report_network.txt
    #  file, to ensure integrity
    dynamic_json_path = os.path.join(OUTPUT_FOLDER, "Sha256_dynamic.json")
    dynamic_txt_path = os.path.join(OUTPUT_FOLDER, "analysis_report.txt")
    network_json_path = os.path.join(OUTPUT_FOLDER, "sha256_net.json")
    network_txt_path = os.path.join(
        OUTPUT_FOLDER, "analysis_report_network.txt")

    if os.path.exists(dynamic_json_path):
        dynamic_hash = calculate_sha256(dynamic_json_path)
        json_hashes["_dynamic.json"] = dynamic_hash
        print(f"[+] Stored hash of _dynamic.json: {dynamic_hash}")

    if os.path.exists(dynamic_txt_path):
        dynamic_txt_hash = calculate_sha256(dynamic_txt_path)
        report_hashes["_dynamic.txt"] = dynamic_txt_hash
        print(f"[+] Stored hash of _dynamic.txt: {dynamic_txt_hash}")

    if os.path.exists(network_json_path):
        network_hash = calculate_sha256(network_json_path)
        json_hashes["_network.json"] = network_hash
        print(f"[+] Stored hash of _network.json: {network_hash}")

    if os.path.exists(network_txt_path):
        network_txt_hash = calculate_sha256(network_txt_path)
        report_hashes["_network.txt"] = network_txt_hash
        print(
            f"[+] Stored hash of _network.txt: {network_txt_hash}")

    print("[*] Running rename...")
    subprocess.run([PYTHON_EXE, RENAME_PY], check=True)

    print("[✓] Pipeline finished successfully")

    return {
        "message": "Upload + extraction completed + analysis completed",
    }


@app.get("/json/{filename}")
def get_json_file(filename: str):

    if not filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files allowed")

    safe_name = os.path.basename(filename)
    filepath = os.path.join(OUTPUT_FOLDER, safe_name)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read JSON")

    # Return the JSON content directly in the response, and the hash is stored in the json_hashes set for integrity verification

    # Find the hash of the requested file in json_hashes set
    # check if the filename ends with _static.json
    file_hash = None
    if filename.endswith("_static.json"):
        hash = json_hashes["_static.json"] if "_static.json" in json_hashes else None
    elif filename.endswith("_dynamic.json"):
        hash = json_hashes["_dynamic.json"] if "_dynamic.json" in json_hashes else None
    elif filename.endswith("_network.json"):
        hash = json_hashes["_network.json"] if "_network.json" in json_hashes else None
    else:
        hash = None

    # Return the JSON content along with the hash in the response
    return JSONResponse(content={"data": data, "hash": hash})


@app.get("/report/{filename}")
def get_report_file(filename: str):
    # Ensure filename is safe
    safe_name = os.path.basename(filename)
    filepath = os.path.join(OUTPUT_FOLDER, safe_name)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    # Find the hash of the requested file in report_hashes set
    # check if the filename ends with _static.json
    file_hash = None
    if filename.endswith("_static.txt"):
        hash = report_hashes["_static.txt"] if "_static.txt" in report_hashes else None
    elif filename.endswith("_dynamic.txt"):
        hash = report_hashes["_dynamic.txt"] if "_dynamic.txt" in report_hashes else None
    elif filename.endswith("_network.txt"):
        hash = report_hashes["_network.txt"] if "_network.txt" in report_hashes else None
    else:
        hash = None    # Return the file as a downloadable response

    return FileResponse(
        path=filepath,
        filename=safe_name,  # suggested download name
        headers={"X-File-Hash": hash} if hash else None,
        media_type="application/octet-stream"  # generic binary type
    )


# ============================
# RUN SERVER
# ============================
if __name__ == "__main__":
    print(f"VM Agent server running on port {PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
