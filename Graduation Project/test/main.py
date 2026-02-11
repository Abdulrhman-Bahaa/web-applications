import requests

# List of clients to send
data = {
    "clients": ["LBDpCtraBFIalrAAAAAB", "asdsssCtraBFIalrAAAAAB"]
}

# Send POST request with JSON body
response = requests.post("http://localhost:5001/update_core/", json=data)
