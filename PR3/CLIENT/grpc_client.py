import sys
import os
import grpc

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../PROTO/generated')))

import clientManager_pb2
import clientManager_pb2_grpc
import mrbiznes_pb2
import mrbiznes_pb2_grpc

class GRPCClient:

    def __init__(self, server_host='192.168.1.104', server_port='50000'):
        self.channel = grpc.insecure_channel(f"{server_host}:{server_port}")
        self.ping_pong_stub = clientManager_pb2_grpc.PingPongStub(self.channel)
        self.currency_stub = mrbiznes_pb2_grpc.CurrencyConverterStub(self.channel)

    def connect(self, client_id):
        request = clientManager_pb2.ClientStatus(clientID=client_id, isRegistered=False)
        return self.ping_pong_stub.connectClient(request)

    def disconnect(self, client_id):
        request = clientManager_pb2.ClientStatus(clientID=client_id, isRegistered=True)
        return self.ping_pong_stub.disonnectClient(request)

    def get_rates(self):
        request = mrbiznes_pb2.Empty()
        response = self.currency_stub.getExchangeRate(request)
        return response.trade