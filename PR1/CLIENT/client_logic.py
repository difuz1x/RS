import socket
import ipaddress
import os

CHUNK_SIZE = 4096

def ip_validate(server_ip: str):
    server_ip = server_ip.strip()
    if not server_ip:
        return None
    try:
        return str(ipaddress.ip_address(server_ip))
    except ValueError:
        return None

def port_validate(server_port):
    try:
        server_port = int(server_port)
    except (ValueError, TypeError):
        return None
    if 1024 <= server_port <= 65535:
        return server_port
    return None

def connect_server(server_ip, server_port):
    validated_ip = ip_validate(server_ip)
    validated_port = port_validate(server_port)
    if not (validated_ip and validated_port):
        return None

    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.settimeout(5)  # таймаут підключення
    try:
        connection.connect((validated_ip, validated_port))
        return connection
    except socket.error as err:
        print(f"Cannot connect: {err}")
        return None

def recv_header(user: socket.socket):
    recv_buffer = b""
    while b"\n" not in recv_buffer:
        chunk = user.recv(16)
        if not chunk:
            break
        recv_buffer += chunk
    return recv_buffer.decode("utf-8").strip()

def request_file(user: socket.socket, filename, save_path):
    user.sendall((filename + "\n").encode())

    header = recv_header(user)
    parts = header.split("|")
    if len(parts) != 4:
        raise ValueError("Invalid header format")
    
    status, name, size, chunk = parts
    if status == "ERR":
        raise FileNotFoundError("File not found on server")

    size = int(size)
    os.makedirs(save_path, exist_ok=True)
    file_path = os.path.join(save_path, name)

    received = 0
    with open(file_path, "wb") as f:
        while received < size:
            data = user.recv(CHUNK_SIZE)
            if not data:
                break
            f.write(data)
            received += len(data)

    return file_path
