import asyncio
import socketio
from aiohttp import web

# Create async Socket.IO server
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

connected_clients = set()


@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    connected_clients.add(sid)
    await sio.emit("message", "Server: Welcome!", to=sid)


@sio.event
async def message(sid, data):
    print(f"Client {sid}: {data}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    connected_clients.discard(sid)


async def server_input_loop():
    """Read server input without blocking asyncio"""
    loop = asyncio.get_running_loop()
    while True:
        msg = await loop.run_in_executor(None, input)
        if msg.lower() == "exit":
            print("Server input exiting...")
            break
        for sid in connected_clients:
            await sio.emit("message", f"Server: {msg}", to=sid)


async def main():
    # Start server input task
    asyncio.create_task(server_input_loop())

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 5000)
    await site.start()

    print("Async Socket.IO server running on http://localhost:5000")

    # Keep server alive forever
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
