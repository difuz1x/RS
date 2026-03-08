import sys
import os
import grpc
from concurrent import futures
import socket
import subprocess
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../PROTO/generated')))
import clientManager_pb2_grpc
import mrbiznes_pb2_grpc

from PingPongLogic import PingPongLogic
from CurrencyLogic import CurrencyConverterServicer
from auth_interceptor import AuthInterceptor

def get_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()

insecure_port = f"{get_ip()}:50000"

def serve():
        
    auth_path = os.path.join(os.path.dirname(__file__), '../AUTH/auth_server.py')
    auth_proc = subprocess.Popen([sys.executable, auth_path])
    print(f"Auth server started with PID {auth_proc.pid}")
    time.sleep(1)

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[AuthInterceptor()]
    )
    clientManager_pb2_grpc.add_PingPongServicer_to_server(PingPongLogic(), server)
    mrbiznes_pb2_grpc.add_CurrencyConverterServicer_to_server(CurrencyConverterServicer(), server)
    server.add_insecure_port(insecure_port)
    server.start()
    print(f"gRPC server started on {insecure_port}")
    try:
        server.wait_for_termination()
    finally:
        auth_proc.terminate()
        
       


if __name__ == "__main__":
    serve()