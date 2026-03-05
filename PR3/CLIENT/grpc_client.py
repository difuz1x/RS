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
        self.currency_stub  = mrbiznes_pb2_grpc.CurrencyConverterStub(self.channel)
        self.client_id      = None

    def _metadata(self):
        return [('client_id', str(self.client_id))] if self.client_id else []

    def connect(self, client_id):
        request = clientManager_pb2.ClientStatus(clientID=client_id, isRegistered=False)
        response = self.ping_pong_stub.connectClient(request)
        self.client_id = response.clientID
        return response

    def disconnect(self, client_id):
        request = clientManager_pb2.ClientStatus(clientID=client_id, isRegistered=True)
        return self.ping_pong_stub.disonnectClient(request, metadata=self._metadata())

    def get_rates(self):
        request = mrbiznes_pb2.Empty()
        response = self.currency_stub.getExchangeRate(request, metadata=self._metadata())
        return response.trade

    def convert_amount(self, from_currency, to_currency, amount):
        request = mrbiznes_pb2.ConvertRequest(
            fromCurrency = from_currency,
            toCurrency   = to_currency,
            amount       = amount
        )
        return self.currency_stub.convertAmount(request, metadata=self._metadata())

    def get_rates_for_base(self, base_currency):
        request = mrbiznes_pb2.BaseRequest(baseCurrency=base_currency)
        return self.currency_stub.getRatesForBase(request, metadata=self._metadata()) 