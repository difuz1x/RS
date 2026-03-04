import sys 
import os 
import grpc 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../PROTO/generated')))

import clientManager_pb2
import clientManager_pb2_grpc 

class PingPongLogic(clientManager_pb2_grpc.PingPongServicer):
    def __init__(self):
        self.current_clients=set()


    def connectClient(self, request, context):

        if request.clientID in self.current_clients:
            return clientManager_pb2.ClientStatus(clientID=request.clientID, isRegistered=False)

        self.current_clients.add(request.clientID)
        print(f"Client with ID {request.clientID} connecting")
        
        return clientManager_pb2.ClientStatus(clientID=request.clientID, isRegistered=True)


    def disonnectClient(self, request, context):
        print(f"Client with ID {request.clientID} disconnecting")
        self.current_clients.discard(request.clientID)
        return clientManager_pb2.ClientStatus(clientID=request.clientID, isRegistered=False)
    
