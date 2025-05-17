import socket
import threading
from datetime import datetime

username = input("Enter your name: ")

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode()
            if message:
                print("\n" + message)
                save_message(message)
        except:
            print("[!] Connection lost.")
            sock.close()
            break

def send_messages(sock):
    while True:
        message = input()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {username}: {message}"
        try:
            sock.send(formatted.encode())
        except:
            print("[!] Failed to send.")
            break

def save_message(message):
    with open("chat_history.txt", "a") as f:
        f.write(message + "\n")

def start_client(server_ip='127.0.0.1', port=12345):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, port))
    print("[*] Connected to the server.")

    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
    send_messages(client_socket)

if __name__ == "__main__":
    start_client()
