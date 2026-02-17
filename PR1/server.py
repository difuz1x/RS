import socket
import os
import threading
import server_logic


def start_server(HOST = '127.0.0.1', PORT = int('7777'), max_client_amount = 1):

 s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

 s.bind ((HOST, PORT))
 if (max_client_amount <1 or max_client_amount > 10):

    print("max_client_amount should be between 1 and 10")
    return 
 
 else:
  
  while True:

    s.listen(max_client_amount)
    print  ("Server is listening on port {PORT}")

    user, addr = s.accept()
    print ("Connected by {addr}")
    user.send('Connection succesful')

    try:
        server_logic.send_file(user,addr)
                
    except Exception as err:
     print('Error with client {addr} : {err}')  

    finally : 
     user.close()