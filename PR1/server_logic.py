import os
import socket


def find_filename(file_name):
    if not file_name.strip():
        return None
    safe_filename = os.path.basename(file_name)
    for root, dirs, files in os.walk('.'):
        if safe_filename in files:
            full_path = os.path.join(root,safe_filename)
            if os.path.isfile(full_path):
                print(f"File {safe_filename} was found at {full_path}")
                return full_path
    print(f"File {safe_filename} was not found in the current directory or its subdirectories")
    return None
        

def send_file (user: socket.socket, addr: tuple,  CHUNK_SIZE: int=4096):
   while True :
        data = user.recv(1024)
        if not data: break
        else :

            file_name = data.decode().strip()
            file_path = find_filename(file_name)

            if file_path:

                file_size = os.path.getsize(file_path)
                print(f"received filename {file_name} from client {addr}, file size is {file_size}")

                hello_header = f"OK|{file_name}|{file_size}|{CHUNK_SIZE}|".encode('utf-8')

                user.sendall(hello_header)

                with open(file_path, 'rb') as file:
                   while chunk:= file.read(CHUNK_SIZE):
                      user.sendall(chunk)
                print(f'Sending file to {addr} is completed')
            else : 
                err_header =f"ERR!|{file_name}|0|0|".encode('utf-8')
                user.sendall(err_header)
                