import socket
import threading
import time
from datetime import datetime
from db import save_message, get_chat_history

def receive_messages(sock, username):
    while True:
        try:
            message = sock.recv(1024).decode()
            if message:
                print("\n" + message)
                if ": " in message:
                    parts = message.split(": ", 1)
                    if len(parts) == 2:
                        sender, content = parts
                        save_message(sender.strip("[] "), username, content.strip())
        except Exception as e:
            print(f"[!] Connection error: {str(e)}")
            sock.close()
            break

def send_messages(sock, username, partner):
    while True:
        try:
            message = input()
            if message.lower() == 'exit':
                print("[*] Closing chat...")
                sock.close()
                return
                
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted = f"[{timestamp}] {username}: {message}"
            sock.send(f"TO:{partner}:{formatted}".encode())
            save_message(username, partner, message)
        except Exception as e:
            print(f"[!] Failed to send message: {str(e)}")
            break

def start_client(server_ip='127.0.0.1', port=12345):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(20)  # Set timeout for socket operations
    
    try:
        print("[*] Connecting to server...")
        client_socket.connect((server_ip, port))
        print("[*] Connected to server")
    except Exception as e:
        print(f"[!] Failed to connect to server: {str(e)}")
        return

    # Step 1: Enter and send username
    username = input("Enter your username: ").strip()
    if not username:
        print("[!] Username cannot be empty")
        client_socket.close()
        return

    try:
        client_socket.send(username.encode())
        print("[*] Username sent to server")
        time.sleep(0.5)  # Small delay to ensure server processes username
    except Exception as e:
        print(f"[!] Failed to send username: {str(e)}")
        client_socket.close()
        return

    # Main interaction loop
    while True:
        try:
            # Request user list
            print("[*] Requesting user list...")
            client_socket.send("GET_USERS".encode())
            
            # Wait for user list response
            users = client_socket.recv(4096).decode()
            if not users:
                print("[!] Empty response from server")
                continue
                
            print("\n=== Available Users ===")
            print(users)
            print("======================")
            
            # Select chat partner
            partner = input("\nWho do you want to chat with? (or type 'exit' to quit) ").strip()
            
            if partner.lower() == 'exit':
                client_socket.close()
                return

            # Check if partner exists and is online
            print(f"[*] Checking status of {partner}...")
            client_socket.send(f"CHECK_USER:{partner}".encode())
            response = client_socket.recv(1024).decode()

            if response == "ONLINE":
                print(f"[*] {partner} is online. Starting chat...")
                break
            else:
                parts = response.split(":", 1)
                if len(parts) > 1:
                    print(f"\n[!] User '{partner}' is offline. Last seen: {parts[1]}")
                else:
                    print(f"\n[!] User '{partner}' doesn't exist")
                print("Please select an online user from the list above.\n")

        except socket.timeout:
            print("[!] Server response timeout. Please try again.")
        except Exception as e:
            print(f"[!] Error during operation: {str(e)}")
            client_socket.close()
            return

    # Display chat history
    print(f"\n--- Chat history with {partner} ---")
    try:
        history = get_chat_history(username, partner)
        for sender, msg, time_ in history:
            print(f"[{time_}] {sender}: {msg}")
    except Exception as e:
        print(f"[!] Couldn't load chat history: {str(e)}")
    print("------------------------------")
    print("Type your messages below (type 'exit' to end chat):\n")

    # Start chat session
    try:
        threading.Thread(target=receive_messages, args=(client_socket, username), daemon=True).start()
        send_messages(client_socket, username, partner)
    except Exception as e:
        print(f"[!] Chat session error: {str(e)}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    start_client()