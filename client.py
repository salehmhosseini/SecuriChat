import socket
import threading
from datetime import datetime
from db import save_message, get_chat_history

username = input("Enter your name: ")
partner = input("Who do you want to chat with? ")

# نمایش تاریخچه چت قبلی
print(f"\n--- Chat history with {partner} ---")
for sender, msg, time in get_chat_history(username, partner):
    print(f"[{time}] {sender}: {msg}")
print("-----------------------------------\n")

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode()
            if message:
                print("\n" + message)
                # ذخیره پیام دریافتی
                if ": " in message:
                    sender, content = message.split(": ", 1)
                    save_message(sender.strip("[] "), username, content.strip())
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
            save_message(username, partner, message)
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
