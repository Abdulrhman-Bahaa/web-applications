import argparse
import requests
import socketio
from dataclasses import dataclass
import time
import io
import json
import hashlib


@dataclass(frozen=True)
class Services:
    CORE: str = "http://45.243.251.70:5002"
    DATA_ACCESS: str = "http://45.243.251.70:5001"
    VM_AGENT: str = "http://192.168.40.128:5003"


@dataclass(frozen=True)
class Endpoints:
    SAMPLES: str = "/samples/"
    VM_UPLOAD: str = "/upload"
    JSON: str = "/json/"
    REPORT: str = "/report/"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-url", default=services.CORE,
                        help="Core service URL")
    parser.add_argument(
        "--data-access-url", default=services.DATA_ACCESS, help="Data access service URL")
    parser.add_argument(
        "--vm-agent-url", default=services.VM_AGENT, help="VM agent service URL")
    return parser.parse_args()


def build_services():
    args = parse_args()
    return Services(
        CORE=args.core_url,
        DATA_ACCESS=args.data_access_url,
        VM_AGENT=args.vm_agent_url,
    )


services = build_services()
DATA_ACCESS_URL = f"{services.DATA_ACCESS}{Endpoints.SAMPLES}"
VM_AGENT_UPLOAD_URL = f"{services.VM_AGENT}{Endpoints.VM_UPLOAD}"

sio = socketio.Client()


def calculate_sha256_bytes(data_bytes: bytes) -> str:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data_bytes)
    return sha256_hash.hexdigest()


@sio.event
def connect():
    print("Connected to Core server!")


@sio.event
def file_sha256(data):
    print(f"\n[+] Processing file: {data}\n")

    # --- Step 1: Download ZIP from Data Access and upload to VM Agent ---
    try:
        with requests.get(
            DATA_ACCESS_URL + data,
            params={"download": 1},
            stream=True,
            timeout=60
        ) as r:
            r.raise_for_status()

            def stream():
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        yield chunk

            headers = {"Content-Type": "application/zip",
                       "X-Filename": f"{data}.zip"}

            response = requests.post(
                VM_AGENT_UPLOAD_URL,
                data=stream(),
                headers=headers,
                timeout=300
            )
            response.raise_for_status()
            print(
                f"[+] Uploaded {data}.zip to VM Agent: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"[-] Failed to send ZIP to VM Agent: {e}")
        return

    sio.emit("file_sent_to_vm_agent", {
             "filename": data, "status": response.status_code})

    # --- Optional wait before retrieving analysis ---
    time.sleep(10)

    # --- Step 2: Fetch JSON and TXT reports from VM Agent and verify hashes ---
    file_types = ["_static", "_dynamic", "_network"]
    json_ext = ".json"
    txt_ext = ".txt"

    for ft in file_types:
        for ext in [json_ext, txt_ext]:
            filename = f"{data}{ft}{ext}"
            endpoint = Endpoints.JSON if ext == ".json" else Endpoints.REPORT
            url = f"{services.VM_AGENT}{endpoint}{filename}"

            try:
                r = requests.get(url, timeout=30)
                r.raise_for_status()

                if ext == ".json":
                    vm_response = r.json()
                    file_content_bytes = json.dumps(
                        vm_response.get("data")).encode("utf-8")
                    vm_hash = vm_response.get("hash")
                else:
                    file_content_bytes = r.content
                    # VM Agent sets this header for TXT
                    vm_hash = r.headers.get("X-File-Hash")

                # Verify hash
                computed_hash = calculate_sha256_bytes(file_content_bytes)
                if vm_hash and computed_hash != vm_hash:
                    print(
                        f"[!] Hash mismatch for {filename}: VM={vm_hash}, Computed={computed_hash}")
                    continue  # skip uploading if hash mismatch

                files = {"file": (filename, io.BytesIO(
                    file_content_bytes), "application/octet-stream")}
                upload_response = requests.post(
                    f"{services.DATA_ACCESS}/upload", files=files, timeout=30)
                upload_response.raise_for_status()

                print(f"[+] {filename} uploaded successfully to Data Access.")
                print("Server response:", upload_response.text)

            except requests.exceptions.RequestException as e:
                print(f"[-] Failed to fetch or upload {filename}: {e}")


@sio.event
def disconnect():
    print("Disconnected from Core server.")


if __name__ == "__main__":
    sio.connect(services.CORE)
    sio.wait()
