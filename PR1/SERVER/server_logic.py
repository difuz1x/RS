import os
import socket


def find_filename(file_name):

    if not file_name.strip():
        return None

    SHARED_DIR="SHARED"

    safe_filename = os.path.basename(file_name)

    for root, dirs, files in os.walk(SHARED_DIR):
        if safe_filename in files:
            full_path = os.path.join(root, safe_filename)
            if os.path.isfile(full_path):
                print(f"File {safe_filename} was found at {full_path}")
                return full_path

    print(f"File {safe_filename} was not found")
    return None

def recv_name (user: socket.socket):
    recv_buffer = b""
    while b"\n" not in recv_buffer:
        chunk=user.recv(1)
        if not chunk :
            break
        recv_buffer += chunk
    return recv_buffer.decode().strip()


def send_file(user: socket.socket, addr: tuple, CHUNK_SIZE: int = 4096):
    file_name = None
    try:
     while True:

        file_name = recv_name(user).strip()
        if not file_name:
            print(f"Client {addr} disconected")
            break


        file_path = find_filename(file_name)

        if not file_path:
            err_header = f"ERR|{file_name}|0|0\n".encode("utf-8")
            user.sendall(err_header)
            continue

        file_size = os.path.getsize(file_path)
        print(f"received filename {file_name} from client {addr}, file size is {file_size}")

        header = f"OK|{file_name}|{file_size}|{CHUNK_SIZE}\n".encode("utf-8")
        user.sendall(header)

        with open(file_path, "rb") as file:
            while True:
                chunk = file.read(CHUNK_SIZE)
                if not chunk:
                    break
                user.sendall(chunk)

        print(f"Sending file to {addr} is completed")

    except Exception as e:
        print(f"Error while sending file to {addr}: {e}")

    finally:
        print(f"Work with client {addr} ended succsessfuly ")

                