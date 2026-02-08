import socketio
import threading

sio = socketio.Client()


@sio.event
def connect():
    print("Connected to server!")


@sio.event
def message(data):
    print(f"\n{data}\nYou: ", end="", flush=True)


@sio.event
def disconnect():
    print("Disconnected from server.")


def input_loop():
    while True:
        msg = input("You: ")
        if msg.lower() == "exit":
            break
        sio.send(msg)
    sio.disconnect()


if __name__ == "__main__":
    sio.connect("http://localhost:5000")
    threading.Thread(target=input_loop, daemon=True).start()
    sio.wait()
