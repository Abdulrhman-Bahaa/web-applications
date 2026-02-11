import asyncio
from datetime import datetime
import aiohttp
import requests
import socketio
import uvicorn

# Socket.IO server
sio = socketio.AsyncServer(async_mode="asgi")
app = socketio.ASGIApp(sio)

# Data Access URLs
DATA_ACCESS_URL = "http://localhost:5001/"
GET_UNANALIZED_SAMPLE_URL = "http://localhost:5001/samples/unanalyzed/first"

# Global state
current_sample = None
sample_fetcher_task = None
connected_clients = set()


@sio.event
async def connect(sid, environ):
    global sample_fetcher_task

    print(f"Client connected: {sid}")
    connected_clients.add(sid)

    # Start background task once
    if sample_fetcher_task is None:
        sample_fetcher_task = asyncio.create_task(sample_fetcher())


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    connected_clients.discard(sid)
    # Do NOT cancel the background task


@sio.event
async def file_processed(sid, data):
    global current_sample

    print(f"Received from {sid}: {data}")

    if not current_sample:
        return

    payload = {
        "static_analysis": True,
        "dynamic_analysis": True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            DATA_ACCESS_URL + "samples/" +
                current_sample["hash_sha256"] + "/analysis",
            json=payload
        ) as response:

            if response.status == 200:
                print("Sample marked for analysis:",
                      current_sample["hash_sha256"])
                current_sample = None
            else:
                print("Error marking sample for analysis")


async def sample_fetcher():
    global current_sample

    print("Sample fetcher started")

    try:
        async with aiohttp.ClientSession() as session:
            while True:

                # No clients connected → idle
                if not connected_clients:
                    await asyncio.sleep(1)
                    continue

                if current_sample is None:
                    # print current time for debugging
                    print(datetime.now().strftime("%H:%M:%S") +
                          " - Fetching unanalyzed sample...")

                    async with session.get(GET_UNANALIZED_SAMPLE_URL) as response:
                        if response.status == 404:
                            print(datetime.now().strftime("%H:%M:%S") +
                                  " - No unanalyzed samples available")
                            pass
                        elif response.status == 200:
                            print(datetime.now().strftime("%H:%M:%S") +
                                  " - Unanalyzed sample fetched !!!")
                            current_sample = await response.json()
                            await sio.emit(
                                "file_sha256",
                                current_sample["hash_sha256"]
                            )

                await asyncio.sleep(5)

    except asyncio.CancelledError:
        print("Sample fetcher cancelled")
        raise


# Hearbeat task
async def heartbeat():
    while True:
        data = {
            "clients": list(connected_clients)
        }

        try:
            response = requests.post(
                DATA_ACCESS_URL + "update_core/", json=data)
            print(f"Heartbeat sent")
        except requests.RequestException as e:
            print(f"Error sending heartbeat: {e}")

        await asyncio.sleep(5)


if __name__ == "__main__":
    async def main():
        # Start the heartbeat as a background task
        asyncio.create_task(heartbeat())

        print("Starting Socket.IO server on port 5002...")

        # Start the Socket.IO ASGI app with Uvicorn
        config = uvicorn.Config(app, host="0.0.0.0",
                                port=5002, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    # Run the async main function
    asyncio.run(main())
