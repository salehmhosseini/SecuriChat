import socket
import threading

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode()
            if message:
                print("\n" + message)
        except:
            print("[!] Connection lost.")
            sock.close()
            break

def send_messages(sock):
    while True:
        message = input()
        try:
            sock.send(message.encode())
        except:
            print("[!] Failed to send.")
            break

def start_client(server_ip='127.0.0.1', port=12345):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, port))
    print("[*] Connected to the server.")

    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
    send_messages(client_socket)

if __name__ == "__main__":
    start_client()
