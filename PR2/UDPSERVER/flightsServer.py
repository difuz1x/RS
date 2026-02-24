import socket
import random
import json
import threading

RACES = [ 'UA123','DE321','USA666','PL333','FR945']


STATUSES = ['BOARDING','COMPLETED','ONTIME']

def flightsGen(races:list, statuses:list)->dict:
    flights={}
    for race in races:
        flights[race]=random.choice(statuses)
    return flights




def get_ip():
    s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8',1))
        ip=s.getsockname()[0]
    except Exception:
        ip='127.0.0.1'
    finally:
        s.close()
    return ip

def listen_clients(sock:socket.socket,registered_clients:set):
    while True:
        try:
            data,user=sock.recvfrom(1024)
            msg=json.loads(data.decode('utf-8'))

            command=msg.get('command')
            if command=="CLIENT_REGISTER":
                registered_clients.add(user)
                print(f'Registered client {user}')
            elif command=="CLIENT_DISCONNECT":
                registered_clients.discard(user)
                print(f'Disconnected client {user}')
        except json.decoder.JSONDecodeError:
            pass
        except OSError:
            print(f'Program exited')
            break

def server_start():
    registered_clients=set()
    SERVER_IP=get_ip()
    SERVER_PORT=9999
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind((SERVER_IP,SERVER_PORT))
    print(f'Server started with IP address {SERVER_IP}:{SERVER_PORT} ')

    listener_thread=threading.Thread(target=listen_clients,
                                 args=(sock,registered_clients),
                                 daemon=True)
    listener_thread.start()





