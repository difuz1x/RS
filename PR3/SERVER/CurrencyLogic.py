import sys 
import os 
import grpc 
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../PROTO/generated')))


import mrbiznes_pb2
import mrbiznes_pb2_grpc

NBU_API='https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json'


class CurrencyConverterServicer(mrbiznes_pb2_grpc.CurrencyConverterServicer):
   
    def getExchangeRate(self,request,context):
       
        print(f"Checking National Bank of Ukraine API")
        try: 
            response=requests.get(NBU_API)
            response.raise_for_status()

            nbu_data=response.json()

            trade_list=mrbiznes_pb2.TradeList()

            for item in nbu_data:

                trade_item = trade_list.trade.add()

                trade_item.fromCurrency = item['cc']
                trade_item.toCurrency = "UAH"
                trade_item.trade_rate= item['rate']
            return trade_list
        except requests.exceptions.RequestException as e:

            print(f"Network failure while connecting to NBU")
            context.abort(grpc.StatusCode.INTERNAL, "Cant get data from bank")
    
    