# flightsClientLogic.py

import socket
import ipaddress
import json
from datetime import datetime

SERVER_PORT_DEFAULT = 9999
DISCOVERY_PORT      = 9998   # той самий порт що сервер анонсує
BUFFER_SIZE         = 4096

# ── Протокол ────────────────────────────────────────────────────────────────

def build_command(command: str) -> bytes:
    return json.dumps({"command": command}).encode('utf-8')

def parse_message(data: bytes) -> dict | None:
    try:
        return json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

# ── Валідація ────────────────────────────────────────────────────────────────

def ip_validate(server_ip: str) -> str | None:
    server_ip = server_ip.strip()
    if not server_ip:
        return None
    try:
        return str(ipaddress.ip_address(server_ip))
    except ValueError:
        return None

def port_validate(server_port) -> int | None:
    try:
        server_port = int(server_port)
    except (ValueError, TypeError):
        return None
    if 1024 <= server_port <= 65535:
        return server_port
    return None

# ── Автовідкриття сервера ────────────────────────────────────────────────────

def discover_server(timeout: float = 5.0) -> tuple[str, int] | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # ← додай це
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # ← і це
    except AttributeError:
        pass  # Windows не підтримує SO_REUSEPORT — ігноруємо
    sock.settimeout(timeout)

    try:
        sock.bind(('', DISCOVERY_PORT))
        data, _ = sock.recvfrom(1024)
        msg = parse_message(data)
        if msg and msg.get('command') == 'SERVER_ANNOUNCE':
            return msg['ip'], msg['port']
    except socket.timeout:
        return None
    except OSError:
        return None
    finally:
        sock.close()


# ── Мережеві операції ────────────────────────────────────────────────────────

def create_udp_socket(timeout: float = 1.0) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    return sock

def register_client(sock, server_addr) -> bool:
    try:
        sock.sendto(build_command('CLIENT_REGISTER'), server_addr)
        return True
    except OSError as e:
        print(f'[ERROR] Реєстрація не вдалась: {e}')
        return False

def unregister_client(sock, server_addr):
    try:
        sock.sendto(build_command('CLIENT_DISCONNECT'), server_addr)
    except OSError:
        pass

def receive_update(sock) -> dict | None:
    data, _ = sock.recvfrom(BUFFER_SIZE)
    return parse_message(data)

def format_timestamp(iso_str: str) -> str:
    try:
        return datetime.fromisoformat(iso_str).strftime('%H:%M:%S')
    except ValueError:
        return iso_str