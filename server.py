import socket
import threading
from datetime import datetime
import mysql.connector

clients = {}  # username -> socket

def update_last_seen(username):
    conn = mysql.connector.connect(
        host="localhost",
        user="xatovate",
        password="123123",
        database="securichat"
    )
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = """
        INSERT INTO user_status (username, last_seen)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE last_seen = VALUES(last_seen)
    """
    cursor.execute(query, (username, now))
    conn.commit()
    conn.close()

def get_last_seen(username):
    conn = mysql.connector.connect(
        host="localhost",
        user="xatovate",
        password="123123",
        database="securichat"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT last_seen FROM user_status WHERE username = %s", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "never"

def handle_client(client_socket):
    try:
        username = client_socket.recv(1024).decode()
        if not username:
            return

        clients[username] = client_socket
        update_last_seen(username)
        print(f"[+] {username} is now online.")

        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break

            if data == "GET_USERS":
                online_users = set(clients.keys())
                all_users = set(get_all_known_users())
                
                response = "=== Online Users ===\n"
                for name in sorted(online_users):
                    response += f"{name}\n"
                
                response += "\n=== Offline Users ===\n"
                for name in sorted(all_users - online_users):
                    last_seen = get_last_seen(name)
                    response += f"{name} (Last seen: {last_seen})\n"
                
                client_socket.send(response.encode())

            elif data.startswith("CHECK_USER:"):
                target = data.split(":")[1]
                if target in clients:
                    client_socket.send(b"ONLINE")
                else:
                    last_seen = get_last_seen(target)
                    client_socket.send(f"OFFLINE:{last_seen}".encode())

            elif data.startswith("TO:"):
                parts = data.split(":", 2)
                if len(parts) == 3:
                    _, to_user, message = parts
                    if to_user in clients:
                        try:
                            clients[to_user].send(message.encode())
                        except:
                            print(f"[!] Failed to send message to {to_user}")

    except Exception as e:
        print(f"[!] Error with client: {e}")
    finally:
        disconnected_user = None
        for name, sock in list(clients.items()):
            if sock == client_socket:
                disconnected_user = name
                break
        
        if disconnected_user:
            update_last_seen(disconnected_user)
            del clients[disconnected_user]
            print(f"[-] {disconnected_user} went offline.")
        client_socket.close()

def get_all_known_users():
    conn = mysql.connector.connect(
        host="localhost",
        user="xatovate",
        password="123123",
        database="securichat"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM user_status")
    result = cursor.fetchall()
    conn.close()
    return [row[0] for row in result] if result else []

def start_server(host='127.0.0.1', port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()
    print(f"[SERVER] Listening on {host}:{port}")

    while True:
        client_socket, _ = server.accept()
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()

if __name__ == "__main__":
    start_server()