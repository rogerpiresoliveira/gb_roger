import sys
from socket import *
from threading import Thread
import sctp
import ipaddress
import time
import os

ip = "127.0.1.1"
base_port = 4200

default_sctp_port = base_port
default_tcp_port = base_port + 1
default_udp_port = base_port + 2

sender_sockets = {}
receiver_sockets = {}
server_connections = []
client_connections = []


def create_sctp():
    sender_socket = sctp.sctpsocket_tcp(AF_INET)
    sender_sockets["SCTP"] = sender_socket
    receiver_socket = sctp.sctpsocket_tcp(AF_INET)
    receiver_sockets["SCTP"] = receiver_socket
    receiver_socket.bind((ip, base_port))


def create_tcp():
    sender_socket = socket(AF_INET, SOCK_STREAM)
    sender_sockets["TCP"] = sender_socket
    receiver_socket = socket(AF_INET, SOCK_STREAM)
    receiver_sockets["TCP"] = receiver_socket
    receiver_socket.bind((ip, base_port + 1))


def create_udp():
    sender_socket = socket(AF_INET, SOCK_DGRAM)
    sender_sockets["UDP"] = sender_socket
    receiver_socket = socket(AF_INET, SOCK_DGRAM)
    receiver_sockets["UDP"] = receiver_socket
    receiver_socket.bind((ip, base_port + 2))


def wait_sctp_connection():
    while True:
        receiver_sockets.get("SCTP").listen(1)
        connection, client_address = receiver_sockets.get("SCTP").accept()
        server_connections.append(("SCTP", connection, client_address))
        thread_sctp = Thread(target=exec_server_option, args=[connection, client_address, "SCTP"])
        thread_sctp.start()


def wait_tcp_connection():
    while True:
        receiver_sockets.get("TCP").listen(1)
        connection, client_address = receiver_sockets.get("TCP").accept()
        server_connections.append(("TCP", connection, client_address))
        thread_tcp = Thread(target=exec_server_option, args=[connection, client_address, "TCP"])
        thread_tcp.start()


def listen_udp():
    while True:
        chosen_option, sender_address = receiver_sockets.get("UDP").recvfrom(53)
        match chosen_option.decode("UTF-8"):
            case "1":
                command, sender_address = receiver_sockets.get("UDP").recvfrom(500)
                print(command)
                print("\nExecuting command from %s: %s\n" % (sender_address, command), end='')
                os.system(command)


create_sctp()
create_tcp()
create_udp()
thread_sctp_listen = Thread(target=wait_sctp_connection)
thread_tcp_listen = Thread(target=wait_tcp_connection)
thread_udp_listen = Thread(target=listen_udp)
thread_sctp_listen.start()
thread_tcp_listen.start()
thread_udp_listen.start()


def exec_client_option(number, protocol, sender_socket, server_address):
    match number:
        case "1":
            command = input("Type command: ")
            message_size = str(sys.getsizeof(command))
            match protocol:
                case "SCTP":
                    sender_socket.sctp_send(str(message_size))
                    sender_socket.sctp_send(str(command))
                case "TCP":
                    sender_socket.send(str(message_size).encode())
                    time.sleep(0.1)
                    sender_socket.send(str(command).encode())
                case "UDP":
                    sender_socket.sendto(str(command).encode(), server_address)
        case "2":
            try:
                guest_filename = input("Type requested filename: ")
                host_filename = input("Type a name for the file: ")
                match protocol:
                    case "SCTP":
                        sender_socket.sctp_send(str(guest_filename))
                        with open(host_filename, "wb") as file:
                            while 1:
                                data = sender_socket.recv(5000)
                                if data.decode() == "FIM":
                                    break
                                file.write(data)
                    case "TCP":
                        sender_socket.send(guest_filename.encode())
                        with open(host_filename, "wb") as file:
                            while 1:
                                data = sender_socket.recv(5000)
                                if data.decode() == "FIM":
                                    break
                                file.write(data)
            except ValueError:
                print("Check filename and try again.")


