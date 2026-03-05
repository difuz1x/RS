import sys 
import os 
import grpc 
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../PROTO/generated')))

import mrbiznes_pb2
import mrbiznes_pb2_grpc

NBU_API = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json'


class CurrencyConverterServicer(mrbiznes_pb2_grpc.CurrencyConverterServicer):

    def _fetch_rates(self):
        
        response = requests.get(NBU_API)
        response.raise_for_status()
        rates = {"UAH": 1.0}
        for item in response.json():
            rates[item['cc']] = item['rate']
        return rates

    def getExchangeRate(self, request, context):
        print("Checking National Bank of Ukraine API")
        try:
            rates = self._fetch_rates()
            trade_list = mrbiznes_pb2.TradeList()
            for cc, rate in rates.items():
                if cc == "UAH":
                    continue
                trade_item = trade_list.trade.add()
                trade_item.fromCurrency = cc
                trade_item.toCurrency   = "UAH"
                trade_item.trade_rate   = rate
            print(f"Received {len(trade_list.trade)} exchange rates from NBU")
            return trade_list
        except requests.exceptions.RequestException:
            print("Network failure while connecting to NBU")
            context.abort(grpc.StatusCode.INTERNAL, "Cant get data from bank")

    def convertAmount(self, request, context):
        meta = dict(context.invocation_metadata())
        client_id = meta.get('client_id', 'unknown')
        print(f"Converting {request.amount} {request.fromCurrency} -> {request.toCurrency} for client {client_id}")
        try:
            rates = self._fetch_rates()
        except requests.exceptions.RequestException:
            context.abort(grpc.StatusCode.INTERNAL, "Cant get data from bank")
            return
        if request.fromCurrency not in rates:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Currency '{request.fromCurrency}' not found")
            return

        if request.toCurrency not in rates:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Currency '{request.toCurrency}' not found")
            return

        result = request.amount * rates[request.fromCurrency] / rates[request.toCurrency]
        return mrbiznes_pb2.ConvertResponse(
            result       = result,
            fromCurrency = request.fromCurrency,
            toCurrency   = request.toCurrency
        )

    def getRatesForBase(self, request, context):
        print(f"Streaming rates for base currency: {request.baseCurrency}")
        try:
            rates = self._fetch_rates()
        except requests.exceptions.RequestException:
            context.abort(grpc.StatusCode.INTERNAL, "Cant get data from bank")

        if request.baseCurrency not in rates:
            context.abort(grpc.StatusCode.NOT_FOUND,
                          f"Base currency '{request.baseCurrency}' not found")

        base_rate = rates[request.baseCurrency]
        for cc, rate in rates.items():
            yield mrbiznes_pb2.ConvertStruct(
                fromCurrency = cc,
                toCurrency   = request.baseCurrency,
                trade_rate   = rate / base_rate
            )