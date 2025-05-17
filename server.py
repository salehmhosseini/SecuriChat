import socket
import threading

clients = []

def handle_client(client_socket, address):
    print(f"[+] Connection from {address}")
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if not message:
                break
            print(f"[{address}] {message}")
            broadcast(message, client_socket)
        except:
            break

    print(f"[-] Disconnected: {address}")
    clients.remove(client_socket)
    client_socket.close()

def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message.encode())
            except:
                pass

def start_server(host='127.0.0.1', port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"[SERVER] Listening on {host}:{port}")

    while True:
        client_socket, addr = server.accept()
        clients.append(client_socket)
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()

if __name__ == "__main__":
    start_server()
