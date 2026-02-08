import argparse
import requests
import socketio
from dataclasses import dataclass


@dataclass(frozen=True)
class Services:
    CORE: str = "http://localhost:5002"
    DATA_ACCESS: str = "http://localhost:5001"
    VM_AGENT: str = "http://localhost:5003"


@dataclass(frozen=True)
class Endpoints:
    SAMPLES: str = "/samples/"
    VM_UPLOAD: str = "/upload"


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--core-url",
        default="http://localhost:5002",
        help="Core service URL"
    )
    parser.add_argument(
        "--data-access-url",
        default="http://localhost:5001",
        help="Data access service URL"
    )
    parser.add_argument(
        "--vm-agent-url",
        default="http://localhost:5003",
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

    # Stream file from Data Access Service and upload to VM Agent
    with requests.get(DATA_ACCESS_URL + data, params={"download": 1}, stream=True) as r:
        r.raise_for_status()  # check for errors
        files = {"file": (f"{data}.zip", r.raw)}  # r.raw is a file-like object
        response = requests.post(VM_AGENT_URL, files=files)

        sio.emit("file_processed", {
                 "filename": data, "status": response.status_code})


@sio.event
def disconnect():
    print("Disconnected from server.")


if __name__ == "__main__":
    sio.connect(services.CORE)
    sio.wait()
