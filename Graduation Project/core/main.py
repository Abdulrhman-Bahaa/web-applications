import asyncio
import requests
import socketio
import uvicorn


sio = socketio.AsyncServer(async_mode="asgi")
app = socketio.ASGIApp(sio)

# Data Access URL
DATA_ACCESS_URL = "http://localhost:5001/samples/"
GET_UNANALIZED_SAMPLE_URL = "http://localhost:5001/samples/unanalyzed/first"

current_sample = None

sample_fetcher_task = None


@sio.event
async def connect(sid, environ):
    global sample_fetcher_task
    print("Client connected:", sid)
    if sample_fetcher_task is None:
        sample_fetcher_task = asyncio.create_task(sample_fetcher())


@sio.event
async def file_processed(sid, data):
    global current_sample
    print("Received:", data)

    payload = {
        "static_analysis": True,
        "dynamic_analysis": True
    }

    response = requests.post(
        DATA_ACCESS_URL + current_sample['hash_sha256'] + '/analysis', json=payload)

    if response.status_code == 200:
        print("Sample marked for analysis:", current_sample['hash_sha256'])
        current_sample = None
    else:
        print("Error marking sample for analysis:", response.text)


@sio.event
async def disconnect(sid):
    global sample_fetcher_task
    if sample_fetcher_task is not None:
        sample_fetcher_task.cancel()
        sample_fetcher_task = None
    print("Client disconnected:", sid)


async def sample_fetcher():
    global current_sample
    while True:
        if current_sample is None:
            response = requests.get(GET_UNANALIZED_SAMPLE_URL)

            if response.status_code == 404:
                print(response.json()["detail"])

            else:
                current_sample = response.json()
                await sio.emit("file_sha256", current_sample['hash_sha256'])
        await asyncio.sleep(5)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5002)
