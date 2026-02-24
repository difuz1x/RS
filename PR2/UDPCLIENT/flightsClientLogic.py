import socket
import ipaddress




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

    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        connection.connect((validated_ip, validated_port))
        return connection
    except socket.error as err:
        print(f"Cannot connect: {err}")
        return None

dict={}