import argparse
import requests
import socketio
from dataclasses import dataclass
import time
import io
import json


@dataclass(frozen=True)
class Services:
    CORE: str = "http://45.243.251.70:5002"
    DATA_ACCESS: str = "http://45.243.251.70:5001"
    VM_AGENT: str = "http://192.168.40.128:5003/"


@dataclass(frozen=True)
class Endpoints:
    SAMPLES: str = "/samples/"
    VM_UPLOAD: str = "/upload"


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--core-url",
        default="http://45.243.251.70:5002",
        help="Core service URL"
    )
    parser.add_argument(
        "--data-access-url",
        default="http://45.243.251.70:5001",
        help="Data access service URL"
    )
    parser.add_argument(
        "--vm-agent-url",
        default="http://192.168.40.128:5003",
        help="VM agent service URL"
    )

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
VM_AGENT_URL = f"{services.VM_AGENT}{Endpoints.VM_UPLOAD}"

sio = socketio.Client()


@sio.event
def connect():
    print("Connected to server!")


@sio.event
def file_sha256(data):
    print(f"\n{data}\n")

    with requests.get(
        DATA_ACCESS_URL + data,
        params={"download": 1},
        stream=True,
        timeout=60,
    ) as r:
        r.raise_for_status()

        def stream():
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    yield chunk

        headers = {
            "Content-Type": "application/zip",
            "X-Filename": f"{data}.zip",
        }

        response = requests.post(
            f"{services.VM_AGENT}{Endpoints.VM_UPLOAD}",
            data=stream(),
            headers=headers,
            timeout=300,
        )

    sio.emit(
        "file_processed",
        {
            "filename": data,
            "status": response.status_code,
        },
    )


    # --- Optional wait before processing JSON ---
    time.sleep(10)  # adjust wait if needed

    # --- Step 2: Get JSON from local VM Agent and send it to Data Access Service as a file ---
    # --- Step 2: Get JSON files from VM Agent and send them to Data Access Service ---
    try:
        json_files = [
            f"{data}_static.json",
            f"{data}_dynamic.json",
        ]

        for json_name in json_files:
            vm_json_url = f"{services.VM_AGENT}/json/{json_name}"
            response = requests.get(vm_json_url, timeout=30)
            response.raise_for_status()
            json_data = response.json()
            print(f"[+] Fetched {json_name} from VM Agent.")

            # Convert JSON to file-like object
            json_file = io.StringIO(json.dumps(json_data))
            files = {"file": (json_name, json_file, "application/json")}

            # Upload to Data Access
            upload_response = requests.post(
                f"{services.DATA_ACCESS}/upload",
                files=files,
                timeout=30,
            )
            upload_response.raise_for_status()

            print(f"[+] {json_name} uploaded successfully to Data Access.")
            print("Server response:", upload_response.text)

    except requests.exceptions.RequestException as e:
        print("[-] JSON transfer failed:", e)


@sio.event
def disconnect():
    print("Disconnected from server.")


if __name__ == "__main__":
    sio.connect(services.CORE)
    sio.wait()
