# logic.py — логіка обробки даних (без мережевого старту)

import json
import random
import socket
from datetime import datetime

# ── Константи ──────────────────────────────────────────────────────────────
RACES              = ['UA123', 'DE321', 'USA666', 'PL333', 'FR945']
STATUSES           = ['BOARDING', 'COMPLETED', 'ONTIME', 'DELAYED', 'CANCELLED']
SERVER_PORT        = 9999
DISCOVERY_PORT     = 9998   # ← окремий порт для анонсів "я тут"
BROADCAST_INTERVAL = 1      # секунд між розсилками статусів

# ── Міні-протокол (JSON) ────────────────────────────────────────────────────
# command: CLIENT_REGISTER   → клієнт реєструється          (клієнт → сервер)
# command: CLIENT_DISCONNECT → клієнт від'єднується         (клієнт → сервер)
# command: FLIGHT_UPDATE     → оновлення статусів            (сервер → клієнт)
# command: SERVER_ANNOUNCE   → "я тут, ось мій IP і порт"   (сервер → broadcast)

def build_flight_update(flights: dict) -> bytes:
    msg = {
        "command":   "FLIGHT_UPDATE",
        "flights":   flights,
        "timestamp": datetime.now().isoformat(timespec='seconds')
    }
    return json.dumps(msg, ensure_ascii=False).encode('utf-8')


def build_announce(server_ip: str, server_port: int) -> bytes:
    """Broadcast-повідомлення щоб клієнти знайшли сервер автоматично."""
    msg = {
        "command": "SERVER_ANNOUNCE",
        "ip":      server_ip,
        "port":    server_port
    }
    return json.dumps(msg).encode('utf-8')


def build_command(command: str) -> bytes:
    return json.dumps({"command": command}).encode('utf-8')


def parse_message(data: bytes) -> dict | None:
    try:
        return json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


# ── Робота з рейсами ────────────────────────────────────────────────────────

def flights_gen(races: list, statuses: list) -> dict:
    return {race: random.choice(statuses) for race in races}


def update_flights(flights: dict, statuses: list) -> dict:
    updated = flights.copy()
    for race in updated:
        if random.random() < 0.3:
            updated[race] = random.choice(statuses)
    return updated


# ── Мережеві утиліти ────────────────────────────────────────────────────────

def get_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()


# ── Потік прийому реєстрацій від клієнтів ──────────────────────────────────

def listen_clients(sock: socket.socket, registered_clients: set, stop_event):
    sock.settimeout(1.0)
    while not stop_event.is_set():
        try:
            data, addr = sock.recvfrom(1024)
            msg = parse_message(data)
            if msg is None:
                print(f'[WARN] Некоректне повідомлення від {addr}')
                continue

            command = msg.get('command')
            if command == 'CLIENT_REGISTER':
                registered_clients.add(addr)
                print(f'[+] Клієнт зареєстровано: {addr}')
            elif command == 'CLIENT_DISCONNECT':
                registered_clients.discard(addr)
                print(f'[-] Клієнт від\'єднався: {addr}')
            else:
                print(f'[WARN] Невідома команда "{command}" від {addr}')

        except socket.timeout:
            continue
        except OSError:
            print('[INFO] Сокет закрито, слухач завершується.')
            break


# ── Потік broadcast-анонсу адреси сервера ──────────────────────────────────

def announce_server(server_ip: str, server_port: int, stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    payload = build_announce(server_ip, server_port)

    # Список адрес куди надсилаємо анонс
    targets = [
        ('255.255.255.255', DISCOVERY_PORT),  # broadcast → інші ПК в мережі
        ('127.0.0.1',       DISCOVERY_PORT),  # loopback  → сам собі
    ]

    print(f'[ANNOUNCE] Розсилаю адресу сервера на порт {DISCOVERY_PORT}...')
    while not stop_event.is_set():
        for target in targets:
            try:
                sock.sendto(payload, target)
            except OSError as e:
                print(f'[WARN] Announce → {target}: {e}')
        stop_event.wait(2)

    sock.close()
