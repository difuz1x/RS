import sys 
import os 
import grpc 
from concurrent import futures 
import socket


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../PROTO/generated')))
import clientManager_pb2_grpc
import mrbiznes_pb2_grpc


from PingPongLogic import PingPongLogic
from CurrencyLogic import CurrencyConverterServicer




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
    server=grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    clientManager_pb2_grpc.add_PingPongServicer_to_server(PingPongLogic(),server)
    mrbiznes_pb2_grpc.add_CurrencyConverterServicer_to_server(CurrencyConverterServicer(),server)

    server.add_insecure_port(insecure_port)
    server.start()
    print(f"gRPC server started on {insecure_port}")
    server.wait_for_termination()   

if __name__ == "__main__":
    serve()

