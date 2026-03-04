# flightsServer.py — запуск сервера та цикл широкомовної розсилки

import socket
import threading
import time

from flightsServerLogic import (
    RACES, STATUSES, SERVER_PORT,
    BROADCAST_INTERVAL,
    flights_gen, update_flights,
    build_flight_update,
    get_ip, listen_clients, announce_server,
)


def broadcast_flights(sock, registered_clients, stop_event):
    flights = flights_gen(RACES, STATUSES)
    print('[INFO] Початковий стан рейсів:', flights)

    while not stop_event.is_set():
        flights = update_flights(flights, STATUSES)
        payload = build_flight_update(flights)

        print('\n[BROADCAST]', {r: s for r, s in flights.items()})

        dead = set()
        for client_addr in list(registered_clients):
            try:
                sock.sendto(payload, client_addr)
            except OSError as e:
                print(f'[WARN] Не вдалося надіслати до {client_addr}: {e}')
                dead.add(client_addr)

        registered_clients -= dead
        time.sleep(BROADCAST_INTERVAL)


def server_start():
    server_ip = get_ip()
    registered_clients = set()
    stop_event = threading.Event()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((server_ip, SERVER_PORT))
    print(f'[SERVER] Запущено на {server_ip}:{SERVER_PORT}')

    # Потік 1: слухає реєстрації від клієнтів
    listener = threading.Thread(
        target=listen_clients,
        args=(sock, registered_clients, stop_event),
        daemon=True
    )

    # Потік 2: розсилає статуси рейсів зареєстрованим клієнтам
    broadcaster = threading.Thread(
        target=broadcast_flights,
        args=(sock, registered_clients, stop_event),
        daemon=True
    )

    # Потік 3: broadcast-анонс "я тут" для автовідкриття ← НОВИЙ
    announcer = threading.Thread(
        target=announce_server,
        args=(server_ip, SERVER_PORT, stop_event),
        daemon=True
    )

    listener.start()
    broadcaster.start()
    announcer.start()

    print('[SERVER] Натисніть Ctrl+C для зупинки.')
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print('\n[SERVER] Зупинка...')
        stop_event.set()
        sock.close()
        listener.join(timeout=2)
        broadcaster.join(timeout=2)
        announcer.join(timeout=2)
        print('[SERVER] Завершено.')


if __name__ == '__main__':
    server_start()