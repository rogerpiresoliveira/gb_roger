import time
from socket import *
import sctp
from threading import Thread

host = "127.0.1.1"
port = 9002

protocol = ""
while protocol != "exit":
    protocol = input("Which protocol? ")
    if protocol == "SCTP" or protocol == "TCP":
        match protocol:
            case "SCTP":
                server_socket = sctp.sctpsocket_tcp(AF_INET)
                server_socket.bind((host, port))
                server_socket.listen(1)

                client_socket = sctp.sctpsocket_tcp(AF_INET)
                client_socket.connect(("127.0.1.1", port))
            case "TCP":
                server_socket = socket(AF_INET, SOCK_STREAM)
                server_socket.bind((host, port))
                server_socket.listen(1)

                client_socket = socket(AF_INET, SOCK_STREAM)
                client_socket.connect(("127.0.1.1", port))


        def client():
            for number in range(10000):
                client_socket.send(str(number).encode())
            client_socket.send("FIM".encode())
            client_socket.shutdown(0)
            client_socket.close()


        def server():
            connection, client_address = server_socket.accept()
            while True:
                data = connection.recv(4)
                if not data:
                    connection.close()
                    break


        thread_client = Thread(target=client)
        thread_server = Thread(target=server)
        thread_client.start()
        thread_server.start()
        thread_client.join()
        thread_server.join()

    if protocol == "UDP":
        server_socket = socket(AF_INET, SOCK_DGRAM)
        server_socket.bind((host, port))
        client_socket = socket(AF_INET, SOCK_DGRAM)


        def client():
            for number in range(10000):
                client_socket.sendto(str(number).encode(), (host, port))
            client_socket.sendto("FIM".encode(), (host, port))

        def server():
            while True:
                message, address = server_socket.recvfrom(4)
                if message.decode() == "FIM":
                    break


        thread_server = Thread(target=server)
        thread_client = Thread(target=client)
        thread_server.start()
        time.sleep(1)
        thread_client.start()
        thread_server.join()
        thread_client.join()
