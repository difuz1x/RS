import sys
import os
import grpc
import requests as http

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../PROTO/generated')))

import clientManager_pb2
import clientManager_pb2_grpc
import mrbiznes_pb2
import mrbiznes_pb2_grpc

AUTH_URL = "http://192.168.1.104:8080"

class GRPCClient:

    def __init__(self, server_host='192.168.1.104', server_port='50000'):
        self.channel        = grpc.insecure_channel(f"{server_host}:{server_port}")
        self.ping_pong_stub = clientManager_pb2_grpc.PingPongStub(self.channel)
        self.currency_stub  = mrbiznes_pb2_grpc.CurrencyConverterStub(self.channel)
        self.client_id      = None
        self.access_token   = None
        self.refresh_token  = None
        self.role           = None

    def login(self, username, password):
        try:
            response = http.post(f"{AUTH_URL}/login", json={
                "username": username, "password": password
            }, timeout=5)
        except http.exceptions.ConnectionError:
            return False, "Auth server unavailable"
        if response.status_code == 200:
            data = response.json()
            self.access_token  = data["access_token"]
            self.refresh_token = data["refresh_token"]
            self.role          = data.get("role", "user")
            print(f"Logged in as {username} (role: {self.role})")
            return True, None
        return False, response.json().get("error", "Unknown error")

    def refresh_access_token(self):
        try:
            response = http.post(f"{AUTH_URL}/refresh", headers={
                "Authorization": f"Bearer {self.refresh_token}"
            }, timeout=5)
        except http.exceptions.ConnectionError:
            return False
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            return True
        return False

    def get_users(self):
        try:
            response = http.get(f"{AUTH_URL}/users", headers={
                "Authorization": f"Bearer {self.access_token}"
            }, timeout=5)
            if response.status_code == 200:
                return response.json().get("users", [])
        except http.exceptions.ConnectionError:
            pass
        return []

    def delete_user(self, username):
        response = http.post(f"{AUTH_URL}/delete_user",
            json={"username": username},
            headers={"Authorization": f"Bearer {self.access_token}"}, timeout=5)
        data = response.json()
        return response.status_code == 200, data.get("message") or data.get("error")

    def add_user(self, username, password, role):
        response = http.post(f"{AUTH_URL}/add_user",
            json={"username": username, "password": password, "role": role},
            headers={"Authorization": f"Bearer {self.access_token}"}, timeout=5)
        data = response.json()
        return response.status_code == 200, data.get("message") or data.get("error")

    def change_role(self, username, role):
        response = http.post(f"{AUTH_URL}/change_role",
            json={"username": username, "role": role},
            headers={"Authorization": f"Bearer {self.access_token}"}, timeout=5)
        data = response.json()
        return response.status_code == 200, data.get("message") or data.get("error")

    def _metadata(self):
        meta = []
        if self.client_id is not None:
            meta.append(('client_id', str(self.client_id)))
        if self.access_token:
            meta.append(('authorization', f'Bearer {self.access_token}'))
        return meta

    def connect(self, client_id):
        request = clientManager_pb2.ClientStatus(clientID=client_id, isRegistered=False)
        response = self.ping_pong_stub.connectClient(request)
        self.client_id = response.clientID
        return response

    def disconnect(self, client_id):
        request = clientManager_pb2.ClientStatus(clientID=client_id, isRegistered=True)
        return self.ping_pong_stub.disonnectClient(request, metadata=self._metadata())

    def get_rates(self):
        request  = mrbiznes_pb2.Empty()
        response = self.currency_stub.getExchangeRate(request, metadata=self._metadata())
        return response.trade

    def convert_amount(self, from_currency, to_currency, amount):
        request = mrbiznes_pb2.ConvertRequest(
            fromCurrency=from_currency,
            toCurrency=to_currency,
            amount=amount
        )
        return self.currency_stub.convertAmount(request, metadata=self._metadata())

    def get_rates_for_base(self, base_currency):
        request = mrbiznes_pb2.BaseRequest(baseCurrency=base_currency)
        return self.currency_stub.getRatesForBase(request, metadata=self._metadata())