import socket
import os
import threading
import server_logic

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

HOST = '127.0.0.1'
PORT = '7777'
s.listen(5)
print  ("Server is listening on port {PORT}")

conn, addr = s.accept()

print ("Connected by {addr}")

while True :
    data = conn.recv(4096)
    if not data: break
    else :
        filename = data.decode()
        print(f"receied filename {filename} from client {addr}")
        if file_path := server_logic.find_filename(filename):
            
