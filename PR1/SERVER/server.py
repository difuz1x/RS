import socket
import os


import server_logic as server_logic


def start_server(HOST='127.0.0.1', PORT=7777, max_client_amount=1):
    if max_client_amount < 1 or max_client_amount > 10:
        print(f"max_client_amount should be between 1 and 10", flush=True)
        return

    try:
      
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen(max_client_amount)
        print(f"Server is listening on {HOST}:{PORT}", flush=True)
    except Exception as e:
        print(f"Failed to start server: {e}", flush=True)
        return

    while True:
        try:
            user, addr = s.accept()
            print(f"Connected by {addr}", flush=True)
            server_logic.send_file(user, addr)
        except Exception as err:
            print(f"Error with client {addr} : {err}", flush=True)
        finally:
            try:
                user.close()
            except:
                pass


if __name__ == "__main__":
    start_server()