def exec_server_option(connection, client_address, protocol):
    while True:
        chosen_option = connection.recv(53).decode("UTF-8")
        match chosen_option:
            case "1":
                match protocol:
                    case "SCTP":
                        next_line_size = int(connection.recv(53))
                        command = connection.recv(next_line_size).decode("UTF-8")
                        print("\nExecuting command from %s: %s\n" % (client_address, command), end='')
                        os.system(command)
                    case "TCP":
                        next_line_size = int(connection.recv(53).decode("UTF-8"))
                        command = connection.recv(next_line_size).decode("UTF-8")
                        print("\nExecuting command from %s: %s\n" % (client_address, command), end='')
                        os.system(command)
            case "2":
                try:
                    match protocol:
                        case "SCTP":
                            namefile = connection.recv(1024).decode("UTF-8")
                            with open(namefile, "rb") as file:
                                for data in file.readlines():
                                    connection.send(data)
                                connection.send("FIM".encode())
                        case "TCP":
                            namefile = connection.recv(1024).decode("UTF-8")
                            with open(namefile, "rb") as file:
                                for data in file.readlines():
                                    connection.send(data)
                                time.sleep(0.2)
                                connection.send("FIM".encode())
                except FileNotFoundError:
                    print("%s tried to get a file that doesn't exist.")


def already_connected(protocol, ip_to_check):
    is_connected = False
    for connection in client_connections:
        if connection[0] == protocol and connection[1] == ip_to_check:
            is_connected = True
    return is_connected


def valid_ip(ip_to_check):
    try:
        ipaddress.ip_address(ip_to_check)
        return True
    except ValueError:
        print("Check the IP address and try again.")
        return False


def show_menu():
    print("1) Send a command")
    print("2) Request a file")
    chosen_option = input("Enter option: ")
    while int(chosen_option) not in (1, 2):
        print("Invalid option. Try again.")
        chosen_option = input("Enter option: ")
    return chosen_option


while True:
    client_protocol = input("Which protocol will you use? ")
    while client_protocol not in ("SCTP", "TCP", "UDP"):
        print("Supported protocols are SCTP, TCP and UDP. Check your choice and try again.")
        client_protocol = input("Which protocol will you use? ")

    guest_ip = input("Insert the guest IP: ")
    while not valid_ip(guest_ip):
        guest_ip = input("Insert the guest IP: ")

    try:
        option = show_menu()
        match client_protocol:
            case "SCTP":
                if already_connected("SCTP", guest_ip):
                    sender_sockets.get("SCTP").sctp_send(str(option))
                    exec_client_option(option, client_protocol, sender_sockets.get(client_protocol), ())
                else:
                    sender_sockets.get("SCTP").connect((guest_ip, default_sctp_port + 1000))
                    sender_sockets.get("SCTP").sctp_send(str(option))
                    exec_client_option(option, client_protocol, sender_sockets.get(client_protocol), ())
                    client_connections.append(("SCTP", guest_ip))
            case "TCP":
                if already_connected("TCP", guest_ip):
                    sender_sockets.get("TCP").send(str(option).encode())
                    exec_client_option(option, client_protocol, sender_sockets.get(client_protocol), ())
                else:
                    sender_sockets.get("TCP").connect((guest_ip, default_tcp_port + 1000))
                    sender_sockets.get("TCP").send(str(option).encode())
                    exec_client_option(option, client_protocol, sender_sockets.get(client_protocol), ())
                    client_connections.append(("TCP", guest_ip))
            case "UDP":
                address = (guest_ip, default_udp_port + 1000)
                sender_sockets.get("UDP").sendto(str(option).encode(), address)
                exec_client_option(option, client_protocol, sender_sockets.get(client_protocol), address)
    except OSError:
        print("An error occurred.")
