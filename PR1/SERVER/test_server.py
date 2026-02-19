import socket

def start_server(HOST='127.0.0.1', PORT=7777):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Server is listening on {HOST}:{PORT}", flush=True)
        user, addr = s.accept()
        print(f"Connected by {addr}", flush=True)
        user.close()
    except Exception as e:
        print(f"Server failed: {e}", flush=True)

if __name__ == "__main__":
    start_server()
