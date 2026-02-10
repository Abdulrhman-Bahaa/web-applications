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
VM_AGENT_URL = f"{services.VM_AGENT}"


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


@sio.event
def disconnect():
    print("Disconnected from server.")


if __name__ == "__main__":
    sio.connect(services.CORE)
    sio.wait()
